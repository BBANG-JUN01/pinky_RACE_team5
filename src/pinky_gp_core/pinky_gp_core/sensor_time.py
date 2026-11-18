"""Header age in ROS time and delivery age in steady time are separate checks."""
import math


def seconds(stamp):
    return stamp.sec+stamp.nanosec/1_000_000_000


def fresh(stamp, now, limit):
    return all(math.isfinite(v) for v in (stamp,now)) and stamp > 0 and 0 <= now-stamp <= limit


def yaw(quaternion):
    x,y,z,w = quaternion.x,quaternion.y,quaternion.z,quaternion.w
    if not .98 <= x*x+y*y+z*z+w*w <= 1.02:
        raise ValueError('INVALID_QUATERNION')
    return math.atan2(2*(w*z+x*y),1-2*(y*y+z*z))
