"""One-robot simulation adapter. Uses TF at laser acquisition time, never truth."""
import json
import math
from pathlib import Path

import rclpy
from geometry_msgs.msg import PoseWithCovarianceStamped, TwistStamped
from nav_msgs.msg import OccupancyGrid, Odometry
from rclpy.clock import Clock, ClockType
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, QoSProfile, qos_profile_sensor_data
from rclpy.time import Time
from sensor_msgs.msg import LaserScan
from std_msgs.msg import String
from std_srvs.srv import Trigger
from tf2_ros import Buffer, TransformException, TransformListener

from pinky_gp_core.sensor_time import fresh, seconds, yaw
from pinky_gp_interfaces.msg import RaceCommand
from .scan_race import Drive, Occupancy, RaceDrive, scan_points


class SensorDriver(Node):
    def __init__(self):
        super().__init__('sensor_driver')
        if not self.get_parameter('use_sim_time').value:
            raise ValueError('simulation time required')
        path = Path(self.declare_parameter('path_file','').value)
        profile = json.loads(path.read_text())
        if profile['frame_id'] != 'map': raise ValueError('path must use map frame')
        self.points = profile['points']
        self.target = self.declare_parameter('target_laps',3).value
        self.race_id = self.declare_parameter('race_id','sim').value
        self.tf = Buffer(node=self)
        self.listener = TransformListener(self.tf,self)
        self.drive = self.scan = self.odom = None
        self.last_consumed = -1.
        self.last_clock = 0.
        self.cov_ok = self.started = self.ready = False
        self.config_fault = ''
        self.candidate = self.create_publisher(TwistStamped,'/gp/candidate',1)
        self.status = self.create_publisher(String,'/gp/status',10)
        retained = QoSProfile(depth=1,durability=DurabilityPolicy.TRANSIENT_LOCAL)
        self.create_subscription(OccupancyGrid,'/map',self.on_map,retained)
        self.create_subscription(PoseWithCovarianceStamped,'/amcl_pose',self.on_amcl,retained)
        self.create_subscription(LaserScan,'/scan',self.on_scan,qos_profile_sensor_data)
        self.create_subscription(Odometry,'/odom',self.on_odom,qos_profile_sensor_data)
        self.create_subscription(RaceCommand,'/gp/event',self.event,10)
        self.create_service(Trigger,'/gp/start',self.start)
        self.create_timer(.025,self.tick,clock=Clock(clock_type=ClockType.STEADY_TIME))

    def ros_now(self):
        return self.get_clock().now().nanoseconds*1e-9

    def on_map(self,m):
        if self.drive:
            return  # One immutable registration per launch.
        try:
            o=m.info.origin
            if m.header.frame_id!='map' or abs(yaw(o.orientation))>1e-5:
                raise ValueError('UNSUPPORTED_MAP_FRAME_OR_ROTATION')
            grid=Occupancy(m.info.width,m.info.height,m.info.resolution,
                           (o.position.x,o.position.y),m.data)
            if any(not grid.clear(p) for p in self.points):
                raise ValueError('REGISTERED_PATH_BLOCKED')
            self.drive=RaceDrive(self.points,grid,self.target,race_id=self.race_id)
        except ValueError as exc:
            self.config_fault=str(exc)

    def on_amcl(self,m):
        c=m.pose.covariance
        self.cov_ok=(m.header.frame_id=='map' and seconds(m.header.stamp)>0
                     and all(math.isfinite(c[i]) and 0 <= c[i] <= .36 for i in (0,7,35)))

    def on_scan(self,m):
        if self.scan is None or seconds(m.header.stamp)>=seconds(self.scan.header.stamp):
            self.scan=m

    def on_odom(self,m):
        self.odom=m

    def start(self,req,res):
        res.success=bool(self.ready and self.drive and not self.drive.policy.aborted
                         and not self.drive.done and not self.drive.fault)
        if res.success: self.started=True
        res.message='STARTED' if res.success else 'WAIT_FOR_READY'
        return res

    def event(self,m):
        now=self.ros_now()
        if (self.drive and m.race_id==self.race_id and m.target_robot in ('pinky','all')
                and fresh(seconds(m.stamp),now,.6)):
            self.drive.event(m.kind,m.command_id,seconds(m.stamp),m.duration_s)

    def publish(self,cmd,stamp):
        msg=TwistStamped()
        msg.header.stamp=stamp
        msg.header.frame_id='base_footprint'
        msg.twist.linear.x=cmd.v
        msg.twist.angular.z=cmd.w
        self.candidate.publish(msg)
        timer=self.drive.timer if self.drive else None
        self.status.publish(String(data=json.dumps({
            'state':cmd.reason,'laps':len(timer.laps) if timer else 0,
            'lap_times_s':timer.laps if timer else [],
            'current_s':timer.current(self.ros_now()) if timer else 0.,
            'last_s':timer.last if timer else None,'best_s':timer.best if timer else None,
            'cross_track_m':cmd.error,'scan_s':seconds(stamp),'race_id':self.race_id})))

    def frame_pose(self,frame,at):
        t=self.tf.lookup_transform('map',frame,at).transform
        return t.translation.x,t.translation.y,yaw(t.rotation)

    def tick(self):
        now=self.ros_now()
        if now+1e-6<self.last_clock: self.config_fault='CLOCK_RESET_RELAUNCH'
        self.last_clock=now
        stamp=self.get_clock().now().to_msg()
        try:
            if self.config_fault: raise ValueError(self.config_fault)
            if not self.drive: raise ValueError('WAIT_MAP')
            if self.drive.policy.aborted: raise ValueError('RED')
            if self.drive.done: raise ValueError('FINISHED')
            if not self.cov_ok: raise ValueError('WAIT_AMCL')
            if self.odom is None or not fresh(seconds(self.odom.header.stamp),now,.35):
                raise ValueError('ODOM_TIMEOUT')
            if self.odom.header.frame_id!='odom' or self.odom.child_frame_id!='base_footprint':
                raise ValueError('ODOM_FRAME')
            if self.scan is None or not fresh(seconds(self.scan.header.stamp),now,.35):
                raise ValueError('SCAN_TIMEOUT')
            stamp=self.scan.header.stamp
            capture=seconds(stamp)
            if capture<=self.last_consumed: return
            at=Time.from_msg(stamp)
            pose=self.frame_pose('base_footprint',at)
            laser=self.frame_pose(self.scan.header.frame_id,at)
            hits=scan_points(self.scan.ranges,self.scan.angle_min,self.scan.angle_increment,
                             self.scan.range_min,self.scan.range_max,laser)
            v=self.odom.twist.twist.linear.x
            w=self.odom.twist.twist.angular.z
            if not all(math.isfinite(a) for a in (*pose,v,w)):
                raise ValueError('INVALID_ODOM_OR_TF')
            self.ready=True
            self.last_consumed=capture
            cmd=self.drive.step(pose,hits,capture,v,w) if self.started else Drive(reason='READY')
        except (TransformException,ValueError) as exc:
            self.ready=False
            reason='WAIT_TF' if isinstance(exc,TransformException) else str(exc)
            # A new scan can precede its odometry transform by one bridge callback.
            # Retry that stamp until the input deadline; the guard owns expiry.
            if reason=='WAIT_TF' and self.started and self.last_consumed>=0 and fresh(self.last_consumed,now,.20):
                return
            cmd=Drive(reason=reason)
        self.publish(cmd,stamp)


def main(args=None):
    rclpy.init(args=args)
    node=SensorDriver()
    try: rclpy.spin(node)
    except KeyboardInterrupt: pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()
