Water queue replication
=======================

Input and scope
---------------
The input file ../data/water_randomized_applications_391.csv contains 391
published eligible applications: 203 from the 15 October 2025 application
window, processed on 16 October; and 188 from 15 December, processed on
16 December. The official report URLs, hashes, and extraction audit are provided in the
source_audit folder in the enclosing package. Download the report PDFs
separately to rerun the independent primary-source comparison. The reports exclude applications
that failed the initial eligibility screen. The October screen excluded two
of 205 submissions; their arrival identifiers are GTM0118 and GTM0164.

Run
---
Python 3 and NumPy are required. The checked run used NumPy 2.3.5.
From any directory:

  python /path/to/empirical/replicate_water_queue.py

Optional arguments: --data PATH --out DIRECTORY --draws 100000 --seed 20251015.
The default input path is resolved relative to the script, not the working
directory. No Internet request or proprietary solver is required. The source
CSV is never modified. All capacity decisions use exact integers in 0.1 ML
units, derived from the decimal precision of the data; floating point is used
only for descriptive ratios and permutation-distribution summaries.

Exact results
-------------
October capacity is 31,215.1 ML. Recorded random priority executes 98
applications using 31,209.8 ML. Arrival order executes 106 using 31,206.4 ML.
Smallest volume first executes 159 using 31,193.0 ML. Residual capacities are
5.3, 8.7 and 22.1 ML respectively. The largest possible application count is
159: the 159 smallest requests sum to 31,193.0 ML, whereas the 160 smallest sum
to 31,693.0 ML, above capacity. The order is not unique. There are 23 requests
of 500 ML at the selection cutoff; ties are resolved by recorded random
priority for the reported application-level comparisons.

The difference is 61 approvals, 38.3647799% of the cardinality maximum and a
62.2448980% increase relative to recorded approvals. It is a net reallocation:
79 recorded approvals remain, 19 are displaced and 80 previously refused
applications are selected. The cardinality-maximizing schedule uses 16.8 ML
less than the recorded order, a 0.05383% reduction. Both exhaust more than
99.9% of corridor capacity. Mean approved request volume falls from 318.4673
ML to 196.1824 ML. Maximizing cardinality favors small applications.

All 391 recorded row balances reconcile exactly. October's 203 statuses
coincide with the one-capacity recurrence without any intervening capacity
adjustment. December additionally requires the documented 6.2 ML tagged trade
between priorities 70 and 71 and the priority-45 refusal of a 62.3 ML request
for insufficient seller balance. That request faced 23,824.0 ML of corridor
capacity. The December reconstruction holds that recorded eligibility
classification fixed; it does not infer outcomes under a different queue.

Conditional random-permutation benchmark
----------------------------------------
For 100,000 uniformly random permutations of the fixed October applications,
seed 20251015, PCG64, the mean approval count is 93.66423, the median is 94 and
the standard deviation is 9.39806. The empirical central 95% range is 75 to
112. The Monte Carlo standard error of the simulated mean is 0.02972. The
recorded count of 98 is ordinary relative to this distribution. Uniform
permutations are the stipulated simulation benchmark. These are not causal
p values, confidence intervals for a treatment effect, or proof of the exact
probabilistic law used by the administrative randomization tool.

Interpretation
--------------
The counterfactual holds submissions, requested volumes, eligibility and
corridor capacity fixed. It measures application cardinality under alternative
orders. Seller account histories, related applications, strategic splitting,
private valuations and compensation schedules are not observed. October has
191 related-party requests and 174 zero declared prices among 203 records;
reported prices are not sufficient to identify willingness to pay or surplus.
The comparison does not estimate welfare or a productive-release multiplier.
The cardinality maximum is itself achieved by sequential processing, so this
one-capacity example has the same cardinality optimum under joint selection
and optimized sequential selection. The main paper's optimized institutional
comparison and the conditional queue comparison answer different questions.

The December seller balance refusal documents a distinct private feasibility
constraint. It is not itself evidence of a separate public account, a public
balance release or a welfare-improving transaction blocked solely by ordering.

Output files
------------
queue_replication_results.json: exact audit, counterfactual results and
  descriptive permutation benchmark, including the input SHA-256 hash.
all_391_ledger_reconciliation.csv: exact row-by-row reconstruction for both
  application windows, including the December external capacity adjustment.
october_counterfactual_schedules.csv: each complete queue, status and balance.
october_application_selection.csv: aligned application-level selections,
  source identifiers, declared prices and reasons for trade.
permutation_count_distribution.csv: all simulated count frequencies.
permutation_draws.npz: every draw's approval count and exact total volume,
  along with the integer scale and seed.
run_summary.txt: console output from the checked default run.

Independent comparison with official PDFs
----------------------------------------
Download both reports using source_audit/source_manifest.json, retaining the
original filenames or renaming them October_2025.pdf and December_2025.pdf.
Then run:

  python empirical/verify_official_pdf_rows.py --source-dir /path/to/reports --data data/water_randomized_applications_391.csv

This optional audit requires pdftotext (Poppler) and Python's standard
library. It compares all 391 application rows across 3,143 fields; the
checked source versions produced zero mismatches. Report PDFs are not
redistributed in this package. The ordinary queue replication runs offline
from the included CSV without these PDFs.
