from setuptools import find_packages, setup
from glob import glob
import os
name = 'pinky_gp_recon'
setup(name=name, version='0.1.0', packages=find_packages(exclude=['test']),
      data_files=[('share/ament_index/resource_index/packages', ['resource/'+name]),
                  ('share/'+name, ['package.xml']),
                  ('share/'+name+'/launch', glob('launch/*.launch.py')),
                  ('share/'+name+'/config', glob('config/*'))],
      install_requires=['setuptools'], zip_safe=True,
      maintainer='Pinky GP Team', maintainer_email='team@example.invalid',
      description='지도 없는 정찰과 지도 확정', license='UNLICENSED',
      entry_points={'console_scripts': ['recon_manager = pinky_gp_recon.recon_manager:main', 'wall_follower = pinky_gp_recon.wall_follower:main', 'map_finalize = pinky_gp_recon.map_finalize:main']})
