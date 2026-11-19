"""Explicit simulation or measured hardware limits shared by planner and motor guard."""
import json
import math
from pathlib import Path
from .hardware_limits import Limits
from .raceline import RacingProfile


def load_profile(path,hardware=False):
    data=json.loads(Path(path).read_text())
    if data.get('environment') not in ('simulation','hardware'):
        raise ValueError('profile environment required')
    if hardware and (data['environment']!='hardware' or data.get('verified') is not True
                     or not data.get('measurement_record')):
        raise ValueError('hardware requires verified measurements and their record')
    radius=data['radius_m']
    if not math.isfinite(radius) or radius<=0:raise ValueError('invalid robot radius')
    return RacingProfile(Limits(**data['limits']),data['acceleration_mps2'],
                         data['wheel_speed_mps'],data['wheel_separation_m']),radius
