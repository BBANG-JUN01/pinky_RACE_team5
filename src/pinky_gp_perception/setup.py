from setuptools import find_packages, setup
from glob import glob
import os
name = 'pinky_gp_perception'
setup(name=name, version='0.1.0', packages=find_packages(exclude=['test']),
      data_files=[('share/ament_index/resource_index/packages', ['resource/'+name]),
                  ('share/'+name, ['package.xml']),
                  ('share/'+name+'/launch', glob('launch/*.launch.py')),
                  ('share/'+name+'/config', glob('config/*'))],
      install_requires=['setuptools'], zip_safe=True,
      maintainer='Pinky GP Team', maintainer_email='team@example.invalid',
      description='카메라·YOLO·깃발·그리드 인식', license='UNLICENSED',
      entry_points={'console_scripts': ['detector = pinky_gp_perception.detector:main', 'signal_reader = pinky_gp_perception.signal_reader:main', 'range_association = pinky_gp_perception.range_association:main', 'grid_reader = pinky_gp_perception.grid_reader:main']})
