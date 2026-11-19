"""One physical robot per ROS_DOMAIN_ID. Start vendor sensor/base bringup first."""
import json
from pathlib import Path
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument,OpaqueFunction,Shutdown
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from pinky_gp_navigation.vehicle_profile import load_profile


def start(context):
    def arg(key):return LaunchConfiguration(key).perform(context)
    profile=Path(arg('limits_file')).resolve()
    load_profile(profile,hardware=True)
    map_file=Path(arg('map_file')).resolve()
    path_file=Path(arg('path_file')).resolve()
    if not map_file.is_file() or not path_file.is_file():raise ValueError('registered map and path required')
    if json.loads(path_file.read_text())['frame_id']!='map':raise ValueError('map-frame path required')
    def node(pkg,exe,name,parameters=None,**kw):
        return Node(package=pkg,executable=exe,name=name,output='screen',
                    parameters=[{'use_sim_time':False,**(parameters or {})}],**kw)
    return [
        node('nav2_map_server','map_server','map_server',{'yaml_filename':str(map_file)}),
        node('nav2_amcl','amcl','amcl',{'set_initial_pose':False,'base_frame_id':'base_footprint',
             'odom_frame_id':'odom','global_frame_id':'map','scan_topic':'scan',
             'update_min_d':.025,'update_min_a':.045,'transform_tolerance':.25}),
        node('nav2_lifecycle_manager','lifecycle_manager','lifecycle_localization',
             {'autostart':True,'node_names':['map_server','amcl']}),
        node('pinky_gp_guard','sim_guard','motor_guard',{'limits_file':str(profile)},
             remappings=[('/gp/sim_cmd_vel',arg('motor_topic'))],
             on_exit=Shutdown(reason='motor guard exited')),
        node('pinky_gp_navigation','sensor_driver','sensor_driver',
             {'limits_file':str(profile),'path_file':str(path_file),'target_laps':int(arg('laps')),
              'robot_id':arg('robot_id'),'race_id':arg('race_id')})
    ]


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument('limits_file'),DeclareLaunchArgument('map_file'),
        DeclareLaunchArgument('path_file'),DeclareLaunchArgument('motor_topic',default_value='/cmd_vel'),
        DeclareLaunchArgument('robot_id',default_value='A'),DeclareLaunchArgument('race_id',default_value='race1'),
        DeclareLaunchArgument('laps',default_value='3'),OpaqueFunction(function=start)])
