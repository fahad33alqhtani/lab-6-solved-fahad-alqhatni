# Raqib Fraud Detection Service — Lab 6 Starter (SDA-AIE-113)

## What this is

This is the **starting point for Lab 6** — "Config, Secrets & Logging"
(the final lab of the course). It already contains a **complete, working
Lab 1 through Lab 5 solution**: the FastAPI service, the Docker/compose
setup, the full three-level pytest suite, AND a green CI/CD pipeline
(`.github/workflows/ci.yml`) with the architecture contract
(`import-linter`) enforced.

If you finished Lab 5 yourself with a working result, keep using your
own repo instead of this one. This starter exists so nobody falls behind
— everyone begins Lab 6 from the same known-good, CI-green baseline.

## What already works (Lab 1 through Lab 5, done for you)

```
src/fraud_service/                  # domain/service/adapters/api — all implemented
                                     # passes `mypy src/fraud_service --strict` cleanly
Dockerfile, docker-compose.yml, requirements.lock, scripts/startup_time.sh
payloads/malformed/                 # 40-file malformed-payload corpus
payloads/sample.json                # used by the CI image-smoke job
tests/
├── conftest.py                       # ConstantModel, client_factory, real_model, sample_txn
├── unit/test_policies.py             # 6-case tightened decision-band test
├── integration/test_predict_api.py   # contract + malformed corpus + no-stack-trace + readiness
└── behavioural/test_model_behaviour.py  # invariance + directional + 5,000-row golden file
scripts/regen_golden.py             # regenerates the golden file — a deliberate, reviewed step only
.github/workflows/ci.yml            # lint → test → image-smoke → publish, all green
pyproject.toml                      # [tool.importlinter] layered-architecture contract, enforced in CI
BENCHMARKS.md                       # Day 1 + Lab 3 + Lab 4 numbers already filled in
```

```
$ ruff check src tests && python -m mypy src/fraud_service --strict && lint-imports
All checks passed!
Success: no issues found in 15 source files
Contracts: 1 kept, 0 broken.

$ pytest -m "not slow" --cov-fail-under=80
52 passed in ~2s (fast suite, ~99% branch coverage)

$ pytest -m behavioural -q --no-cov
3 passed in ~6s (behavioural suite, real model, golden file)
```

**Note on the CI workflow:** the "Behavioural gate" step deliberately
runs `pytest -m behavioural -q --no-cov`, not `-m "behavioural and not
slow"`. Every behavioural test is marked `slow`, so filtering on `not
slow` would always select zero tests and fail on the coverage gate for
the wrong reason. If you see that pattern anywhere else in your own
workflow files, that's the bug to look for.

## What you build today (Lab 6)

```
src/fraud_service/config.py         # upgrade — SecretStr, field_validator, extra="forbid"
src/fraud_service/logging_setup.py  # NEW — structlog JSON logs, contextvars trace_id, secret masking
src/fraud_service/api/app.py        # wire the trace/timing middleware into structured logging
INCIDENT.md                         # NEW — your secret-leak drill write-up
```

Full step-by-step instructions, expected results, and a troubleshooting
table are in the Day 3 Lab Guide (Lab 6 section) — work through it in
order; this README is just the starting-point map.

## Quick start

```
pip install -e ".[dev,api]"
make test                        # 52 fast tests, all green
pytest -m behavioural -q --no-cov   # 3 behavioural tests, all green
ruff check src tests && python -m mypy src/fraud_service --strict && lint-imports
make up && make smoke            # Docker stack, from Lab 3
```

## Pushing this to your own GitHub repo

Carried over from Lab 5 — if you haven't already:

```
git init   # if not already a repo (this starter already is one)
gh repo create fraud-service --private --source=. --push
# or create an empty repo on github.com and:
git remote add origin <your-repo-url>
git push -u origin main
```

Once pushed, check the **Actions** tab — all four jobs (lint, test,
image-smoke, publish) should go green on `main`.
