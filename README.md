# The Cost of Voluntary Exchange

## Allocation and Settlement under Separate Public Accounts

Anonymous manuscript and reproducibility materials, prepared using the official
Econometrica `econsocart` submission template.

**Read:** [Main manuscript](Anonymous_Main_Manuscript.pdf) ·
[Online appendix](Anonymous_Online_Appendix.pdf) ·
[中文上传说明](UPLOAD_GUIDE_ZH.md)

The informed authority chooses an allocation and an admissible voluntary
settlement schedule. The paper studies how separate public accounts, productive
resource releases, original capacity, and implementation costs determine the
preferred settlement institution. The water application reports conditional
allocation benchmarks; it does not estimate the welfare effect of joint
settlement or identify productive amplification.

## Contents

| File or directory | Purpose |
| --- | --- |
| `Paper_1_Main_Manuscript.tex` / `Anonymous_Main_Manuscript.pdf` | Anonymous main paper, 34 pages including references |
| `Paper_1_Online_Appendix.tex` / `Anonymous_Online_Appendix.pdf` | Complete proofs and extensions, 45 pages |
| `build.py` | Build both PDFs and refresh all numbered references |
| `compilation_report.json` | Page counts, reference checks, and build status |
| `FORMAT_NOTES.md` | Verified template settings and scope of format checks |
| `data/` | Published water application data, 391 eligible requests |
| `empirical/` | Queue replication, schedules, simulations, and source checks |
| `verification/` | Exact mathematical audits and selected independent LP checks |
| `source_audit/` | Official report URLs and hashes |
| `econsocart.cls`, `econsocart.cfg`, `econsoc.bst` | Unmodified official author-support files |

Author names, affiliations, contact details, acknowledgments, and PDF author
metadata are omitted. Editorial replies, cover letters, earlier manuscripts,
and prospective research designs are excluded from this release. Bibliographic
authors and third-party software attribution are retained.

## Build the paper

Install Python 3 and a reasonably complete TeX Live or MiKTeX distribution,
including `pdflatex`, `microtype`, `mathtools`, `booktabs`, `enumitem`, `needspace`,
`longtable`, `tabularx`, `hyperref`, `bookmark`, `xurl`, and the standard Times
fonts. Install Poppler so that `pdfinfo` is available on the command line.

From the repository root:

```bash
python3 build.py
```

On Windows, use `python build.py` if Python is installed under `python`.
The script runs LaTeX until the two documents' references stabilize and records
the result in `compilation_report.json`. Each `.tex` includes its bibliography
and compiles as a self-contained document. Keep the three official style files
next to the sources. No BibTeX run is needed for the supplied bibliography.

The official class excludes `xr` and `xr-hyper`. References to the other document
are explicit numbers followed by `%<xref:label>` or `%<xeqref:label>` comments.
`build.py` refreshes these numbers from the newly compiled labels. Retain these
comments and run the script after editing either document. Cross-document
references are plain text; internal references remain linked.

## Reproduce the water application

The tested environment uses Python 3.12, NumPy 2.3.5, and SciPy 1.17.0.
NumPy is needed for the water replay; SciPy is needed only for the optional LP
audit. The manuscript build and exact-rational theory checks use the Python
standard library.

```bash
python3 -m pip install -r requirements.txt
python3 empirical/replicate_water_queue.py --out replication-output
```

The default run uses 100,000 permutations and seed 20251015. It reproduces
October counts of 98, 106, and 159 under recorded, arrival, and smallest-first
ordering. Calculations use integer tenths of a megalitre. The 159 count is the
capacity-only maximum for the fixed submitted menu, conditional on the other
account requirements. It is not an estimate of welfare or a unique allocation.

To repeat the official PDF-to-CSV comparison, download the two reports listed
in `source_audit/source_manifest.json` into a directory, naming them
`October_2025.pdf` and `December_2025.pdf`. Install Poppler's `pdftotext`, then run:

```bash
python3 empirical/verify_official_pdf_rows.py --source-dir /path/to/reports
```

The official report PDFs are not bundled. Existing audit results document
3,143 comparisons with no mismatches. Historical mathematical and data audits
are distinct from this release's typography and reference checks.

## Reproduce mathematical checks

```bash
python3 verification/verify_revision_previous.py
python3 verification/verify_new_results.py
python3 verification/slack_audit.py
python3 verification/verify_fixed_grid_robustness.py
python3 verification/independent_slack_lp.py
```

The last command is optional and uses SciPy. The checks supplement the analytic
proofs and do not replace them. Reports under `verification/history/` describe
earlier manuscript builds, so their page counts do not describe this edition.

## Upload and rights

Upload the **contents** of this folder to a GitHub repository. No repository has
been created or published by this package. For author anonymity during review,
remember that a public personal GitHub repository displays its owner's account.

See [RIGHTS.md](RIGHTS.md) for the distinction between original research,
third-party templates, and administrative data. No new open-source or
Creative Commons license has been assigned to the original research materials.
