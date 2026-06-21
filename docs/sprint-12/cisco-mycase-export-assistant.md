# Cisco MyCase PDF Export Assistant

## Purpose

Sprint 12.1 introduces a **local-only Playwright utility** that exports Cisco MyCase support cases to PDF using a user-authenticated browser session.

The assistant is intentionally **not integrated into VoicePilot core**. It runs on an engineer workstation with manual login, resume support, and audit logging.

## Design Principles

| Rule | Implementation |
|------|----------------|
| No stored credentials | Persistent browser profile only; no username/password handling |
| No bypass of MFA/CAPTCHA/SSO | User completes authentication manually in Chromium |
| Automation after login | Export loop starts only after user presses Enter |
| Delay between cases | Configurable `--delay` (default 5 seconds) |
| Resume support | `--resume` skips cases with existing PDFs |
| Failure tolerance | Missing export button saves HTML + screenshot and continues |
| Audit trail | `export_manifest.json` and `export.log` |

## Architecture

```text
Cisco Case List (Excel/CSV)
        │
        ▼
  parse_case_list()
        │
        ▼
Playwright persistent context (manual login)
        │
        ▼
For each case ──► open case URL ──► export PDF or save HTML/screenshot
        │
        ▼
export_manifest.json + export.log
```

## Package Layout

```text
tools/cisco_mycase_export/
  README.md
  export_cases.py
  requirements.txt
```

## Setup

```bash
cd tools/cisco_mycase_export
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

## Usage

```bash
python tools/cisco_mycase_export/export_cases.py \
  --case-list SCMCaseList.xlsx \
  --output exports/cisco_mycase \
  --delay 5 \
  --resume
```

### Manual Login Flow

1. Chromium opens with a persistent profile (`.browser_profile/` by default).
2. Cisco MyCase login page loads.
3. User signs in and completes MFA/SSO.
4. User presses Enter in the terminal.
5. Exports begin with delay between cases.

## Output

```text
exports/cisco_mycase/
  6991234567.pdf
  6991234568.html
  6991234568.png
  export_manifest.json
  export.log
```

### Manifest Format

```json
{
  "case_list": "/path/to/SCMCaseList.xlsx",
  "output_dir": "/path/to/exports/cisco_mycase",
  "entries": {
    "6991234567": {
      "case_number": "6991234567",
      "status": "success",
      "pdf_path": "exports/cisco_mycase/6991234567.pdf",
      "updated_at": "2026-06-19T12:00:00+00:00"
    }
  }
}
```

## Case List Parsing

Supported formats:

- `.csv`
- `.xlsx`

Detected columns (case-insensitive):

- `Case Number`
- `Case #`
- `SR Number`
- `Case ID`
- Any header containing `case`

## Failure Handling

When the export button is not found:

1. Save `{case_number}.html` (page HTML)
2. Save `{case_number}.png` (full-page screenshot)
3. Record `status: failed` in manifest
4. Continue to next case

## CLI Options

| Option | Default | Description |
|--------|---------|-------------|
| `--case-list` | required | Cisco exported case list |
| `--output` | `exports/cisco_mycase` | Output directory |
| `--delay` | `5` | Seconds between cases |
| `--resume` | off | Skip existing PDFs |
| `--profile-dir` | `.browser_profile` | Browser profile directory |
| `--login-url` | Cisco MyCase URL | Login page |
| `--case-url-template` | Cisco case URL template | `{case_number}` placeholder |

## Security Notes

- Do not commit browser profiles, exports, or customer case lists.
- The tool never stores passwords or bypasses access controls.
- All authentication happens through the normal Cisco MyCase web UI.

## Related Tests

- [`../../tests/test_cisco_mycase_export.py`](../../tests/test_cisco_mycase_export.py)

## Related Documentation

- [`../../tools/cisco_mycase_export/README.md`](../../tools/cisco_mycase_export/README.md)

## Future Work

This sprint does **not** integrate with VoicePilot runtime, investigation engines, or REST APIs. Future sprints may attach exported PDFs as investigation evidence.
