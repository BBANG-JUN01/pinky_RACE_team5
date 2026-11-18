"""Launch an isolated race and score it from world truth. Run after sourcing ROS."""
import argparse
from collections import Counter
from datetime import datetime,timezone
import json
import math
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time


def options():
    p=argparse.ArgumentParser()
    p.add_argument('--backend',choices=['gazebo','ros_fixture'],default='gazebo')
    p.add_argument('--case',choices=['clean','cone','barrier','rules','watchdog'],default='clean')
    p.add_argument('--seed',type=int,default=0,help='ROS fixture sensor noise seed')
    p.add_argument('--domain',type=int,default=82)
    p.add_argument('--timeout',type=float,default=360,help='wall seconds per trial')
    p.add_argument('--output',type=Path,default=Path('log/gp_trials'))
    p.add_argument('--gui',action='store_true')
    p.add_argument('--bag',action='store_true')
    args=p.parse_args()
    if not 0<=args.domain<=100 or args.timeout<=0: p.error('invalid domain or timeout')
    return args


def stop_process(proc):
    if proc and proc.poll() is None:
        os.killpg(proc.pid,signal.SIGINT)
        try: proc.wait(10)
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid,signal.SIGTERM)
            try: proc.wait(4)
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid,signal.SIGKILL);proc.wait()


def run(args,folder,report):
    import rclpy
    from rclpy.node import Node
    from rclpy.parameter import Parameter
    from rclpy.qos import qos_profile_sensor_data
    from geometry_msgs.msg import Twist
    from nav_msgs.msg import Odometry
    from sensor_msgs.msg import LaserScan
    from std_msgs.msg import String
    from std_srvs.srv import Trigger
    from ros_gz_interfaces.srv import ControlWorld,DeleteEntity,SpawnEntity
    from pinky_gp_interfaces.msg import RaceCommand
    from pinky_gp_navigation.scan_race import RADIUS as radius

    from pinky_gp_navigation import track_fixture as track
    from pinky_gp_core.sensor_time import seconds
    rclpy.init()
    n=Node('trial_judge',parameter_overrides=[Parameter('use_sim_time',value=True)])
    stat={}
    counts=Counter()
    last_state=''
    truth=None
    truth_gate=0
    previous_x=0.
    min_clearance=math.inf
    cmd=(0.,0.)
    commanded_at=None
    guard=''
    active_box=None
    trace=(folder/'events.jsonl').open('w',buffering=1)
    def log(event,**data):
        trace.write(json.dumps(dict(wall_s=round(time.monotonic()-begin,3),event=event,**data))+'\n')
    def status(m):
        nonlocal stat,last_state
        stat=json.loads(m.data)
        if stat['state']!=last_state:
            last_state=stat['state'];log('state',state=last_state,laps=stat['laps'])
        counts['state_'+last_state]+=1
    def command(m):
        nonlocal cmd,commanded_at
        cmd=(m.linear.x,m.angular.z)
        commanded_at=time.monotonic()
        counts['cmd']+=1
    def guard_cb(m):
        nonlocal guard
        guard=m.data
    def truth_cb(m):
        nonlocal truth,previous_x,truth_gate,min_clearance
        x=m.pose.pose.position.x;y=m.pose.pose.position.y
        truth=(x,y,abs(m.twist.twist.linear.x),abs(m.twist.twist.angular.z),seconds(m.header.stamp))
        boxes=track.WALLS+((track.EVENT_BOXES[active_box],) if active_box else ())
        min_clearance=min(min_clearance,track.wall_distance(x,y,boxes)-radius)
        passed=(x>1.02,y>1.18 and abs(x)<.45,x<-1.02,y<.30 and previous_x<-.08<=x)
        if passed[truth_gate%4]:
            truth_gate+=1;log('truth_gate',gate=truth_gate,x=x,y=y)
        previous_x=x
        counts['truth']+=1
    def scan_cb(m):
        if m.header.frame_id=='rplidar_link' and len(m.ranges)>=32:
            counts['scan']+=1
    def odom_cb(m):
        if m.header.frame_id=='odom' and m.child_frame_id=='base_footprint': counts['odom']+=1
    begin=time.monotonic()
    n.create_subscription(String,'/gp/status',status,10)
    n.create_subscription(String,'/gp/guard_state',guard_cb,10)
    n.create_subscription(Twist,'/gp/sim_cmd_vel',command,10)
    n.create_subscription(Odometry,'/gp/truth',truth_cb,qos_profile_sensor_data)
    n.create_subscription(Odometry,'/odom',odom_cb,qos_profile_sensor_data)
    n.create_subscription(LaserScan,'/scan',scan_cb,qos_profile_sensor_data)
    events=n.create_publisher(RaceCommand,'/gp/event',10)
    start=n.create_client(Trigger,'/gp/start')
    add=n.create_client(SpawnEntity,'/world/pinky_gp/create')
    remove=n.create_client(DeleteEntity,'/world/pinky_gp/remove')
    world=n.create_client(ControlWorld,'/world/pinky_gp/control')
    def wait(check,label,limit=30):
        until=min(begin+args.timeout,time.monotonic()+limit)
        while time.monotonic()<until:
            rclpy.spin_once(n,timeout_sec=.05)
            if proc is not None and proc.poll() is not None:
                raise RuntimeError('launch exited before '+label+'; inspect launch.log')
            if min_clearance < 0:
                raise RuntimeError(f'footprint clearance {min_clearance:.3f} m at {truth}')
            if check(): return
        raise RuntimeError(f'{label}: timed out, state={last_state}, guard={guard}, truth={truth}, cmd={cmd}')
    def service(client,request,label):
        wait(client.service_is_ready,label+' discovery',10)
        fut=client.call_async(request)
        wait(fut.done,label+' response',8)
        if not fut.result().success: raise RuntimeError(label+' rejected')
        log('service',name=label)
    def event(kind,duration=0.):
        m=RaceCommand()
        m.stamp=n.get_clock().now().to_msg();m.race_id='sim';m.target_robot='pinky'
        m.source_id='trial_judge';m.command_id=kind+'-'+str(time.monotonic_ns())
        m.kind=kind;m.duration_s=duration;events.publish(m);log('event',kind=kind)
    def hold(check,duration,label):
        # Require a continuous interval with live command and truth samples.
        since=None
        def held():
            nonlocal since
            if not check():
                since=None;return False
            if since is None: since=truth[4]
            return truth[4]-since>=duration
        wait(held,label,15)
    def moving(): return truth is not None and truth[2]>.035 and cmd[0]>.035
    def stopped(): return truth is not None and truth[2]<.015 and truth[3]<.08 and cmd==(0.,0.)
    proc=bag=None
    logs=(folder/'launch.log').open('w')
    env=os.environ.copy()
    laps=3 if args.case=='clean' else 1
    launch=['ros2','launch','pinky_gp_bringup','single_gazebo.launch.py',
            'backend:='+args.backend,'gui:='+str(args.gui).lower(),'laps:='+str(laps),
            'track_dir:='+str(folder/'track'),'seed:='+str(args.seed)]
    try:
        proc=subprocess.Popen(launch,stdout=logs,stderr=subprocess.STDOUT,start_new_session=True,env=env)
        if args.bag:
            bag=subprocess.Popen(['ros2','bag','record','-o',str(folder/'bag'),'/clock',
                '/map','/tf','/tf_static','/scan','/odom','/amcl_pose','/gp/candidate',
                '/gp/sim_cmd_vel','/gp/truth','/gp/status','/gp/event','/gp/guard_state'],
                stdout=logs,stderr=subprocess.STDOUT,start_new_session=True,env=env)
        wait(lambda: last_state=='READY' and counts['scan'] and counts['odom'] and truth,'sensor readiness',75)
        if n.count_publishers('/gp/sim_cmd_vel')!=1: raise RuntimeError('motor publisher ownership')
        service(start,Trigger.Request(),'start')
        wait(moving,'first physical motion',15)
        if args.case in ('cone','barrier'):
            active_box=args.case
            req=SpawnEntity.Request();factory=req.entity_factory
            factory.name=active_box;factory.sdf=track.event_sdf(active_box)
            x,y,_,_=track.EVENT_BOXES[active_box]
            factory.pose.position.x=x;factory.pose.position.y=y;factory.pose.position.z=.16
            factory.pose.orientation.w=1.
            service(add,req,'spawn '+active_box)
            if active_box=='cone':
                wait(lambda: counts['state_BYPASS']>=3,'cone bypass')
            else:
                hold(lambda: stopped() and last_state in ('NO_CLEAR_LANE','BRAKING_ARC_BLOCKED','FOOTPRINT_BLOCKED'),
                     1.0,'barrier stop')
                req=DeleteEntity.Request();req.entity.name=active_box;req.entity.type=req.entity.MODEL
                service(remove,req,'remove barrier');active_box=None
                wait(moving,'resume after barrier')
        elif args.case=='watchdog':
            hold(moving,.4,'running before pause')
            start_wall=time.monotonic();req=ControlWorld.Request();req.world_control.pause=True
            service(world,req,'pause')
            wait(lambda: cmd==(0.,0.) and 'STALE' in guard and commanded_at>=start_wall,
                 'steady watchdog',2.0)
            report['watchdog_zero_wall_s']=round(time.monotonic()-start_wall,3)
            if report['watchdog_zero_wall_s']>1.: raise RuntimeError('watchdog exceeded 1.0 wall second')
            req.world_control.pause=False;service(world,req,'unpause');wait(moving,'resume with fresh data')
        elif args.case=='rules':
            for kind,cap in [('YELLOW',.12),('SC_ON',.09),('GREEN',.24)]:
                event(kind)
                floor=.13 if kind=='GREEN' else .03
                hold(lambda: floor<cmd[0]<=cap+.001 and moving(),.35,kind)
            event('PERSON_ON');hold(lambda: last_state=='PERSON' and stopped(),.5,'person stop')
            event('PERSON_OFF');wait(moving,'person clear')
            event('PENALTY',1.5);hold(lambda: last_state=='PENALTY' and stopped(),1.0,'penalty standstill')
            wait(moving,'penalty release')
            event('RED');hold(lambda: last_state=='RED' and stopped(),.5,'red stop')
            event('GREEN');hold(lambda: last_state=='RED' and stopped(),1.,'terminal red')
        if args.case!='rules':
            wait(lambda: last_state=='FINISHED','finish',args.timeout)
            hold(lambda: last_state=='FINISHED' and stopped(),.5,'finished standstill')
            # The stripe crosses the drivable width, including legal bypass lanes.
            in_stripe = -.08 <= truth[0] <= .15 and abs(truth[1]) <= .31
            if stat['laps']!=laps or truth_gate//4!=laps or not in_stripe:
                raise RuntimeError(f'independent finish gate disagreement: {truth[:2]}, gates={truth_gate}')
        report['passed']=True
    finally:
        report.update(counts=dict(counts),last_state=last_state,truth_laps=truth_gate//4,
            final_truth_xy=list(truth[:2]) if truth else None,
            lap_times_s=stat.get('lap_times_s',[]),wall_s=round(time.monotonic()-begin,2),
            min_margin_m=round(min_clearance,4) if math.isfinite(min_clearance) else None)
        stop_process(bag);stop_process(proc)
        logs.close();trace.close();n.destroy_node();rclpy.try_shutdown()


def main():
    a=options()
    folder=(a.output/(datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'_'+a.backend+'_'+a.case)).resolve()
    folder.mkdir(parents=True)
    os.environ.update(ROS_DOMAIN_ID=str(a.domain),ROS_AUTOMATIC_DISCOVERY_RANGE='LOCALHOST',
                      GZ_PARTITION='gp_'+str(os.getpid())+'_'+folder.name)
    report={'backend':a.backend,'case':a.case,'seed':a.seed,'passed':False}
    try:
        if not shutil.which('ros2'): raise RuntimeError('source /opt/ros/jazzy/setup.bash and the workspace install/setup.bash')
        if a.backend=='gazebo' and not shutil.which('gz'): raise RuntimeError('Gazebo Harmonic missing')
        run(a,folder,report)
    except (ImportError,RuntimeError,OSError,KeyboardInterrupt) as exc:
        report['failure']=str(exc) or 'interrupted'
    finally:
        (folder/'result.json').write_text(json.dumps(report,indent=2)+'\n')
    print(folder/'result.json',json.dumps(report),flush=True)
    return 0 if report['passed'] else 1


if __name__=='__main__': sys.exit(main())
