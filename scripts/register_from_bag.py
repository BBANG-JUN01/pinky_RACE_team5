"""Create a persistent pre-race map using only laser, TF, odometry and bag time."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import time


def main():
    p=argparse.ArgumentParser()
    p.add_argument('bag',type=Path)
    p.add_argument('output',type=Path,help='new, empty output directory')
    p.add_argument('--domain',type=int,default=84)
    p.add_argument('--rate',type=float,default=1.)
    a=p.parse_args()
    if not .1<=a.rate<=5 or not 0<=a.domain<=100: p.error('invalid rate/domain')
    source=a.bag.resolve();out=a.output.resolve()
    if not (source/'metadata.yaml').is_file(): p.error('bag directory must contain metadata.yaml')
    if out.exists() and any(out.iterdir()): p.error('choose an empty output directory')
    out.mkdir(parents=True,exist_ok=True)
    os.environ.update(ROS_DOMAIN_ID=str(a.domain),ROS_AUTOMATIC_DISCOVERY_RANGE='LOCALHOST')
    import yaml
    import rclpy
    from rclpy.node import Node
    from rclpy.qos import QoSProfile,DurabilityPolicy
    from nav_msgs.msg import OccupancyGrid
    from lifecycle_msgs.srv import GetState
    from ament_index_python.packages import get_package_share_directory
    from run_single_trial import stop_process
    meta=yaml.safe_load((source/'metadata.yaml').read_text())['rosbag2_bagfile_information']
    topics={v['topic_metadata']['name'] for v in meta['topics_with_message_count'] if v['message_count']>0}
    needed={'/scan','/tf','/tf_static'}
    if not needed<=topics: p.error('missing required topics '+str(sorted(needed-topics)))
    cfg=Path(get_package_share_directory('slam_toolbox'))/'config/mapper_params_online_sync.yaml'
    params=yaml.safe_load(cfg.read_text())
    params['slam_toolbox']['ros__parameters'].update(map_frame='survey_map',resolution=.03,
        minimum_time_interval=.08,minimum_travel_distance=.045,minimum_travel_heading=.08,
        map_update_interval=.5,transform_timeout=.3,max_laser_range=12.)
    params_file=out/'slam_config.yaml'
    params_file.write_text(yaml.safe_dump(params))
    rclpy.init()
    node=Node('registration_judge')
    received=[]
    durable=QoSProfile(depth=1,durability=DurabilityPolicy.TRANSIENT_LOCAL)
    node.create_subscription(OccupancyGrid,'/map',lambda m:received.__setitem__(slice(None),[m]),durable)
    state=node.create_client(GetState,'/slam_toolbox/get_state')
    log=(out/'mapping.log').open('w')
    slam=play=None
    try:
        slam=subprocess.Popen(['ros2','launch','slam_toolbox','online_sync_launch.py',
            'use_sim_time:=true','slam_params_file:='+str(params_file)],stdout=log,stderr=subprocess.STDOUT,
            start_new_session=True)
        deadline=time.monotonic()+30
        while time.monotonic()<deadline:
            if slam.poll() is not None: raise RuntimeError('SLAM launch exited; see mapping.log')
            if state.wait_for_service(.5):
                f=state.call_async(GetState.Request())
                rclpy.spin_until_future_complete(node,f,timeout_sec=1.)
                if f.done() and f.result().current_state.label=='active':break
            time.sleep(.15)
        else: raise RuntimeError('SLAM did not activate')
        # Simulated bags have their original clock; hardware logs use rosbag playback time.
        select=sorted((needed|{'/clock','/odom'}) & topics)
        cmd=['ros2','bag','play',str(source),'--rate',str(a.rate),'--topics',*select]
        if '/clock' not in topics:cmd+=['--clock','40']
        play=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
        duration=meta['duration']['nanoseconds']*1e-9
        deadline=time.monotonic()+duration/a.rate+40
        while play.poll() is None and time.monotonic()<deadline:
            rclpy.spin_once(node,timeout_sec=.1)
        if play.poll()!=0: raise RuntimeError('bag playback failed or timed out')
        for _ in range(12): rclpy.spin_once(node,timeout_sec=.1)
        if not received:raise RuntimeError('no SLAM map; check scan frame, /clock and /tf_static')
        m=received[-1]
        if m.header.frame_id!='survey_map' or min(m.info.width,m.info.height)<8 or not any(v>=65 for v in m.data):
            raise RuntimeError('empty or unregistered SLAM map')
        subprocess.run(['ros2','run','nav2_map_server','map_saver_cli','-t','/map','-f',str(out/'map'),
            '--fmt','pgm','--ros-args','-p','map_subscribe_transient_local:=true',
            '-p','save_map_timeout:=8.0'],stdout=log,stderr=subprocess.STDOUT,timeout=20,check=True)
        if not all((out/f).is_file() for f in ('map.pgm','map.yaml')):
            raise RuntimeError('map export incomplete')
        stats={'source_bag':source.name,'topics_replayed':select,'frame':m.header.frame_id,
            'resolution_m':m.info.resolution,'width':m.info.width,'height':m.info.height,
            'occupied_cells':sum(v>=65 for v in m.data),'free_cells':sum(0<=v<=25 for v in m.data)}
        (out/'registration.json').write_text(json.dumps(stats,indent=2)+'\n')
        print(out/'map.yaml',stats)
    finally:
        stop_process(play);stop_process(slam);log.close();node.destroy_node();rclpy.try_shutdown()


if __name__=='__main__': main()
