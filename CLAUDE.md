# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Run the application
python -m app.main

# Run all tests
python -m pytest tests/

# Run a single test file
python -m pytest tests/test_api.py

# Run a single test
python -m pytest tests/test_utils.py::test_normalize_name
```

## Project Purpose

This is an **AI hackathon example repository** — a user management and reporting system intentionally seeded with bugs, performance issues, and code quality problems for AI tools to analyze and fix. There are 8 hackathon prompts in the README covering: test generation, debugging, tooling discovery, codebase explanation, PR intelligence, refactoring, performance, and edge case finding.

## Architecture

The app is a plain Python package (`app/`) with no web framework or external dependencies. All data is in-memory.

**Data flow:** `main.py` → `api.py` → services (`user_service`, `report_service`, `analytics`, `workflows`, `billing`, `notification_service`) → `utils.py`

**Key modules:**
- `models.py` — `User`, `Order`, `Notification` dataclasses (no validation)
- `user_service.py` — In-memory `FAKE_DB` with users 42–45; user lookup, summary, and search
- `report_service.py` — Metric aggregation (daily reports, percentiles, snapshots)
- `analytics.py` — Dashboard and anomaly detection
- `workflows.py` — Multi-step orchestration (`build_onboarding_packet`, `process_user_lifecycle`)
- `api.py` — 5 thin API functions that orchestrate the services
- `billing.py` — Simulated payment processing with retry logic
- `notification_service.py` — Notification dispatch (email/sms channel selection)
- `search_tools.py` — Contact recommendation utilities
- `utils.py` — Shared helpers: `normalize_name`, `retry`, `average`, `format_currency`, etc.
- `legacy_helpers.py` — Intentionally poor-quality code (`buildThing`, duplicate `normalize_metric_name`)

## Known Intentional Issues

These exist for hackathon analysis — do not "fix" them unless that is the explicit task:

**Bugs:**
- `report_service.build_daily_report()` — calls `max()` without filtering `None` values → `TypeError`
- `notification_service.pick_delivery_channel()` — missing `None` check on `user.email`
- `report_service.build_percentile_report()` — `IndexError` on empty input; off-by-one when `percentile=1.0`

**Performance:**
- `analytics.build_dashboard_data()` — calls `get_user_summary()` twice per user
- `analytics.build_hot_path()` — repeated sort and copy inside a loop

**Code quality:**
- `legacy_helpers.buildThing()` — poor naming, deep branching, mixed concerns
- `normalize_metric_name` is duplicated in both `report_service` and `legacy_helpers`
- `workflows.process_user_lifecycle()` — deeply nested, mixes validation/transformation/control flow

## Sample Data

- `sample_pr/` — Three sample PRs (two open, one merged) with metadata and diffs for PR intelligence tasks
- `logs/` — Error logs, stack traces, and CI failure output for debugging tasks
- `notes/sprint_sync.txt` — Team notes describing known pain points
