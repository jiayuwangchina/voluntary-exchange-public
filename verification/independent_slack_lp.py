import numpy as np
from scipy.optimize import linprog
from itertools import product
M=np.array([[-2,1.5,2.5],[1,-.5,-1.5],[1,-1,-1.]])

def opt(word,s,rho=12,target=None):
    T=len(word); n=2*T+1
    effects=[]
    for k,j in enumerate(word):
        E=np.zeros((3,n)); E[:,2*k]=M[:,0]
        if j: E[:,2*k+1]=M[:,j]
        effects.append(E)
    Aub=[];bub=[];cum=np.zeros((3,n))
    for E in effects:
        cum+=E
        A=-cum.copy(); A[:,-1]=-1
        Aub.extend(A);bub.extend([s]*3)
    Aub.extend(-cum);bub.extend([s]*3)
    activity=np.zeros((3,n))
    for k,j in enumerate(word):
        activity[0,2*k]=1
        if j: activity[j,2*k+1]=1
        a=np.zeros(n); a[2*k]=-1;a[2*k+1]=.1
        Aub.append(a);bub.append(0)
    Aub.extend(activity);bub.extend([1]*3)
    c=-(activity[0]-.1*(activity[1]+activity[2]));c[-1]=rho
    bounds=[(0,None)]*n
    for k,j in enumerate(word):
        if not j: bounds[2*k+1]=(0,0)
    kwargs={}
    if target is not None:
        c=np.zeros(n);c[-1]=1
        kwargs.update(A_eq=activity,b_eq=target)
    sol=linprog(c,A_ub=Aub,b_ub=bub,bounds=bounds,method='highs',**kwargs)
    return sol.fun if sol.success else np.inf

checked=0
for s in [0,.0004,.02,.03125]:
    for T in range(1,6):
        val=min(opt(w,s) for w in product(range(3),repeat=T))
        if T==1: pred=7.4*s
        else:
            n=T-1
            a=1 if 12<=10.8*n else min(1,(12*n+8)*s)
            pred=.9*a+.2*s-12*max(0,(a-8*s)/(12*n)-s)
            pred=max(pred,7.4*s,0)
        assert abs(-val-pred)<1e-7,(s,T,-val,pred)
        checked+=1
        if T>=2:
            target=[1,.5-4*s,.5+2*s]
            res=min(opt(w,s,target=target) for w in product(range(3),repeat=T))
            pred=max(0,(1-8*s)/(12*(T-1))-s)
            assert abs(res-pred)<1e-7,(s,T,res,pred)
            checked+=1
print('Independent all-word LP checks passed:',checked)

from fractions import Fraction as Q
sJ=Q(1,1208);sS=Q(9901,11960000); joint=Q(101,10000)
def costs(s,n): return max(Q(0),(1-8*s)/n-12*s)+Q(n+1,10000)
for s,sign in [(Q(0),1),(sJ-Q(1,10**9),1),(sJ,0),((sJ+sS)/2,0),(sS,0),(sS+Q(1,10**9),-1),(Q(1,32),-1)]:
    pairs=[(costs(s,n),n) for n in range(2,1000)]
    cost,n=min(pairs)
    dif=cost-joint
    assert (dif>0)-(dif<0)==sign,(s,n,cost,sign)
    print('s=',s,'cost=',cost,'n=',n,'sign=',sign)
