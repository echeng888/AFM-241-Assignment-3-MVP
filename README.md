# AFM 241 Assignment 3 — MVP

Corporate investment bookkeeping: statement PDFs in, draft cost-base working paper out.
Baker Tilly KDN engagement brief, Section 6.

## Run it

    python3 make_testdata.py     # regenerates the synthetic corpus
    python3 pipeline.py          # offline mode (no API key needed)
    python3 pipeline.py --live   # stages 2 and 3 call the Claude API

`--live` needs `ANTHROPIC_API_KEY` in the environment. Verify the request shape,
model name and field names against current Anthropic documentation before relying
on the live path — we implemented it but have not executed it.

## Files

| File | What it is |
|---|---|
| `make_testdata.py` | Generates the synthetic corpus. All data invented by us. |
| `pipeline.py` | The four-stage pipeline plus the scoring harness. |
| `out/statements_FY2025.pdf` | 12 monthly statement pages, 29 transactions. |
| `out/slips_FY2025.pdf` | T5 and T3 slips. T5 interest is $6.40 above the statement total, deliberately. |
| `out/ground_truth.csv` | The correct answer, used for scoring. |
| `out/working_paper_FY2025.xlsx` | The output: 5 tabs plus a run-info tab. |
| `out/score.json` | Measured results against the six criteria. |
| `run_log.txt` | Console output of the last run. |

## Data

Synthetic only. No real Baker Tilly client statement, slip or working paper was
requested, received or seen at any point in this project.

## What the offline run proves, and what it does not

Offline mode substitutes a deterministic layout parser and a keyword classifier
for the model, so stages 1 and 4 and the scoring harness can be exercised without
an API key. It demonstrates that ingestion rejects untextable pages, that both
exception gates route correctly, that every figure in the workbook is computed in
code rather than by a model, and that the variance is surfaced rather than absorbed.

It is not evidence about how well a language model reads brokerage statements,
because in offline mode no model reads them. The extraction score in particular is
inflated: the parser was written against this exact layout. The meaningful test is
a live run against a statement format the prompt was not tuned on.
