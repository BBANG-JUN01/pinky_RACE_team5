"""Official Pinky Pro differential drive, encoder odometry, GPU lidar and Nav2 AMCL."""
import os
import tempfile
from pathlib import Path
from xml.etree import ElementTree as ET
import xacro
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess, OpaqueFunction, SetEnvironmentVariable, Shutdown
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from pinky_gp_navigation.track_fixture import write_track


def start(context):
    def arg(k): return LaunchConfiguration(k).perform(context)
    directory = Path(arg('track_dir') or tempfile.mkdtemp(prefix='pinky_gp_track_'))
    write_track(directory)
    description = Path(get_package_share_directory('pinky_description'))
    model = ET.fromstring(xacro.process_file(str(description/'urdf/robot.urdf.xacro'),
                           mappings={'namespace':'','is_sim':'true'}).toxml())
    # The optional vendor lamp plugin is outside this driving fixture.
    gazebo = next(g for g in model.findall('gazebo') if g.find('plugin') is not None)
    for plugin in gazebo.findall('plugin'):
        if plugin.get('name')=='pinky_gz_sim::LampControlPlugin': gazebo.remove(plugin)
    truth = ET.SubElement(gazebo,'plugin',filename='gz-sim-odometry-publisher-system',
                          name='gz::sim::systems::OdometryPublisher')
    for k,v in {'odom_topic':'/gp/truth','odom_frame':'world','robot_base_frame':'pinky',
                'dimensions':'2','odom_publish_frequency':'30','tf_topic':'/gp/truth_tf'}.items():
        ET.SubElement(truth,k).text=v
    sim = {'use_sim_time':True}
    config = Path(get_package_share_directory('pinky_gp_bringup'))/'config/sim_bridge.yaml'
    def node(pkg, exe, name, params=None, **kw):
        return Node(package=pkg,executable=exe,name=name,output='screen',
                    parameters=[{**sim,**(params or {})}],**kw)
    cmd=['gz','sim','-r','-v','2']
    if arg('gui').lower()!='true': cmd += ['-s','--headless-rendering']
    cmd.append(str(directory/'track.sdf'))
    resources=os.pathsep.join(filter(None,[str(description.parent),os.environ.get('GZ_SIM_RESOURCE_PATH')]))
    gazebo_actions = [
        SetEnvironmentVariable('GZ_SIM_RESOURCE_PATH',resources),
        ExecuteProcess(cmd=cmd,output='screen',on_exit=Shutdown(reason='Gazebo server exited')),
        node('ros_gz_bridge','parameter_bridge','gp_bridge',{'config_file':str(config)},arguments=[
             '/world/pinky_gp/create@ros_gz_interfaces/srv/SpawnEntity',
             '/world/pinky_gp/remove@ros_gz_interfaces/srv/DeleteEntity',
             '/world/pinky_gp/control@ros_gz_interfaces/srv/ControlWorld']),
        node('ros_gz_sim','create','spawn_pinky',arguments=['-world','pinky_gp','-topic','/robot_description',
             '-name','pinky','-x','0','-y','0','-z','0.10']),
    ]
    backend=arg('backend')
    if backend not in ('gazebo','ros_fixture'): raise ValueError('unknown backend')
    simulation = gazebo_actions if backend=='gazebo' else [
        node('pinky_gp_bringup','ray_sensor','ray_sensor',{'seed':int(arg('seed'))})]
    return simulation+[
        node('robot_state_publisher','robot_state_publisher','robot_state_publisher',
             {'robot_description':ParameterValue(ET.tostring(model,encoding='unicode'),value_type=str)}),
        node('nav2_map_server','map_server','map_server',{'yaml_filename':str(directory/'map.yaml')}),
        node('nav2_amcl','amcl','amcl',{'set_initial_pose':True,'initial_pose.x':0.,
             'initial_pose.y':0.,'initial_pose.yaw':0.,'base_frame_id':'base_footprint',
             'odom_frame_id':'odom','global_frame_id':'map','scan_topic':'scan',
             'update_min_d':.025,'update_min_a':.045,'transform_tolerance':.25,
             'min_particles':350,'max_particles':1100,'sigma_hit':.06,
             'laser_likelihood_max_dist':.55,'alpha1':.05,'alpha2':.05,'alpha3':.05,'alpha4':.05}),
        node('nav2_lifecycle_manager','lifecycle_manager','lifecycle_localization',
             {'autostart':True,'node_names':['map_server','amcl']}),
        node('pinky_gp_guard','sim_guard','sim_guard',on_exit=Shutdown(reason='motor guard exited')),
        node('pinky_gp_navigation','sensor_driver','sensor_driver',
             {'path_file':str(directory/'path.json'),'target_laps':int(arg('laps'))})]


def generate_launch_description():
    return LaunchDescription([DeclareLaunchArgument('gui',default_value='false'),
        DeclareLaunchArgument('backend',default_value='gazebo'),DeclareLaunchArgument('seed',default_value='0'),
        DeclareLaunchArgument('laps',default_value='3'),DeclareLaunchArgument('track_dir',default_value=''),
        OpaqueFunction(function=start)])
