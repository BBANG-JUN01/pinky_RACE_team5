from setuptools import find_packages, setup
from glob import glob
import os
name = 'pinky_gp_guard'
setup(name=name, version='0.1.0', packages=find_packages(exclude=['test']),
      data_files=[('share/ament_index/resource_index/packages', ['resource/'+name]),
                  ('share/'+name, ['package.xml']),
                  ('share/'+name+'/launch', glob('launch/*.launch.py')),
                  ('share/'+name+'/config', glob('config/*'))],
      install_requires=['setuptools'], zip_safe=True,
      maintainer='Pinky GP Team', maintainer_email='team@example.invalid',
      description='최종 모터 명령과 로컬 정지', license='UNLICENSED',
      entry_points={'console_scripts': ['sim_guard = pinky_gp_guard.sim_guard:main', 'command_guard = pinky_gp_guard.command_guard:main', 'robot_health = pinky_gp_guard.robot_health:main']})

