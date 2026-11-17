"""Display selection only. No LCD or LED driver is included."""
def display_state(stops, restriction='NORMAL', drs_active=False, finished=False,
                  phase='RACING', fresh=False):
    reasons = set(stops)
    if not fresh or reasons & {'ESTOP', 'FAULT', 'TIMEOUT'}:
        return 'RED', 'FAULT'
    if 'RED' in reasons:
        return 'RED', 'RACE ABORTED'
    if reasons & {'PERSON', 'COLLISION'}:
        return 'RED', 'STOP PERSON / COLLISION'
    if 'PENALTY' in reasons:
        return 'MAGENTA', 'PENALTY'
    if reasons - {'FINISHED'}:
        return 'RED', 'STOP'
    if finished or 'FINISHED' in reasons:
        return 'WHITE', 'FINISHED'
    if restriction == 'SC':
        return 'YELLOW_SLOW', 'SC'
    if restriction == 'YELLOW':
        return 'YELLOW', 'YELLOW'
    if phase != 'RACING':
        return 'BLUE', phase
    if drs_active:
        return 'GREEN', 'DRS ON'
    return 'WHITE_DIM', 'LAP TIMER'
