cmake_minimum_required(VERSION 3.8)
project(pinky_gp_interfaces)
find_package(ament_cmake REQUIRED)
find_package(rosidl_default_generators REQUIRED)
find_package(std_msgs REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(builtin_interfaces REQUIRED)
rosidl_generate_interfaces(${PROJECT_NAME}
  "msg/RaceControl.msg"
  "msg/RaceCommand.msg"
  "msg/RobotStatus.msg"
  "msg/Detection.msg"
  "msg/MotionStatus.msg"
  "msg/RaceProgress.msg"
  "msg/MapReady.msg"
  "msg/EffectState.msg"
  "msg/StopState.msg"
  "srv/SubmitCommand.srv"
  DEPENDENCIES std_msgs geometry_msgs builtin_interfaces)
ament_export_dependencies(rosidl_default_runtime)
ament_package()
