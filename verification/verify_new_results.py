#!/usr/bin/env python3
"""Exact finite audits accompanying (not substituting for) the analytic proofs."""
from fractions import Fraction as F
from pathlib import Path
import json
import verify_revision_previous as old

checks=0
def check(c,msg):
    global checks
    checks+=1
    if not c: raise AssertionError(msg)

# Stronger primary witness and its allocation-dependent fee interval.
e=F(1,144309); tau=F(1,10000)
cost=12*e+16*tau
check(cost==F(50603,30064375),'16 approval cost')
check(F(10,11)-cost==F(27280647,30064375),'16 approval welfare')
check(cost-tau==F(152309,96206000),'fee threshold bound')
check(cost-tau<F(5,1000)<F(15,1000)<F(1,50),'fee interval')
for value,expected in [(F(9,10),F(8859,10000)),(F(10,11),F(8949,10000))]:
    check(F(99,100)*value-tau-F(1,200)==expected,'nonconstant fee optimum')

# Curved-preference allocation: global tail bound allows a finite exact audit.
rho,tau=F(36,5),F(1,20)
results=[]
for n in range(1,20):
    theta=min(F(1),F(9,8)-F(3,4*n))
    value=(F(9,10)-F(3,5*n))*theta-F(2,5)*theta**2-tau*(n+1)
    results.append((value,n,theta))
best=max(results)
check(best==(F(17,160),3,F(7,8)),'unique interior global optimum')
check(sum(v==best[0] for v,n,t in results)==1,'unique count')
check(F(1,2)-20*tau<best[0],'all later counts below best by gross planner bound')
theta=F(7,8); e=theta/36
check(e==F(7,288),'curved reserve')
q=(e,)*3; a=F(0)
curved_trace=[]
for supplier,x,y in [(1,5*e,6*e),(2,15*e,12*e),(1,9*e,12*e),(2,7*e,6*e)]:
    inc=(x,y if supplier==1 else F(0),y if supplier==2 else F(0))
    q=old.vector_add(q,old.mv(old.technology(F(0)),inc))
    benefit=x-F(2,5)*((a+x)**2-a*a)
    check(benefit>=y/10,'curved incremental participation')
    check(all(v>=0 for v in q),'curved intermediate balances')
    a+=x
    curved_trace.append({'supplier':supplier,'x':x,'y':y,'balances':q,'employee_gain':benefit-y/10})
check(a==theta and q==(e,)*3,'curved endpoint and repayment')

# Participation frontier, including both branches and threshold.
for c in [F(1,100),F(4,5),F(5,6),F(9,10),F(99,100)]:
    e=max(F(1,12),c-F(3,4)); x=max(F(5,12),c/2)
    first=(e-2*x+F(3,4),e+x-F(1,4),e+x-F(1,2))
    check(all(v>=0 for v in first),'binding participation first ledger')
    check(x>=c/2 and 1-x>=c/2,'both employees voluntarily financed')
    check(e>=F(1,12) and e>=c-F(3,4),'both analytic reserve bounds')
check(max(F(1,12),F(9,10)-F(3,4))==F(3,20),'c=.9 frontier')

# Direct planner certificate for the primitive LP in the original family.
for h in [F(1,100),F(1,8),F(1,4),F(49,100)]:
    D=2+3*h
    u1=((F(3,4)+h/2)/D,1/D,F(0))
    u2=(F(5,4)*(1+2*h)/D,F(0),(1+2*h)/D)
    p=old.mv(old.technology(h),old.vector_add(u1,u2))
    q=old.mv(old.technology(h),u1)
    k=(1-2*h)/(4*h)
    check(old.vector_add(u1,u2)==old.planner_formula(h)[0],'LP output planner endpoint')
    check(p==(F(0),F(0),h/D),'LP productive support')
    check(all(v>=-k*w for v,w in zip(q,p)),'LP prefix certificate')
    check(u1[0]>u1[1]/10 and u2[0]>u2[2]/10,'LP voluntary bundles')

# Independent exact simulation of the nonseparable release cycle.
M=((-1,1,1,1),(1,-2,-1,1),(0,1,-1,0),(0,0,1,-1))
e=F(1,10**6); q=(e,)*4; z=(F(0),)*4; amount=F(0); trace=[]
while amount<F(1,3):
    size=min(e+amount,F(1,3)-amount)
    for j in (1,2,3):
        inc=tuple(size if k in (0,j) else F(0) for k in range(4))
        z=old.vector_add(z,inc); q=old.vector_add(q,old.mv(M,inc))
        check(all(v>=0 for v in q),'cycle account feasibility')
        check(z[0]<=1 and all(v<=F(1,3) for v in z[1:]),'cycle caps')
        check(size-size/10>0,'cycle participation and balanced supplier reimbursement')
        trace.append({'supplier':j,'size':size,'balances':q,'allocation':z})
    amount+=size
check(len(trace)==57,'57 cycle approvals')
check(z==(F(1),F(1,3),F(1,3),F(1,3)),'cycle exact target')
check(tuple(v-e for v in q)==(F(0),F(1,3),F(0),F(0)),'cycle full repayment')
check(F(9,10)-58*e==F(449971,500000),'cycle productive lower bound')
check(F(201,10**6)**2<F(3,10**7),'cycle conserving upper below joint')

report={'status':'PASS','exact_checks':checks,
        'primary_16_approval_cost':cost,'primary_16_approval_net':F(10,11)-cost,
        'curved_optimum':{'net':best[0],'T':best[1]+1,'quantity':best[2]},
        'curved_trace':curved_trace,'cycle_trace':trace,
        'scope':'Finite numerical certificates; rate theorems established by analytic proofs.'}
path=Path(__file__).with_name('new_results_verification_report.json')
path.write_text(json.dumps(report,default=str,indent=2)+'\n')
print(f'PASS: {checks} exact checks; report: {path}')
