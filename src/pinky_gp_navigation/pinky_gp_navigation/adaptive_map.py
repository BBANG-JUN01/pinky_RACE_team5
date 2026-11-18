"""Registered occupancy grid + expiring live hits. Grid uses metres and map XY.
Local replanning is discrete A*, with conservative circular footprint inflation.
"""
import heapq,math
class AdaptiveMap:
    def __init__(self,width,height,resolution,data,radius,origin=(0.,0.)):
        if width<=0 or height<=0 or len(data)!=width*height:raise ValueError('invalid grid')
        if not all(math.isfinite(v) for v in (resolution,radius,*origin)) or resolution<=0 or radius<=0:raise ValueError('invalid geometry')
        self.w,self.h,self.res,self.radius,self.origin=width,height,resolution,radius,origin
        self.static={(i%width,i//width) for i,v in enumerate(data) if v<0 or v>=50}
        self.live={};self.last=None
    def cell(self,xy):return (math.floor((xy[0]-self.origin[0])/self.res),math.floor((xy[1]-self.origin[1])/self.res))
    def observe(self,points,now,ttl):
        if not math.isfinite(now) or not math.isfinite(ttl) or ttl<=0:raise ValueError('invalid clock/ttl')
        if any(len(p)!=2 or not all(math.isfinite(v) for v in p) for p in points):raise ValueError('invalid points')
        if self.last is not None and now<self.last:raise ValueError('clock rollback')
        self.last=now
        for p in points:self.live[self.cell(p)]=now+ttl
    def blocked(self,now):
        if not math.isfinite(now) or (self.last is not None and now<self.last):raise ValueError('invalid clock')
        obstacles=self.static|{p for p,t in self.live.items() if t>now}
        self.live={p:t for p,t in self.live.items() if t>now}
        # Include half cell diagonal so obstacle cells are treated as areas.
        r=math.ceil(self.radius/self.res+.7072);out=set()
        for x,y in obstacles:
            for dx in range(-r,r+1):
                for dy in range(-r,r+1):
                    if math.hypot(dx,dy)*self.res<=self.radius+self.res*.7072:out.add((x+dx,y+dy))
        for x in range(self.w):
            for y in range(self.h):
                if min(x+.5,y+.5,self.w-x-.5,self.h-y-.5)*self.res<self.radius:out.add((x,y))
        return out
    def plan(self,start,goal,now):
        start,goal=self.cell(start),self.cell(goal);blocked=self.blocked(now)
        valid=lambda p:0<=p[0]<self.w and 0<=p[1]<self.h and p not in blocked
        if not valid(start) or not valid(goal):raise ValueError('blocked endpoints')
        queue=[(0,0,start)];cost={start:0};parent={}
        while queue:
            _,g,p=heapq.heappop(queue)
            if g!=cost[p]:continue
            if p==goal:
                route=[p]
                while p!=start:p=parent[p];route.append(p)
                return [(self.origin[0]+(x+.5)*self.res,self.origin[1]+(y+.5)*self.res) for x,y in reversed(route)]
            for dx,dy in [(1,0),(-1,0),(0,1),(0,-1)]:
                q=p[0]+dx,p[1]+dy
                if valid(q) and g+1<cost.get(q,math.inf):
                    cost[q]=g+1;parent[q]=p;heapq.heappush(queue,(g+1+abs(q[0]-goal[0])+abs(q[1]-goal[1]),g+1,q))
        raise ValueError('no route; stop')
