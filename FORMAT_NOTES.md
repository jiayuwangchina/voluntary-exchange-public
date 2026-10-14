# Format and verification notes

Checked on 14 October 2026.

## Official template

- Official support page: https://www.e-publications.org/ecta/support/
- Author-support repository: https://github.com/vtex-soft/texsupport.econometricsociety-ecta
- Pinned upstream commit: `959c321528527291927748d3e506e3f39024244c`
- Configuration version: 2026/01/06, v1.0.7.

The `econsocart` class replaces the obsolete `ectaart` class. Both PDFs use
the official `ecta,draft` mode; the appendix additionally uses `supplement`.
The redundant `nameyear` option in the sample is omitted because the current
class already loads author-year natbib and reports that option as unused.
The upstream class, configuration, and bibliography style are unchanged.

The template sets US Letter paper, 12-point Times body text, a six-inch text
width, and its native review spacing and marginal line numbers. No additional
`setspace` scaling or manual text-width/height changes are applied. The body
baseline is approximately 18.78 points under the official draft settings.
Sections, theorems, proofs, tables, citations, and running heads use the class
styles. The paper retains five keywords, its JEL codes, and a 99-word abstract.

Local changes provide a neutral anonymous masthead, portable aliases for three
font shapes used by the public class, bookmark handling, and unnumbered paragraph
headings below the numbered sections and subsections. These do not
modify the upstream files. The PDF author field is empty. No author, address,
email, funding, or coeditor block is included.

Theorem numbering is continuous in the main manuscript. The appendix uses a
separate continuous series prefixed `A.`. Labels are preserved. External
references are explicit text because the official class prohibits `xr` and
`xr-hyper`; `build.py` refreshes their numbers through source comments.
Bibliographies are embedded in each `.tex`, as requested by the template.

## Scope of verification

The accompanying `compilation_report.json` records the actual page counts,
resolved references, warning status, and source hashes. Formatting preservation
checks compare the scientific body and theorem/proof environments with the
previous completed-work edition, after normalizing cross-reference notation.
The latest PDFs were visually inspected, including tables, theorem pages,
appendix headings, first and last pages, and bibliography pages.

The earlier 42-page main paper and 55-page appendix become 34 and 45 pages in
this official draft layout. No proof or research section was removed to obtain
these counts. Historical audits under `verification/history/` retain their
original dates, numbering, and page claims.

The journal's current instructions page was inaccessible during this check:
https://www.econometricsociety.org/publications/econometrica/information-authors/instructions-submitting-articles

Accordingly, the release verifies conformity to the accessible official
template, not every current submission-portal rule. The main paper is below
the requested 45-page target. The complete 45-page appendix is retained;
the permissible supplement length requires confirmation on the current
journal instructions page. No claim of editorial approval or acceptance is made.
