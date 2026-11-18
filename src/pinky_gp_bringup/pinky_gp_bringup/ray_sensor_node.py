"""ROS test stimulus for hosts without Gazebo transport. Ground truth is score-only."""
import math
import random
import rclpy
from builtin_interfaces.msg import Time
from geometry_msgs.msg import TransformStamped, Twist
from nav_msgs.msg import Odometry
from rclpy.node import Node
from rclpy.clock import Clock,ClockType
from rclpy.qos import qos_profile_sensor_data
from rosgraph_msgs.msg import Clock as ClockMessage
from ros_gz_interfaces.srv import SpawnEntity,DeleteEntity,ControlWorld
from sensor_msgs.msg import LaserScan
from tf2_ros import TransformBroadcaster
from pinky_gp_navigation import track_fixture as track


class RaySensor(Node):
    def __init__(self):
        super().__init__('ray_sensor')
        self.ticks=0
        self.pose=[0.,0.,0.]
        self.odo=[0.,0.,0.]
        self.v=self.w=self.target_v=self.target_w=0.
        self.paused=False
        self.objects={}
        self.rng=random.Random(self.declare_parameter('seed',0).value)
        self.clock_pub=self.create_publisher(ClockMessage,'/clock',10)
        self.scan_pub=self.create_publisher(LaserScan,'/scan',qos_profile_sensor_data)
        self.odom_pub=self.create_publisher(Odometry,'/odom',10)
        self.truth_pub=self.create_publisher(Odometry,'/gp/truth',10)
        self.tf=TransformBroadcaster(self)
        self.create_subscription(Twist,'/gp/sim_cmd_vel',self.cmd,1)
        self.create_service(SpawnEntity,'/world/pinky_gp/create',self.spawn)
        self.create_service(DeleteEntity,'/world/pinky_gp/remove',self.remove)
        self.create_service(ControlWorld,'/world/pinky_gp/control',self.control)
        self.create_timer(.012,self.tick,clock=Clock(clock_type=ClockType.STEADY_TIME))

    def spawn(self,req,res):
        name=req.entity_factory.name
        res.success=name in track.EVENT_BOXES and name not in self.objects
        if res.success: self.objects[name]=track.EVENT_BOXES[name]
        return res

    def remove(self,req,res):
        res.success=self.objects.pop(req.entity.name,None) is not None
        return res

    def control(self,req,res):
        self.paused=req.world_control.pause
        res.success=True
        return res

    def cmd(self,m):
        self.target_v,self.target_w=m.linear.x,m.angular.z

    def odometry(self,pose,frame,child,stamp):
        msg=Odometry()
        msg.header.stamp=stamp;msg.header.frame_id=frame;msg.child_frame_id=child
        msg.pose.pose.position.x,msg.pose.pose.position.y=pose[:2]
        msg.pose.pose.orientation.z=math.sin(pose[2]/2)
        msg.pose.pose.orientation.w=math.cos(pose[2]/2)
        msg.twist.twist.linear.x=self.v;msg.twist.twist.angular.z=self.w
        return msg

    def tick(self):
        if self.paused: return
        self.ticks+=1
        # 50 Hz encoder/clock, 10 Hz laser. Wheel odometry has a scale error.
        dt=.02
        stamp=Time(sec=self.ticks//50,nanosec=(self.ticks%50)*20_000_000)
        self.clock_pub.publish(ClockMessage(clock=stamp))
        self.v+=max(-.6*dt,min(.6*dt,self.target_v-self.v))
        self.w+=max(-3.*dt,min(3.*dt,self.target_w-self.w))
        for pose,mult in ((self.pose,1.),(self.odo,1.003)):
            a=pose[2]+self.w*dt/2
            pose[0]+=self.v*mult*dt*math.cos(a);pose[1]+=self.v*mult*dt*math.sin(a)
            pose[2]+=self.w*dt
        od=self.odometry(self.odo,'odom','base_footprint',stamp)
        self.odom_pub.publish(od)
        self.truth_pub.publish(self.odometry(self.pose,'world','pinky',stamp))
        tf=TransformStamped()
        tf.header=od.header;tf.child_frame_id=od.child_frame_id
        tf.transform.translation.x,tf.transform.translation.y=self.odo[:2]
        tf.transform.rotation=od.pose.pose.orientation
        self.tf.sendTransform(tf)
        if self.ticks%5: return
        msg=LaserScan()
        msg.header.stamp=stamp;msg.header.frame_id='rplidar_link'
        n=160
        msg.angle_min=-math.pi;msg.angle_increment=2*math.pi/(n-1);msg.angle_max=math.pi
        msg.range_min=.05;msg.range_max=12.;msg.scan_time=.1
        x,y,a=self.pose
        x-=.017*math.cos(a);y-=.017*math.sin(a)
        boxes=track.WALLS+tuple(self.objects.values())
        msg.ranges=[track.ray(x,y,a+i*msg.angle_increment,boxes)+self.rng.gauss(0,.004)
                    for i in range(n)]
        self.scan_pub.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node=RaySensor()
    try: rclpy.spin(node)
    except KeyboardInterrupt: pass
    finally:
        node.destroy_node();rclpy.try_shutdown()
