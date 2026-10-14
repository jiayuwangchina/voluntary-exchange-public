#!/usr/bin/env python3
"""Exact arithmetic audit of the endogenous-allocation revision.

Python standard library only. Run:
    python verification/verify_revision.py
    python verification/verify_revision_previous.py --json /path/to/report.json

This audits finite rational examples, exhaustive polytope vertices, and
constructive schedules. It is a reproducible complement to the proofs,
not a substitute for the general theorems or a claimed global solution
of the productive sequential-allocation problem.
"""

from __future__ import annotations

import argparse
from decimal import Decimal, localcontext
from fractions import Fraction as F
from itertools import combinations
import json
from pathlib import Path


CHECKS = 0


def check(condition, description):
    global CHECKS
    CHECKS += 1
    if not condition:
        raise AssertionError(description)


def decimal(q, places=6):
    with localcontext() as context:
        context.prec = 50
        return f"{Decimal(q.numerator) / Decimal(q.denominator):.{places}f}"


def vector_add(x, y):
    return tuple(a + b for a, b in zip(x, y))


def dot(x, y):
    return sum((a * b for a, b in zip(x, y)), F(0))


def mv(matrix, vector):
    return tuple(dot(row, vector) for row in matrix)


def technology(h):
    return (
        (F(-2), F(3, 2) + h, F(5, 2)),
        (F(1), F(-1, 2), F(-3, 2)),
        (F(1), F(-1), F(-1)),
    )


def linear_solve(matrix, rhs):
    """Exact Gaussian elimination; None for a singular square system."""
    n = len(rhs)
    augmented = [[F(x) for x in row] + [F(b)]
                 for row, b in zip(matrix, rhs)]
    for col in range(n):
        pivot = next((r for r in range(col, n) if augmented[r][col]), None)
        if pivot is None:
            return None
        augmented[col], augmented[pivot] = augmented[pivot], augmented[col]
        scale = augmented[col][col]
        augmented[col] = [x / scale for x in augmented[col]]
        for row in range(n):
            if row != col:
                scale = augmented[row][col]
                augmented[row] = [a - scale * b
                                  for a, b in zip(augmented[row], augmented[col])]
    return tuple(augmented[r][-1] for r in range(n))


def feasible_vertices(h):
    """All vertices of {z in [0,1]^3: M_h z >= 0}, exactly."""
    inequalities = [(row, F(0)) for row in technology(h)]
    for j in range(3):
        unit = tuple(F(int(k == j)) for k in range(3))
        inequalities.append((unit, F(0)))
        inequalities.append((tuple(-x for x in unit), F(-1)))
    vertices = set()
    for active in combinations(inequalities, 3):
        vertex = linear_solve([a for a, _ in active], [b for _, b in active])
        if vertex is not None and all(dot(a, vertex) >= b for a, b in inequalities):
            vertices.add(vertex)
    check(bool(vertices), f"nonempty rational vertex set at h={h}")
    return vertices


def employee_surplus(z):
    return z[0] - (z[1] + z[2]) / 10


def planner_formula(h):
    d = 2 + 3 * h
    return (F(1), 1 / d, (1 + 2 * h) / d), 1 - (1 + h) / (5 * d)


def G(h, T):
    gamma = (1 + 2 * h) / (1 - 2 * h)
    n = T // 2
    return gamma**n if T % 2 else (1 + gamma) * gamma**(n - 1) / 2


def reserve_frontier(h, theta, T):
    check(T >= 2, "frontier requires at least two approvals")
    return (theta / (12 * (T - 1)) if h == 0
            else h * theta / (6 * (G(h, T) - 1)))


def optimal_fixed_target_cost(h, theta=F(1), rho=F(12), tau=F(1, 10000)):
    """Exact global discrete minimum, with a rigorous termination bound.

    Once tau*T >= incumbent, no subsequent T can improve the incumbent,
    since reserve cost is nonnegative and tau*T is increasing.
    """
    best, best_T, best_e = None, None, None
    T = 2
    while best is None or tau * T < best:
        e = reserve_frontier(h, theta, T)
        cost = rho * e + tau * T
        if best is None or cost < best:
            best, best_T, best_e = cost, T, e
        T += 1
    check(tau * T >= best, "analytic tail bound covers all later approval counts")
    return {"cost": best, "T": best_T, "reserve": best_e,
            "first_unsearched_T": T, "tail_lower_bound": tau * T}


def seventeen_steps(e):
    steps = [(1, 11 * e, 12 * e)]
    for m in range(1, 8):
        steps.append((2, 30 * 3**(m - 1) * e, 24 * 3**(m - 1) * e))
        steps.append((1, 42 * 3**(m - 1) * e, 48 * 3**(m - 1) * e))
    steps.extend([(2, 26245 * e, 26244 * e), (2, F(3, 11), F(2, 11))])
    return steps


def audit_schedule(h, e, steps, expected_target):
    matrix = technology(h)
    z, q = (F(0),) * 3, (e,) * 3
    trace = []
    for t, (supplier, x, y) in enumerate(steps, 1):
        check(supplier in (1, 2), f"valid supplier at step {t}")
        check(x > 0 and y > 0, f"irreversible positive bilateral increments at step {t}")
        increment = (x, y if supplier == 1 else F(0),
                     y if supplier == 2 else F(0))
        z = vector_add(z, increment)
        q = vector_add(q, mv(matrix, increment))
        check(all(v >= 0 for v in q), f"all account balances nonnegative at step {t}")
        check(all(0 <= v <= 1 for v in z), f"all activity caps respected at step {t}")
        payment = y / 10
        supplier_transfer, demander_transfer = payment, -payment
        check(supplier_transfer + demander_transfer == 0,
              f"exact budget balance at step {t}")
        check(supplier_transfer - y / 10 == 0, f"supplier participation at step {t}")
        check(x + demander_transfer > 0, f"strict demander participation at step {t}")
        trace.append({"t": t, "supplier": supplier, "x": x, "y": y,
                      "allocation": z, "balances": q,
                      "payment": payment, "demander_gain": x - payment})
    check(z == expected_target, "schedule reaches the exact target")
    returned = tuple(v - e for v in q)
    check(all(v >= 0 for v in returned), "full reserve is repayable")
    check(returned == mv(matrix, expected_target), "repayment leaves the original-ledger balances")
    # Along an approval, ledger balances are affine; verified endpoints
    # imply feasibility at every interpolation point, without a mesh test.
    return trace, returned


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", type=Path,
                        default=Path(__file__).with_name("revision_verification_report.json"))
    args = parser.parse_args()
    report = {"arithmetic": "fractions.Fraction throughout; decimals for display only",
              "scope": "Exact finite checks supplement, and do not replace, the analytic proofs."}

    # Independent LP certificate: exhaustive rational vertices plus the
    # supplier-cost dual identity, rather than merely substituting formulas.
    planner_cases = []
    for h in [F(0), F(1, 100), F(1, 8), F(1, 4), F(49, 100), F(499, 1000)]:
        z, value = planner_formula(h)
        vertices = feasible_vertices(h)
        best = max(employee_surplus(v) for v in vertices)
        maximizers = {v for v in vertices if employee_surplus(v) == best}
        check(best == value and maximizers == {z}, f"unique planner optimum at h={h}")
        check(mv(technology(h), z) == (F(0), F(0), h / (2 + 3 * h)),
              f"planner residual balances at h={h}")
        alpha, beta = 2 / (2 + 3 * h), 2 * (1 - h) / (2 + 3 * h)
        check(alpha > 0 and beta > 0, f"strictly positive dual weights at h={h}")
        check(alpha * (F(3, 2) + h) - beta / 2 == 1,
              f"supplier-1 dual cost coefficient at h={h}")
        check(alpha * F(5, 2) - beta * F(3, 2) == 1,
              f"supplier-2 dual cost coefficient at h={h}")
        check(2 * alpha - beta == 2 * (1 + h) / (2 + 3 * h),
              f"dual lower bound right side at h={h}")
        for a in [F(0), F(1, 7), F(2, 3), F(1)]:
            scaled = tuple(a * v for v in z)
            check(all(v >= 0 for v in mv(technology(h), scaled)),
                  f"cost-minimizing suppliers feasible for a={a}, h={h}")
            check((scaled[1] + scaled[2]) / 10 == (1 + h) * a / (5 * (2 + 3 * h)),
                  f"supplier-cost formula at a={a}, h={h}")
        check(value - F(9, 10) == h / (10 * (2 + 3 * h)),
              f"fixed-target welfare shortfall at h={h}")
        planner_cases.append({"h": h, "optimum": z, "value": value,
                              "vertices_enumerated": len(vertices)})
    report["planner_cases"] = planner_cases

    h, theta, e = F(1, 4), F(8, 11), F(1, 144309)
    check(G(h, 16) == 4374, "G_16(1/4)=4374")
    check(reserve_frontier(h, theta, 16) == e, "exact first-stage reserve is 1/144309")
    z_star, productive_value = planner_formula(h)
    check(z_star == (F(1), F(4, 11), F(6, 11)), "productive planner quantities")
    check(productive_value == F(10, 11), "productive planner value")
    check(productive_value - F(9, 10) == F(1, 110), "fixed-target welfare loss at h=1/4")
    steps = seventeen_steps(e)
    check(len(steps) == 17, "original witness has seventeen listed approvals")
    trace, returned = audit_schedule(h, e, steps, z_star)
    check(trace[15]["allocation"] == (theta, theta / 2, theta / 2),
          "first sixteen approvals reach the proportional target")
    check(trace[15]["balances"] == (e + F(1, 11), e, e),
          "first stage releases exactly 1/11 pension capacity")
    check(mv(technology(h), (F(3, 11), F(0), F(2, 11)))
          == (F(-1, 11), F(0), F(1, 11)), "completion consumes pension release")
    check(returned == (F(0), F(0), F(1, 11)), "final residual balances")
    report["seventeen_step_witness"] = {"reserve": e, "trace": trace,
                                         "balances_after_repayment": returned}

    # Adjacent approvals 16 and 17 have the same pair. Their merger is
    # feasible by convexity here, but neither witness is claimed optimal.
    merged = steps[:15] + [(2, steps[15][1] + steps[16][1], steps[15][2] + steps[16][2])]
    check(len(merged) == 16, "merged witness has sixteen approvals")
    merged_trace, _ = audit_schedule(h, e, merged, z_star)

    rho, tau, joint_cost = F(12), F(1, 10000), F(101, 10000)
    cost17 = rho * e + 17 * tau
    net17 = productive_value - cost17
    joint_productive = productive_value - joint_cost
    check(cost17 == F(857751, 481030000), "17-approval cost fraction")
    check(net17 == F(436442249, 481030000), "17-approval net fraction")
    check(joint_productive == F(98889, 110000), "productive joint optimum fraction")
    check(net17 - joint_productive == F(1000163, 120257500), "productive strict comparison margin")
    check(net17 > joint_productive, "sequential witness beats globally optimized joint value")
    check(decimal(net17) == "0.907308" and decimal(joint_productive) == "0.898991",
          "six-place display values")
    check(F("0.907307") < net17 < F("0.907308"),
          "rounded 0.907308 must not be presented as a literal exact lower bound")

    conserving = optimal_fixed_target_cost(F(0))
    fixed_productive = optimal_fixed_target_cost(h)
    check((conserving["T"], conserving["reserve"], conserving["cost"])
          == (101, F(1, 1200), F(201, 10000)), "conserving global discrete cost minimum")
    check((fixed_productive["T"], fixed_productive["reserve"], fixed_productive["cost"])
          == (16, F(1, 104952), F(9371, 5466250)), "productive fixed-target global discrete cost minimum")
    check(F(9, 10) - joint_cost == F(8899, 10000), "conserving joint value")
    check(F(9, 10) - conserving["cost"] == F(8799, 10000), "conserving sequential value")
    check(conserving["cost"] > joint_cost > fixed_productive["cost"], "fixed-target cost reversal")
    report["fixed_target_global_cost_minima"] = {"conserving": conserving,
                                                  "productive": fixed_productive}
    report["institutional_values"] = {
        "conserving_joint_exact": F(8899, 10000),
        "conserving_sequential_exact": F(8799, 10000),
        "productive_joint_exact": joint_productive,
        "productive_sequential_17_approval_lower_bound_exact": net17,
        "productive_sequential_17_approval_bound_rounded_display": decimal(net17),
        "rounding_note": "The exact-fraction inequality is valid; 0.907308 is an approximation, not an exact lower bound.",
        "productive_merged_16_approval_lower_bound_exact": net17 + tau,
        "productive_merged_16_approval_bound_rounded_display": decimal(net17 + tau),
        "productive_sequential_global_optimum": "Not claimed or computed"}

    # Valued-public-balance extension: independent vertex maximization.
    public_cases = []
    productive_vertices = feasible_vertices(h)
    fixed = (F(1), F(1, 2), F(1, 2))
    for lam in [F(0), F(1, 100), F(4, 55), F(1, 10), F(1), F(100)]:
        def public_value(z):
            return employee_surplus(z) + lam * mv(technology(h), z)[0]
        best = max(map(public_value, productive_vertices))
        expected = max(F(10, 11), F(9, 10) + lam / 8)
        check(best == expected, f"valued-balance planner value at lambda={lam}")
        maximizers = {v for v in productive_vertices if public_value(v) == best}
        expected_maximizers = ({z_star} if lam < F(4, 55) else
                               {fixed} if lam > F(4, 55) else {z_star, fixed})
        check(maximizers == expected_maximizers, f"valued-balance planner maximizers at lambda={lam}")
        witness_cost = cost17 if lam <= F(4, 55) else fixed_productive["cost"]
        check(best - witness_cost > best - joint_cost > 0,
              f"valued-balance institutional comparison at lambda={lam}")
        public_cases.append({"lambda": lam, "social_value": best,
                             "maximizing_vertices": sorted(maximizers)})
    check(F(9, 10) + F(1, 10) / 8 == F(73, 80), "lambda=.1 social value")
    check(F(73, 80) - joint_cost == F(564, 625), "lambda=.1 joint net value")
    valued_witness = F(73, 80) - fixed_productive["cost"]
    check(valued_witness == F(39828657, 43730000), "lambda=.1 sequential bound")
    check(decimal(valued_witness) == "0.910786", "lambda=.1 rounded sequential bound")
    report["valued_public_balance_cases"] = public_cases

    # Exact grid cycle and finite-budget inversion in the conserving family.
    grid_cases = []
    for delta in [F(1, 2), F(1, 10), F(1, 24), F(1, 100)]:
        units = int(F(1) / (2 * delta))
        theta_grid = 2 * delta * units
        grid_steps = [(supplier, delta, delta)
                      for _ in range(units) for supplier in (1, 2)]
        _, grid_returned = audit_schedule(F(0), delta / 2, grid_steps,
                                          (theta_grid, theta_grid / 2, theta_grid / 2))
        check(grid_returned == (F(0),) * 3, "grid-cycle reserve is fully returned")
        check(len(grid_steps) == theta_grid / delta, "grid-cycle approval count")
        check(0 <= F(9, 10) * (1 - theta_grid) < F(9, 5) * delta,
              "grid welfare-loss bound")
        grid_cases.append({"delta": delta, "reserve": delta / 2,
                           "theta": theta_grid, "approvals": len(grid_steps)})
    for delta in [F(3, 20), F(7, 100), F(3, 100)]:
        theta_grid = 2 * delta * int(F(1) / (2 * delta))
        check(0 < 1 - theta_grid < 2 * delta, "nonaligned planner-target rounding loss")
        check(F(9, 10) * (1 - theta_grid) < F(9, 5) * delta,
              "nonaligned grid welfare-loss bound")
    for N in [2, 5, 17, 101]:
        for e_cap in [F(1, 10000), F(1, 1200), F(1, 12)]:
            max_theta = min(F(1), 12 * e_cap * (N - 1))
            check(reserve_frontier(F(0), max_theta, N) <= e_cap,
                  "finite-cap maximizing quantity is attainable")
            if max_theta < 1:
                check(reserve_frontier(F(0), max_theta, N) == e_cap,
                      "finite-cap quantity exactly exhausts frontier")
    report["grid_cycle_cases"] = grid_cases
    report["status"] = "PASS"
    report["exact_checks"] = CHECKS

    def encode(value):
        if isinstance(value, F):
            return str(value)
        raise TypeError(type(value).__name__)

    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(json.dumps(report, default=encode, indent=2) + "\n", encoding="utf-8")
    print(f"PASS: {CHECKS} exact checks; Python standard library only.")
    print("Planner: six rational technologies, dual cost certificates, exhaustive feasible vertices.")
    print("Schedule: G16=4374; reserve=1/144309; all 17 approvals and full repayment verified.")
    print("Costs: conserving global fixed-target minimum T=101; productive T=16; analytic tail bounds.")
    print(f"Productive sequential witness >= {net17} (approximately {decimal(net17)}).")
    print(f"Merged 16-approval witness >= {net17 + tau} (approximately {decimal(net17 + tau)}).")
    print("Extensions: valued-public-balance vertex comparisons and discrete grid cycles verified.")
    print(f"JSON report: {args.json}")


if __name__ == "__main__":
    main()
