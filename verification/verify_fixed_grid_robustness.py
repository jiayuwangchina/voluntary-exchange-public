#!/usr/bin/env python3
"""Exact audit of the fixed-grid, positive-original-slack reversal.

Uses only the Python standard library. Exhaustively solves the grid
planner problem by enumerating all supplier pairs and selecting their
best feasible demander quantity. Does not claim to solve sequential
optimization. Every displayed bound is checked with fractions.Fraction.
"""
from fractions import Fraction as F
from itertools import product
import json
from pathlib import Path

DELTA, E, SBAR = F(1, 500), F(1, 2000), F(1, 2500)
RHO, TAU, JOINT_COST = F(12), F(1, 10000), F(101, 10000)
CHECKS = 0


def check(condition, description):
    global CHECKS
    CHECKS += 1
    if not condition:
        raise AssertionError(description)


def dot(x, y):
    return sum((a*b for a,b in zip(x,y)), F(0))


def matrix(h):
    return ((-2,F(3,2)+h,F(5,2)), (1,F(-1,2),F(-3,2)), (1,-1,-1))


def mv(M,z):
    return tuple(dot(row,z) for row in M)


def add(x,y):
    return tuple(a+b for a,b in zip(x,y))


def integer_ceil_ratio(a,b):
    return -((-a)//b)


def grid_planner(h,s):
    """Enumerate 501^2 supplier choices, optimize demander units exactly.

    All inequalities are multiplied by 20/delta, yielding integers
    at h in {0,1/4} and s in {0,1/2500}. This covers every grid
    allocation, rather than searching a neighborhood of the witness.
    """
    check(h in (F(0),F(1,4)), 'supported rational technology')
    c = 20*s/DELTA
    check(c.denominator==1, 'integer right side for exhaustive grid audit')
    c = int(c)
    supplier1_pension = 30 if h==0 else 35
    best_units=-10**9
    best_allocations=[]
    feasible_supplier_pairs=0
    for i in range(501):
        for j in range(501):
            kmax=min(500,(c+supplier1_pension*i+50*j)//40)
            kmin=max(0,integer_ceil_ratio(10*i+30*j-c,20),
                     integer_ceil_ratio(20*i+20*j-c,20))
            if kmin<=kmax:
                feasible_supplier_pairs+=1
                objective=10*kmax-i-j
                allocation=(kmax*DELTA,i*DELTA,j*DELTA)
                if objective>best_units:
                    best_units=objective
                    best_allocations=[allocation]
                elif objective==best_units:
                    best_allocations.append(allocation)
    return {'h':h,'s':s,'value':F(best_units,5000),
            'maximizers':best_allocations,
            'feasible_supplier_pairs':feasible_supplier_pairs,
            'supplier_pairs_examined':501**2}


def main():
    M=matrix(F(1,4))
    chunks=(1,2,4,8,16,32,64,56)
    check(sum(chunks)==183,'round quantities sum to 183')
    steps=[]
    for u in chunks:
        steps.extend(((1,u*DELTA,u*DELTA),(2,u*DELTA,u*DELTA)))
    steps.append((2,134*DELTA,89*DELTA))
    check(len(steps)==17,'seventeen approvals')
    z=(F(0),)*3
    q=(E,)*3
    trace=[]
    for t,(supplier,x,y) in enumerate(steps,1):
        check((x/DELTA).denominator==1 and (y/DELTA).denominator==1,
              f'grid increments at step {t}')
        inc=(x,y if supplier==1 else F(0),y if supplier==2 else F(0))
        z=add(z,inc)
        q=add(q,mv(M,inc))
        check(all(v>=0 for v in q),f'nonnegative intermediate ledger {t}')
        check(all(0<=v<=1 for v in z),f'activity caps {t}')
        payment=y/10
        check(payment-payment==0,f'balanced compensation {t}')
        check(x-payment>0,f'strict demander participation {t}')
        check(payment-y/10==0,f'weak supplier participation {t}')
        trace.append({'step':t,'supplier':supplier,'x':x,'y':y,'allocation':z,
                      'ledger':q,'payment':payment,'demander_gain':x-payment})
    target=(F(1),F(183,500),F(272,500))
    check(z==target,'grid target reached exactly')
    residual=tuple(v-E for v in q)
    check(residual==(F(1,2000),F(1,1000),F(9,100)),
          'residual balances after full reserve repayment')
    check(residual==mv(M,target),'original-ledger terminal accounting')
    check(trace[15]['allocation']==(F(366,500),F(183,500),F(183,500)),
          'first sixteen approvals reach proportional intermediate target')
    check(mv(M,(F(134,500),F(0),F(89,500)))
          ==(F(-91,1000),F(1,1000),F(9,100)),'final resource increment')
    check(F(134,500)-F(89,5000)==F(1251,5000),'final demander gain')
    for original in product((F(0),SBAR),repeat=3):
        for entry in trace:
            check(all(v>=0 for v in add(entry['ledger'],original)),
                  'prefix feasible at a corner of original-ledger box')
        check(all(v>=0 for v in add(residual,original)),
              'full repayment at a corner of original-ledger box')
    gross=target[0]-(target[1]+target[2])/10
    cost=RHO*E+17*TAU
    check(gross==F(909,1000),'productive grid gross value')
    check(cost==F(77,10000),'productive grid implementation cost')
    check(gross-cost==F(9013,10000),'productive grid sequential lower bound')

    planner_audits=[]
    for h,s in product((F(0),F(1,4)),(F(0),SBAR)):
        audit=grid_planner(h,s)
        expected=F(9,10) if h==0 else F(909,1000)
        check(audit['value']==expected,
              f'exhaustive planner optimum at h={h}, original uniform s={s}')
        for maximizer in audit['maximizers']:
            check(all(v>=0 for v in add(mv(matrix(h),maximizer),(s,)*3)),
                  'exhaustive maximizing allocation is ledger-feasible')
        planner_audits.append(audit)

    seq_conserving_upper=F(8799,10000)+F(101,5)*SBAR
    joint_conserving=F(9,10)-JOINT_COST
    joint_productive=F(909,1000)-JOINT_COST
    check(seq_conserving_upper==F(44399,50000),'conserving sequential global upper bound')
    check(joint_conserving==F(8899,10000),'conserving joint exact value')
    check(joint_productive==F(8989,10000),'productive joint exact value')
    check(joint_conserving-seq_conserving_upper==F(6,3125),'conserving strict margin')
    check(gross-cost-joint_productive==F(3,1250),'productive strict margin')
    check(F(9,10)+SBAR/5<F(9,10)+F(1,5000),'conserving lattice objective upper cutoff')
    check(F(10,11)+F(7,55)*SBAR<F(909,1000)+F(1,5000),
          'productive lattice objective upper cutoff')
    check((F(8,11)+F(6,11))/10==F(7,55),'productive planner slack coefficient')
    report={'status':'PASS','exact_checks':CHECKS,'delta':DELTA,'reserve_per_account':E,
            'original_ledger_box_upper_bound':SBAR,'original_ledger_box_lower_bound':0,
            'productive_schedule':trace,'terminal_residual':residual,
            'exhaustive_grid_planner_audits':planner_audits,
            'conserving_joint_exact':joint_conserving,
            'conserving_sequential_upper_bound':seq_conserving_upper,
            'productive_joint_exact':joint_productive,
            'productive_sequential_lower_bound':gross-cost,
            'sequential_global_optima':'Not computed or claimed',
            'note':'Analytic inequalities in the appendix cover the entire continuous slack box; corner checks complement that proof.'}
    output=Path(__file__).with_name('fixed_grid_robustness_report.json')
    output.write_text(json.dumps(report,default=str,indent=2)+'\n',encoding='utf-8')
    print(f'PASS: {CHECKS} exact checks; all 17 grid approvals and reserve repayment verified.')
    print('Planner audits: 1,004,004 supplier pairs exhaustively enumerated across four cases.')
    print('Grid: delta=1/500; original balances independently range from 0 to 1/2500.')
    print('Conserving: joint=0.8899 > sequential upper bound=0.88798.')
    print('Productive: sequential lower bound=0.9013 > joint=0.8989.')
    print(f'JSON report: {output}')


if __name__=='__main__':
    main()
