"""ROS PoseStamped -> candidate Twist. Never remap output directly to hardware.
The upstream localization adapter must transform pose into the JSON path frame.
"""
import json, math, time
from pathlib import Path
from .pure_pursuit import PurePursuit, LapProgress

def main(args=None):
    import rclpy
    from rclpy.node import Node
    from rclpy.qos import qos_profile_sensor_data
    from geometry_msgs.msg import PoseStamped, Twist
    from std_msgs.msg import Bool, String
    class TrackingNode(Node):
        def __init__(self):
            super().__init__('pinky_gp_tracking')
            for k,v in [('path_file',''),('pose_timeout',.25),('lookahead',.25),('speed',.15),('max_angular',.8),('max_error',.35),('target_laps',3)]:self.declare_parameter(k,v)
            get=lambda k:self.get_parameter(k).value
            payload=json.loads(Path(get('path_file')).read_text())
            self.frame=payload['frame_id']
            if not isinstance(self.frame,str) or not self.frame:raise ValueError('path frame required')
            self.controller=PurePursuit(payload['points'],get('lookahead'),get('speed'),get('max_angular'),get('max_error'))
            self.timeout=float(get('pose_timeout'));self.target=int(get('target_laps'))
            if not math.isfinite(self.timeout) or self.timeout<=0 or self.target<=0:raise ValueError('invalid timeout/laps')
            self.progress=LapProgress(self.controller.path.length,min(self.controller.path.length/8,.2))
            self.pose=None;self.received=None;self.enabled=False;self.done=False
            self.pub=self.create_publisher(Twist,'candidate/nav',10)
            self.status=self.create_publisher(String,'tracking/status',10)
            self.create_subscription(PoseStamped,'tracking/pose',self.on_pose,qos_profile_sensor_data)
            self.create_subscription(Bool,'tracking/enable',self.on_enable,10)
            self.create_timer(.05,self.tick)
        def on_enable(self,msg):
            self.enabled=msg.data
            self.pose=None  # A new pose is required after either transition.
        def on_pose(self,msg):
            self.pose=None
            if msg.header.frame_id!=self.frame:return
            stamp=msg.header.stamp.sec+msg.header.stamp.nanosec*1e-9
            age=self.get_clock().now().nanoseconds*1e-9-stamp
            q=msg.pose.orientation;p=msg.pose.position
            if not all(math.isfinite(v) for v in (p.x,p.y,q.x,q.y,q.z,q.w)):return
            norm=q.x*q.x+q.y*q.y+q.z*q.z+q.w*q.w
            if not .99<=norm<=1.01 or not 0<=age<=self.timeout:return
            yaw=math.atan2(2*(q.w*q.z+q.x*q.y),1-2*(q.y*q.y+q.z*q.z))
            self.pose=(p.x,p.y,yaw);self.received=time.monotonic()
        def tick(self):
            out=Twist();reason='DISABLED';lap=self.progress.quarters//4
            if self.done:reason='FINISHED'
            elif self.enabled:
                if self.pose is None or self.received is None or time.monotonic()-self.received>self.timeout:reason='POSE_TIMEOUT_OR_INVALID'
                else:
                    try:
                        v,w,p=self.controller.update(*self.pose);lap=self.progress.update(p['s'])
                        self.done=lap>=self.target
                        if not self.done:out.linear.x=v;out.angular.z=w
                        reason='FINISHED' if self.done else 'TRACKING'
                    except ValueError as exc:
                        self.enabled=False;reason=str(exc)
            self.pub.publish(out);self.status.publish(String(data=json.dumps({'reason':reason,'laps':lap})))
    rclpy.init(args=args);node=None
    try:
        node=TrackingNode();rclpy.spin(node)
    finally:
        if node is not None:
            node.pub.publish(Twist());node.destroy_node()
        rclpy.shutdown()
