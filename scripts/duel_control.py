"""Control two isolated ROS domains from a sourced operator PC. No synchronized clock claim."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import os
import subprocess
import sys


def call(domain,action,timeout=8):
    env=dict(os.environ,ROS_DOMAIN_ID=str(domain))
    # This PC must discover both physical robot networks.
    env.pop('ROS_AUTOMATIC_DISCOVERY_RANGE',None)
    service,kind,body=('/gp/start','std_srvs/srv/Trigger','{}') if action=='start' else (
        '/gp/stop','std_srvs/srv/SetBool','{data: true}')
    try:
        r=subprocess.run(['ros2','service','call',service,kind,body],env=env,
                         capture_output=True,text=True,timeout=timeout)
        ok=r.returncode==0 and 'success=True' in r.stdout
        return domain,ok,r.stdout+r.stderr
    except (OSError,subprocess.TimeoutExpired) as exc:
        return domain,False,str(exc)


def operate(domains,action,caller=call):
    with ThreadPoolExecutor(max_workers=2) as pool:
        results=list(pool.map(lambda d:caller(d,action),domains))
    if action=='start' and not all(r[1] for r in results):
        # A may already be moving while B rejects; request stop in both domains.
        with ThreadPoolExecutor(max_workers=2) as pool:
            results+=list(pool.map(lambda d:caller(d,'stop'),domains))
    return results


def main():
    p=argparse.ArgumentParser()
    p.add_argument('action',choices=['start','stop'])
    p.add_argument('--domains',nargs=2,type=int,default=[41,42])
    a=p.parse_args()
    if len(set(a.domains))!=2 or any(not 0<=d<=100 for d in a.domains):p.error('two distinct domains 0..100 required')
    results=operate(a.domains,a.action)
    for domain,ok,message in results:print(f'domain={domain} acknowledged={ok}\n{message}')
    return 0 if all(r[1] for r in results) else 1


if __name__=='__main__':sys.exit(main())
