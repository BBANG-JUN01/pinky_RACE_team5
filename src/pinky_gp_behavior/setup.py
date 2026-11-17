from setuptools import find_packages, setup
from glob import glob
import os
name = 'pinky_gp_behavior'
setup(name=name, version='0.1.0', packages=find_packages(exclude=['test']),
      data_files=[('share/ament_index/resource_index/packages', ['resource/'+name]),
                  ('share/'+name, ['package.xml']),
                  ('share/'+name+'/launch', glob('launch/*.launch.py')),
                  ('share/'+name+'/config', glob('config/*'))],
      install_requires=['setuptools'], zip_safe=True,
      maintainer='Pinky GP Team', maintainer_email='team@example.invalid',
      description='추종·추월·DRS·속도 정책', license='UNLICENSED',
      entry_points={'console_scripts': ['behavior_manager = pinky_gp_behavior.behavior_manager:main', 'speed_policy = pinky_gp_behavior.speed_policy:main']})
