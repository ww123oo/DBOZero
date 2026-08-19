# Repository Guidelines

## Tips

Answer questions in Chinese.

## Agent Safety Workflow

- Use `tmp/` (gitignored) as the scratch root for any experimental or generated file work.
- At the start of a task, create a purpose-named subdirectory under `tmp/` and keep intermediate files inside it.
- Unless the user explicitly asks for direct source modification, do not edit the tracked source tree first. Build and verify inside `tmp/<task>/`, then ask before merging.
- Merging into tracked source always requires explicit user confirmation.

## Current Workflow

This workspace builds a copy-only DBO Zero Chinese patch from `src_file/DBOZero`.
Never write to the live game directory.
The only allowed live-directory read is an explicit `dboc refresh` or `dboc update`.

## CLI

- Canonical user docs: root `README.md`
- Translation rules: `docs/translation-rules.md`
- Dev docs: `docs/development.md`
- Install: `pip install -e .` only (editable; workspace root = repo root)

Key commands:

- `dboc update` — checkpoint → refresh source → scan → translate new → build both
- `dboc status` — compare source snapshot vs live game
- `dboc refresh` — checkpoint + refresh required source assets
- `dboc scan` — refresh queues from `src_file/DBOZero`
- `dboc build` — build simplified + traditional outputs
- `dboc config` — show/write game dir in `dboc.toml` (gitignored)

## Source And Output Boundaries

- `src_file/DBOZero/` — source snapshot, **not tracked**; never commit game assets
- `dboc.toml` — local config, **not tracked**
- `output/`, `output_taiwan/`, `release/` — generated, **not tracked**
- `hanhua_v3/runtime/` — actively maintained patch modules
- `legacy/` — archived only; do not restart old workflows unless asked
- `reports/internal/` — generated discovery tables; keep out of daily editing

## Taiwan Traditional Preferences (this fork)

When adjusting `TAIWAN_SIMPLIFY_FIXUPS` in `hanhua_v3/runtime/taiwan_fixups.py` (single source; imported by install_hanhua):

- Prefer **登錄** (not 登入) for login
- Prefer **帳號 / 帳戶** (not 賬號 / 賬戶)
- Prefer Taiwan UI vocabulary: 伺服器、訊息、視窗、預設、設定、軟體…

Format: `("正確台灣用字", "簡體原文")`. Longer phrases before shorter ones.

## Validation

```powershell
python -m compileall -q build_output.py hanhua_v3
pytest
dboc status
dboc build
```

## Code Style

Python 3 + standard library unless a dependency is clearly needed.
Tests in `tests/` with pytest.
Keep changes scoped to the v3 workflow unless the user asks for legacy recovery.
