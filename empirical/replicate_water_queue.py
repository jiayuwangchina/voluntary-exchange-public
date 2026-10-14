#!/usr/bin/env python3
"""Reproduce October 2025 water-queue cardinality comparisons.

All capacity comparisons use exact integer tenths of megalitres (0.1 ML
units), inferred from the supplied decimal data.  NumPy is used only to draw
permutations and describe their finite simulation distribution.  No estimated
treatment effect, welfare weight, or causal p value is produced.

Run from any directory:
    python replicate_water_queue.py --data ../data/water_randomized_applications_391.csv
"""

from __future__ import annotations

import argparse
import collections
import csv
import hashlib
import json
from decimal import Decimal
from fractions import Fraction
from pathlib import Path

import numpy as np


def exact_units(value: str, scale: int) -> int:
    x = Decimal(value) * scale
    if x != x.to_integral_value():
        raise ValueError(f"Cannot represent {value} at scale {scale}")
    return int(x)


def ml_string(units: int, scale: int) -> str:
    places = len(str(scale)) - 1
    return f"{Decimal(units) / scale:.{places}f}"


def execute(indices, volumes, capacity):
    remaining = capacity
    accepted = []
    for i in indices:
        if volumes[i] <= remaining:
            accepted.append(int(i))
            remaining -= volumes[i]
    return accepted, remaining


def write_csv(path, rows, fieldnames):
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    base = Path(__file__).resolve().parent
    parser.add_argument("--data", type=Path,
                        default=base.parent / "data" / "water_randomized_applications_391.csv")
    parser.add_argument("--out", type=Path, default=base)
    parser.add_argument("--draws", type=int, default=100_000)
    parser.add_argument("--seed", type=int, default=20251015)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    if args.draws <= 0:
        raise ValueError("draws must be positive")

    raw = args.data.read_bytes()
    with args.data.open(newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    decimal_fields = ["volume_ML", "opportunity_before_ML", "opportunity_after_ML"]
    places = max(max(0, -Decimal(r[k]).as_tuple().exponent)
                 for r in rows for k in decimal_fields)
    scale = 10 ** places
    assert all(exact_units(r["volume_ML"], scale) > 0 for r in rows)

    report = {
        "input_file": args.data.name,
        "input_sha256": hashlib.sha256(raw).hexdigest(),
        "sample_rows": len(rows),
        "capacity_integer_scale_per_ML": scale,
        "events": {},
        "interpretation": {
            "objective": "Number of whole applications executed, with unit weight per application.",
            "counterfactual_scope": "Fixed October applications, fixed volumes, fixed corridor capacity, and unchanged eligibility; balances and strategic resubmission under changed order are unobserved.",
            "not_identified": "Welfare, surplus, prices as valuations, causal institutional effects, the main paper's productive-release mechanism, or the difference between joint and optimally chosen sequential settlement.",
            "random_benchmark": "Uniform random permutations are a transparent stipulated conditional benchmark; no causal p value or claim that the observed draw is the expected random outcome.",
            "joint_comparison": "The cardinality maximum is attainable by a sequential order; joint and optimized sequential choice have the same cardinality value in this one-capacity problem.",
        },
    }

    for date in sorted({r["event_date"] for r in rows}):
        sample = sorted([r for r in rows if r["event_date"] == date],
                        key=lambda r: int(r["random_priority"]))
        priorities = [int(r["random_priority"]) for r in sample]
        assert priorities == list(range(1, len(sample) + 1))
        transition_shocks = []
        mismatch = []
        for j, r in enumerate(sample):
            before = exact_units(r["opportunity_before_ML"], scale)
            after = exact_units(r["opportunity_after_ML"], scale)
            volume = exact_units(r["volume_ML"], scale)
            expected_after = before - (volume if r["status"] == "Approved" else 0)
            if expected_after != after:
                mismatch.append({"priority": j + 1, "reported_after": r["opportunity_after_ML"],
                                 "expected_after": ml_string(expected_after, scale)})
            if j:
                previous = exact_units(sample[j - 1]["opportunity_after_ML"], scale)
                if previous != before:
                    transition_shocks.append({"before_priority": j + 1,
                                              "change_ML": ml_string(before - previous, scale)})
        missing = {k: sum(not r[k] for r in sample) for k in sample[0]}
        duplicates = {}
        for key in ["random_priority", "arrival_order", "source_row_id"]:
            counts = collections.Counter(r[key] for r in sample if r[key])
            duplicates[key] = {k: v for k, v in counts.items() if v > 1}
        approved_volume = sum(exact_units(r["volume_ML"], scale) for r in sample
                              if r["status"] == "Approved")
        total_volume = sum(exact_units(r["volume_ML"], scale) for r in sample)
        account_refusals = [{k: r[k] for k in ["random_priority", "volume_ML", "status",
                            "opportunity_before_ML", "opportunity_after_ML", "status_footnote",
                            "source_physical_page", "source_printed_page", "source_url"]}
                           for r in sample if r["insufficient_seller_balance_reported"].lower() == "true"]
        report["events"][date] = {
            "n": len(sample), "processing_dates": sorted({r["processing_date"] for r in sample}),
            "status_counts": dict(collections.Counter(r["status"] for r in sample)),
            "total_requested_volume_ML": ml_string(total_volume, scale),
            "approved_volume_ML": ml_string(approved_volume, scale),
            "initial_capacity_ML": sample[0]["opportunity_before_ML"],
            "terminal_capacity_ML": sample[-1]["opportunity_after_ML"],
            "missing_fields": missing, "duplicate_nonempty_identifiers": duplicates,
            "row_balance_mismatches": mismatch, "between_row_capacity_changes": transition_shocks,
            "reason_counts": dict(collections.Counter(r["reason_for_trade"] for r in sample)),
            "zero_declared_price_count": sum(Decimal(r["price_AUD_per_ML"]) == 0 for r in sample),
            "positive_declared_price_count": sum(Decimal(r["price_AUD_per_ML"]) > 0 for r in sample),
            "seller_balance_refusals": account_refusals,
        }
        assert not mismatch
        assert all(not v for v in duplicates.values())

    # The report documents a 6.2 ML tagged trade between December priorities
    # 70 and 71, and seller-balance refusal at priority 45. These are not
    # inferred behavioral counterfactuals: this is a reconstruction of the
    # actual dated administrative ledger, holding the recorded eligibility
    # decision fixed. October has no within-queue external adjustment.
    ledger_rows = []
    for date in ["2025-10-15", "2025-12-15"]:
        sample = sorted([r for r in rows if r["event_date"] == date],
                        key=lambda r: int(r["random_priority"]))
        remaining = exact_units(sample[0]["opportunity_before_ML"], scale)
        matches = 0
        for r in sample:
            priority = int(r["random_priority"])
            external_change = -exact_units("6.2", scale) if date == "2025-12-15" and priority == 71 else 0
            remaining += external_change
            before = remaining
            assert before == exact_units(r["opportunity_before_ML"], scale)
            eligible = r["insufficient_seller_balance_reported"].lower() != "true"
            approved = eligible and exact_units(r["volume_ML"], scale) <= before
            assert approved == (r["status"] == "Approved")
            if approved:
                remaining -= exact_units(r["volume_ML"], scale)
            assert remaining == exact_units(r["opportunity_after_ML"], scale)
            matches += 1
            ledger_rows.append({"event_date": date, "random_priority": priority,
                                "external_change_before_row_ML": ml_string(external_change, scale),
                                "capacity_before_ML": ml_string(before, scale),
                                "volume_ML": r["volume_ML"],
                                "seller_balance_eligibility_held_fixed": int(eligible),
                                "predicted_approved": int(approved), "recorded_status": r["status"],
                                "capacity_after_ML": ml_string(remaining, scale), "exact_match": 1})
        report["events"][date]["exact_full_ledger_replay_matches"] = matches
        report["events"][date]["replay_method"] = "Capacity recurrence plus recorded seller-balance refusal, with the reported December tagged trade at its actual location; this is ledger verification, not a December counterfactual."
    write_csv(args.out / "all_391_ledger_reconciliation.csv", ledger_rows, list(ledger_rows[0]))

    oct_rows = sorted([r for r in rows if r["event_date"] == "2025-10-15"],
                      key=lambda r: int(r["random_priority"]))
    n = len(oct_rows)
    volumes = [exact_units(r["volume_ML"], scale) for r in oct_rows]
    capacity = exact_units(oct_rows[0]["opportunity_before_ML"], scale)
    assert not report["events"]["2025-10-15"]["between_row_capacity_changes"]
    orderings = {
        "recorded_random_priority": list(range(n)),
        "arrival_order": sorted(range(n), key=lambda i: Decimal(oct_rows[i]["arrival_order"])),
        "smallest_volume_first": sorted(range(n), key=lambda i: (volumes[i], i)),
    }
    accepted_sets = {}
    schedule_summary = {}
    selection_rows = []
    for name, order in orderings.items():
        selected, residual = execute(order, volumes, capacity)
        accepted_sets[name] = set(selected)
        volume = capacity - residual
        schedule_summary[name] = {
            "approved_count": len(selected), "approved_volume_ML": ml_string(volume, scale),
            "residual_capacity_ML": ml_string(residual, scale),
            "mean_approved_volume_ML": float(Fraction(volume, scale * len(selected))),
            "capacity_utilization": float(Fraction(volume, capacity)),
            "related_party_approved_count": sum(oct_rows[i]["reason_for_trade"] == "Related party trade" for i in selected),
            "zero_declared_price_approved_count": sum(Decimal(oct_rows[i]["price_AUD_per_ML"]) == 0 for i in selected),
            "tie_break": "Recorded random priority, when requested volumes are equal." if name == "smallest_volume_first" else "Not needed; ordering variable is unique.",
        }
        remaining = capacity
        for rank, i in enumerate(order, 1):
            before = remaining
            approved = int(i in accepted_sets[name])
            if approved:
                remaining -= volumes[i]
            selection_rows.append({"schedule": name, "schedule_rank": rank,
                                   "source_row_id": oct_rows[i]["source_row_id"],
                                   "recorded_random_priority": i + 1,
                                   "arrival_order": int(Decimal(oct_rows[i]["arrival_order"])),
                                   "volume_ML": ml_string(volumes[i], scale),
                                   "approved": approved,
                                   "capacity_before_ML": ml_string(before, scale),
                                   "capacity_after_ML": ml_string(remaining, scale)})
    observed_status_set = {i for i, r in enumerate(oct_rows) if r["status"] == "Approved"}
    assert accepted_sets["recorded_random_priority"] == observed_status_set
    for name, expected in [("recorded_random_priority", (98, "31209.8", "5.3")),
                           ("arrival_order", (106, "31206.4", "8.7")),
                           ("smallest_volume_first", (159, "31193.0", "22.1"))]:
        result = schedule_summary[name]
        assert (result["approved_count"], result["approved_volume_ML"], result["residual_capacity_ML"]) == expected
    k_star = len(accepted_sets["smallest_volume_first"])
    ordered_volumes = sorted(volumes)
    sum_k = sum(ordered_volumes[:k_star])
    sum_next = sum(ordered_volumes[:k_star + 1])
    assert sum_k <= capacity < sum_next
    report["october_schedules"] = schedule_summary
    report["cardinality_certificate"] = {
        "maximum_feasible_count": k_star,
        "sum_smallest_k_ML": ml_string(sum_k, scale),
        "sum_smallest_k_plus_one_ML": ml_string(sum_next, scale),
        "capacity_ML": ml_string(capacity, scale),
        "cutoff_volume_ML": ml_string(ordered_volumes[k_star - 1], scale),
        "number_at_cutoff_volume": ordered_volumes.count(ordered_volumes[k_star - 1]),
        "unique_optimal_order": False,
        "argument": "Every subset of k+1 applications uses at least the sum of the k+1 smallest volumes. That sum exceeds capacity, while the k-smallest subset fits. Ordering that subset first attains k sequentially. Equal 500 ML applications make the optimizer nonunique.",
    }
    comparison = {}
    recorded = accepted_sets["recorded_random_priority"]
    for name in ["arrival_order", "smallest_volume_first"]:
        chosen = accepted_sets[name]
        comparison[name] = {
            "common_approved_count": len(chosen & recorded),
            "newly_approved_count": len(chosen - recorded),
            "formerly_approved_not_selected_count": len(recorded - chosen),
            "net_count_difference": len(chosen) - len(recorded),
        }
    report["comparison_to_recorded_order"] = comparison
    report["participation_gap"] = {
        "count": k_star - len(recorded),
        "fraction_of_cardinality_maximum": str(Fraction(k_star - len(recorded), k_star)),
        "percent_of_cardinality_maximum": 100 * (k_star - len(recorded)) / k_star,
        "fraction_increase_over_observed": str(Fraction(k_star - len(recorded), len(recorded))),
        "percent_increase_over_observed": 100 * (k_star - len(recorded)) / len(recorded),
        "volume_change_ML": ml_string(sum(volumes[i] for i in accepted_sets["smallest_volume_first"]) - sum(volumes[i] for i in recorded), scale),
    }

    rng = np.random.Generator(np.random.PCG64(args.seed))
    counts = np.empty(args.draws, dtype=np.int16)
    used = np.empty(args.draws, dtype=np.int64)
    for draw in range(args.draws):
        chosen, residual = execute(rng.permutation(n), volumes, capacity)
        counts[draw] = len(chosen)
        used[draw] = capacity - residual
    # Quantiles are empirical inverse-CDF order statistics, not interpolations.
    probs = [0, .025, .25, .5, .75, .975, 1]
    count_quantiles = np.quantile(counts, probs, method="inverted_cdf")
    volume_quantiles = np.quantile(used, probs, method="inverted_cdf")
    report["uniform_permutation_benchmark"] = {
        "draws": args.draws, "seed": args.seed, "generator": "NumPy PCG64",
        "numpy_version": np.__version__,
        "mean_approved_count": float(counts.mean()),
        "standard_deviation_approved_count": float(counts.std(ddof=1)),
        "monte_carlo_standard_error_of_mean_count": float(counts.std(ddof=1) / np.sqrt(args.draws)),
        "count_quantiles": {str(p): int(q) for p, q in zip(probs, count_quantiles)},
        "mean_approved_volume_ML": float(used.mean() / scale),
        "volume_quantiles_ML": {str(p): ml_string(int(q), scale) for p, q in zip(probs, volume_quantiles)},
        "mean_cardinality_gap_to_159": float(k_star - counts.mean()),
        "description": "Simulation distribution conditional on the fixed October application set and capacity, under uniformly random permutations. It is not a sampling distribution for a causal estimator.",
    }
    hist = collections.Counter(map(int, counts))
    write_csv(args.out / "permutation_count_distribution.csv",
              [{"approved_count": k, "draw_frequency": hist[k], "draw_share": hist[k] / args.draws}
               for k in sorted(hist)], ["approved_count", "draw_frequency", "draw_share"])
    np.savez_compressed(args.out / "permutation_draws.npz", approved_counts=counts,
                        approved_volume_units=used, scale=np.array(scale),
                        seed=np.array(args.seed))
    write_csv(args.out / "october_counterfactual_schedules.csv", selection_rows,
              list(selection_rows[0]))
    membership_rows = []
    for i, row in enumerate(oct_rows):
        new = {k: row[k] for k in ["source_row_id", "random_priority", "arrival_order", "volume_ML",
                                  "status", "reason_for_trade", "price_AUD_per_ML", "source_url"]}
        new.update({f"approved_{name}": int(i in chosen) for name, chosen in accepted_sets.items()})
        membership_rows.append(new)
    write_csv(args.out / "october_application_selection.csv", membership_rows,
              list(membership_rows[0]))
    (args.out / "queue_replication_results.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: report[k] for k in ["october_schedules", "cardinality_certificate",
                                            "comparison_to_recorded_order", "participation_gap",
                                            "uniform_permutation_benchmark"]}, indent=2))


if __name__ == "__main__":
    main()
