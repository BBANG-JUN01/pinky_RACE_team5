from setuptools import find_packages, setup
from glob import glob
import os
name = 'pinky_gp_display'
setup(name=name, version='0.1.0', packages=find_packages(exclude=['test']),
      data_files=[('share/ament_index/resource_index/packages', ['resource/'+name]),
                  ('share/'+name, ['package.xml']),
                  ('share/'+name+'/launch', glob('launch/*.launch.py')),
                  ('share/'+name+'/config', glob('config/*'))],
      install_requires=['setuptools'], zip_safe=True,
      maintainer='Pinky GP Team', maintainer_email='team@example.invalid',
      description='후면 LED·전면 LCD', license='UNLICENSED',
      entry_points={'console_scripts': ['display_manager = pinky_gp_display.display_manager:main']})
