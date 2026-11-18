"""Dedicated owner of the simulator motor topic; wall watchdog survives /clock pauses."""
import time

import rclpy
from geometry_msgs.msg import Twist, TwistStamped
from nav_msgs.msg import Odometry
from rclpy.clock import Clock, ClockType
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import LaserScan
from std_srvs.srv import SetBool
from std_msgs.msg import String
from pinky_gp_core.sensor_time import fresh, seconds
from .guard_core import CommandGuard


class SimGuard(Node):
    def __init__(self):
        super().__init__('sim_guard')
        if not self.get_parameter('use_sim_time').value:
            raise ValueError('simulation time required')
        self.guard=CommandGuard(.24,1.65,.65,required=('scan','odom'))
        self.guard.select('tracker')
        self.stamps={}
        self.last_ros=0.
        self.pub=self.create_publisher(Twist,'/gp/sim_cmd_vel',1)
        self.state=self.create_publisher(String,'/gp/guard_state',10)
        self.create_subscription(TwistStamped,'/gp/candidate',self.candidate,1)
        self.create_subscription(LaserScan,'/scan',lambda m:self.observe('scan',m),qos_profile_sensor_data)
        self.create_subscription(Odometry,'/odom',lambda m:self.observe('odom',m),qos_profile_sensor_data)
        self.create_service(SetBool,'/gp/stop',self.stop)
        self.create_timer(.04,self.tick,clock=Clock(clock_type=ClockType.STEADY_TIME))

    def now_s(self):
        return self.get_clock().now().nanoseconds*1e-9

    def observe(self,key,m):
        stamp=seconds(m.header.stamp)
        if stamp>self.stamps.get(key,-1.) and fresh(stamp,self.now_s(),.35):
            self.stamps[key]=stamp
            self.guard.observe(key,time.monotonic())

    def candidate(self,m):
        at=seconds(m.header.stamp)
        v,w=m.twist.linear.x,m.twist.angular.z
        if v==0. and w==0.:
            self.guard.receive('tracker',0.,0.,time.monotonic())
        elif (m.header.frame_id=='base_footprint' and fresh(at,self.now_s(),.35)
              and at>self.stamps.get('candidate',-1.)):
            self.stamps['candidate']=at
            self.guard.receive('tracker',v,w,time.monotonic())

    def stop(self,request,response):
        self.guard.stop('OPERATOR',request.data)
        if request.data: self.pub.publish(Twist())
        # In-flight messages captured before release cannot restart the wheels.
        self.stamps['candidate']=self.now_s()
        response.success=True
        response.message='STOPPED' if request.data else 'WAIT_NEW_COMMAND'
        return response

    def tick(self):
        now=self.now_s()
        if now+1e-6<self.last_ros:
            self.guard.stop('CLOCK_RESET_RELAUNCH')
        self.last_ros=now
        v,w,reasons=self.guard.tick(time.monotonic())
        if (v or w) and any(not fresh(self.stamps.get(k,-1.),now,.35)
                            for k in ('scan','odom','candidate')):
            v=w=0.
            reasons=('STALE_HEADER',)
        msg=Twist()
        msg.linear.x=v
        msg.angular.z=w
        self.pub.publish(msg)
        self.state.publish(String(data=','.join(reasons) or 'OK'))


def main(args=None):
    rclpy.init(args=args)
    node=SimGuard()
    try: rclpy.spin(node)
    except KeyboardInterrupt: pass
    finally:
        if rclpy.ok(): node.pub.publish(Twist())
        node.destroy_node()
        rclpy.try_shutdown()
