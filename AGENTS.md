# Open Food Downloader agent guide

## Scope

These instructions apply to the entire repository.

## Repository map

- `download_products.py` downloads and validates OpenFoodFacts records, writes
  category artifacts, and optionally stores products in MongoDB.
- `search_products.py` performs individual product searches.
- `search_batch.py` runs searches from `batch.txt` and produces tabular output.
- `utils.py` owns shared query formatting, scoring, and product-name helpers.
- `openai_assistant.py` contains the optional OpenAI-assisted search path.
- `.github/workflows/` contains the corresponding CI, download, and search flows.

## Working rules

1. Inspect the relevant implementation, tests, and workflow before changing a
   behavior exposed through GitHub Actions.
2. Keep changes narrowly scoped and add or update a focused regression test.
3. Preserve existing output schemas unless the task explicitly changes their
   contract.
4. Treat `.env`, `MONGO_URI`, and `OPENAI_API_KEY` as secrets. Never print,
   commit, or place their values in fixtures or generated artifacts.
5. Run live MongoDB, OpenAI, or Hugging Face operations only when the task
   requires them and the necessary credentials or network access are available.
   Otherwise use unit tests and clearly report what was not verified.
6. Treat generated JSON and CSV result files as outputs, not source files,
   unless the task explicitly targets them.

## Domain invariants

- A direct category is the last category in a product category path that is not
  a language-prefixed tag.
- Direct-category counts include only products assigned directly to that
  category. Do not roll counts up into parent categories.
- When category artifacts change, inspect together:
  `download_products.py`, its focused tests, and
  `.github/workflows/download-food-records.yml`.

## Verification

Use the repository virtual environment for focused tests:

```bash
venv/bin/python -m pytest path/to/test_file.py -q
```

For changes to shared behavior, run the complete suite:

```bash
venv/bin/python -m pytest -q
```

`make test` currently runs only `test_utils.py`; do not treat it as the complete
test suite.

A change is complete when:

- focused tests cover the changed behavior;
- the appropriate test suite passes;
- affected README or workflow contracts are updated;
- any unverified external integration is called out in the final report.

## Agent skills

### Issue tracker

Issues are tracked in GitHub Issues. See `docs/agents/issue-tracker.md`.

### Triage labels

Use the five default triage labels. See `docs/agents/triage-labels.md`.

### Domain docs

This repository uses a single-context domain layout. See
`docs/agents/domain.md`.
