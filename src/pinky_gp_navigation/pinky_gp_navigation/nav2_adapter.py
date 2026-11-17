"""A/S04. 비동기 FollowPath 연결을 위한 transport-independent 계약.
실제 Nav2 action 호출은 미연결. 아래 transport protocol을 구현하고 ROS executor에서
feedback/result/cancel callback을 이 상태 기계에 전달한다. 취소 ACK 전 새 goal 금지.
"""
class NavigationSession:
    def __init__(self):
        self.state = 'IDLE'; self.goal_id = None

    def request(self, goal_id, path_valid, server_ready):
        if self.state != 'IDLE' or not goal_id or not path_valid or not server_ready:
            return False
        self.goal_id, self.state = goal_id, 'PENDING'
        return True

    def accepted(self, goal_id, accepted):
        if goal_id != self.goal_id or self.state != 'PENDING': return False
        self.state = 'ACTIVE' if accepted else 'FAILED'
        return True

    def cancel(self):
        if self.state != 'ACTIVE': return False
        self.state = 'CANCELING'; return True

    def result(self, goal_id, success=False, canceled=False):
        if goal_id != self.goal_id or self.state not in {'ACTIVE','CANCELING'}: return False
        self.state = 'IDLE' if canceled or success else 'FAILED'
        self.goal_id = None
        return True

def demo():
    n = NavigationSession(); n.request('lap-segment-1',True,True)
    n.accepted('lap-segment-1',True); n.cancel()
    blocked = n.request('lap-segment-2',True,True)
    n.result('lap-segment-1',canceled=True)
    return {'goal_during_cancel': blocked, 'after_ack': n.state}


def main(args=None):
    from pinky_gp_core.guide_cli import run
    run("navigation/nav2_adapter", demo, args)


if __name__ == "__main__":
    main()
