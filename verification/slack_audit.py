"""Exact arithmetic audit: true-planner settlement with positive original stock.

This checks witnesses, not a substitute for the uniform analytical proof.
"""
from fractions import Fraction as Q


def planner(h,s):
    d=2+3*h
    return (Q(1),(1-8*s)/d,(1+2*h+(4+2*h)*s)/d)


def frontier(h,theta,T):
    if not h:
        return theta/(12*(T-1))
    gamma=(1+2*h)/(1-2*h)
    G=gamma**((T-1)//2) if T%2 else (1+gamma)*gamma**(T//2-1)/2
    return h*theta/(6*(G-1))


def witness(h,s,e):
    t=s+e
    assert t>0 and 0<=s<=Q(1,32)
    theta=2*(1-8*s)/(2+3*h)
    T=2
    while frontier(h,theta,T)>t:
        T+=1
    seed=frontier(h,theta,T)
    a=b1=b2=Q(0)
    history=[]
    for k in range(1,T+1):
        supplier=1 if k%2 else 2
        if h:
            S=3*seed+h*b1
            q=(b1-b2)/2
            u,v=S-q,S+q
            if k<T:
                y=u/(Q(1,2)-h) if supplier==1 else 2*v
            else:
                y=u-v if supplier==1 else v-u
            b1new=b1+y if supplier==1 else b1
            b2new=b2+y if supplier==2 else b2
            anew=(b1new+b2new-seed if supplier==1
                  else b1new/2+3*b2new/2-seed) if k<T else theta
            x=anew-a
        else:
            if k==1:
                x,y=5*seed,6*seed
            elif k==T:
                x,y=(4*seed,6*seed) if supplier==1 else (7*seed,6*seed)
            else:
                x,y=(9*seed,12*seed) if supplier==1 else (15*seed,12*seed)
        a+=x
        if supplier==1: b1+=y
        else: b2+=y
        P=t-2*a+(Q(3,2)+h)*b1+Q(5,2)*b2
        W=t+a-b1/2-3*b2/2
        H=t+a-b1-b2
        assert min(x,y,P,W,H)>=0
        assert x>=y/10
        assert max(a,b1,b2)<=1
        history.append((supplier,x,y,P,W,H))
    assert (a,b1,b2)==(theta,theta/2,theta/2)
    x=(3*h+16*s)/(2+3*h)
    y=(2*h+(12+2*h)*s)/(2+3*h)
    if x or y:
        a+=x; b2+=y
        P=t-2*a+(Q(3,2)+h)*b1+Q(5,2)*b2
        W=t+a-b1/2-3*b2/2
        H=t+a-b1-b2
        assert min(x,y,P,W,H)>=0 and x>=y/10
        history.append((2,x,y,P,W,H))
    assert (a,b1,b2)==planner(h,s)
    assert P==W==e
    assert H-e==(h+(6+h)*s)/(2+3*h)
    V=a-(b1+b2)/10
    expected=1-(1+h)/(5*(2+3*h))+(2-h)*s/(5*(2+3*h))
    assert V==expected
    return len(history),seed,V


def conserving_exact_frontier(s,T):
    """Attain the sharp reserve frontier at the true s-ledger planner."""
    r=(1-8*s)/(12*(T-1))
    e=max(r-s,Q(0))
    t=s+e
    a=b1=b2=Q(0)
    history=[]
    # Last approval must use supplier 2; parity chooses the first supplier.
    for k in range(1,T+1):
        supplier=2 if (T-k)%2==0 else 1
        oldq=(b1-b2)/2
        q=(-3*s if k==T else (3*r if supplier==1 else -3*r))
        y=2*abs(q-oldq)
        if supplier==1: b1+=y
        else: b2+=y
        P=e if k==T else Q(0)
        anew=(t+Q(3,2)*b1+Q(5,2)*b2-P)/2
        x=anew-a
        a=anew
        W=t+a-b1/2-3*b2/2
        H=t+a-b1-b2
        assert min(x,y,P,W,H)>=0 and x>=y/10
        assert max(a,b1,b2)<=1
        history.append((supplier,x,y,P,W,H))
    assert (a,b1,b2)==planner(Q(0),s)
    assert (P,W,H)==(e,e,e+3*s)
    return e,history


if __name__=='__main__':
    count=0
    for h in [Q(0),Q(1,100),Q(1,4),Q(49,100)]:
        for s in [Q(0),Q(1,10000),Q(1,2500),Q(1,100),Q(1,32)]:
            for e in [Q(0),Q(1,144309),Q(1,1000),Q(1,100)]:
                if not s+e: continue
                N,seed,V=witness(h,s,e)
                count+=1
    print(f'{count} exact-arithmetic planner witnesses verified.')
    count=0
    for s in [Q(0),Q(1,10000),Q(1,2500),Q(1,100),Q(1,32)]:
        for T in list(range(2,30))+[100,210,500,834,1000]:
            conserving_exact_frontier(s,T)
            count+=1
    print(f'{count} exact conserving positive-stock frontier witnesses verified.')
    for h in [Q(0),Q(1,4)]:
        for s in [Q(1,10000),Q(1,2500),Q(1,100),Q(1,32)]:
            N,seed,V=witness(h,s,Q(0))
            print(f'h={h}; s={s}; no borrowed reserve; T={N}; V={V}')
