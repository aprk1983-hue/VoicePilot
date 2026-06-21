# Cisco MyCase PDF Export Assistant

Local-only Playwright helper that exports Cisco MyCase support cases to PDF using a **user-authenticated browser session**.

This utility is **not** integrated into VoicePilot core. It runs on your workstation only.

## Important Rules

- **No credentials are stored.** You log in manually in the browser.
- **No bypass of MFA, CAPTCHA, SSO, or access controls.**
- Automation starts **only after** you confirm login is complete.
- A **delay** is applied between each case export.
- **Resume** skips cases that already exported successfully.
- Success and failure are logged to a manifest and the console.

## Prerequisites

- Python 3.12+
- Access to Cisco MyCase in a supported browser profile
- An exported Cisco case list (Excel `.xlsx` or CSV)

## Setup

```bash
cd tools/cisco_mycase_export
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

## Prepare Case List

Export your case list from Cisco MyCase (for example `SCMCaseList.xlsx`). The tool detects a column named one of:

- `Case Number`
- `Case #`
- `SR Number`
- `Case ID`
- `Case`

Or any column whose header contains `case`.

## Usage

```bash
python export_cases.py \
  --case-list SCMCaseList.xlsx \
  --output exports/cisco_mycase \
  --delay 5 \
  --resume
```

From the repository root:

```bash
python tools/cisco_mycase_export/export_cases.py \
  --case-list SCMCaseList.xlsx \
  --output exports/cisco_mycase \
  --delay 5 \
  --resume
```

### What Happens

1. Chromium opens with a **persistent profile** (`.browser_profile/` by default).
2. The Cisco MyCase sign-in page loads.
3. **You sign in manually** (MFA/SSO as required).
4. Press **Enter** in the terminal when login is complete.
5. The tool visits each case, clicks **Save As PDF** (or equivalent export control), and saves output.

Closed Cisco MyCase cases commonly expose **Save As PDF** under an **Actions** or **More** menu rather than a top-level Export button. The assistant detects these labels case-insensitively:

- Save As PDF / Save as PDF
- Save PDF
- Download PDF
- Print
- Export

If the export control is hidden in a menu, the tool opens **Actions/More** first, then clicks **Save As PDF**.

### Output Layout

```text
exports/cisco_mycase/
  6991234567.pdf              # successful export
  6991234568.html             # fallback when export button not found
  6991234568.png              # screenshot for failed export
  export_manifest.json        # resume + audit log
  export.log                  # text log
```

## Options

| Flag | Default | Description |
|------|---------|-------------|
| `--case-list` | required | Path to Cisco case list Excel or CSV |
| `--output` | `exports/cisco_mycase` | Directory for PDFs and artifacts |
| `--delay` | `5` | Seconds to wait between cases |
| `--resume` | off | Skip cases already marked successful in manifest |
| `--profile-dir` | `.browser_profile` | Persistent browser profile directory |
| `--login-url` | Cisco MyCase sign-in URL | Page opened for manual login |
| `--case-url-template` | Cisco case URL template | `{case_number}` placeholder |
| `--headless` | off | Run headless (not recommended for manual login) |

## Resume

With `--resume`, cases that already have a successful PDF and manifest entry are skipped. Failed cases are retried.

## Troubleshooting

| Issue | Action |
|-------|--------|
| Login page loops | Complete MFA/SSO manually, then press Enter |
| Export control not found | Check saved `.html`, `.png`, and `export.log` for listed visible button/menu text |
| Save As PDF hidden in menu | Confirm the case page shows Actions/More; the tool opens that menu automatically |
| Excel parse error | Install `openpyxl` or export the list as CSV |
| Session expired mid-run | Re-run with `--resume` after logging in again |

## Security

- Browser profile data stays local in `--profile-dir`.
- Do not commit `.browser_profile/`, `exports/`, or case lists with customer data.
- This tool does not send credentials anywhere except through your normal browser login flow.
