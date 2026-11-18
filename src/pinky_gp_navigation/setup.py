from setuptools import find_packages, setup
from glob import glob
import os
name = 'pinky_gp_navigation'
setup(name=name, version='0.1.0', packages=find_packages(exclude=['test']),
      data_files=[('share/ament_index/resource_index/packages', ['resource/'+name]),
                  ('share/'+name, ['package.xml']),
                  ('share/'+name+'/launch', glob('launch/*.launch.py')),
                  ('share/'+name+'/config', glob('config/*'))],
      install_requires=['setuptools'], zip_safe=True,
      maintainer='Pinky GP Team', maintainer_email='team@example.invalid',
      description='경기 경로 생성과 Nav2 어댑터', license='UNLICENSED',
      entry_points={'console_scripts': ['sensor_driver = pinky_gp_navigation.sensor_driver:main', 'tracking_node = pinky_gp_navigation.tracking_node:main', 'path_manager = pinky_gp_navigation.path_manager:main', 'nav2_adapter = pinky_gp_navigation.nav2_adapter:main', 'grid_manager = pinky_gp_navigation.grid_manager:main']})

