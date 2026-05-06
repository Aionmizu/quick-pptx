# Security policy

## Supported versions

Only the latest minor (currently `0.8.x`) receives security fixes. Older
versions are not maintained.

## Reporting a vulnerability

Use GitHub's [private security advisory](https://github.com/Aionmizu/quick-pptx/security/advisories/new)
flow to report anything that affects:

- API key storage / leakage (the `~/.config/ia-pptx/credentials.json` path,
  process-list visibility, environment leakage)
- Carte blanche execution scope (a path where Claude Code could run
  arbitrary commands the user did not explicitly authorize)
- Subprocess argument handling (`gen_image.py`, `freeform_helpers`,
  pptxgenjs / WeasyPrint invocations)
- Any path that downloads remote resources at install/run time

Do **not** open a public issue for security-relevant reports. We aim to
acknowledge within 72 hours and ship a fix within 7 days for high-severity
issues.

## Trust boundaries (what users should know)

- **Carte blanche** is opt-in (default ON in Streamlit, can be disabled).
  When enabled, Claude Code has Bash/Read/Write/Edit access in a tmp cwd.
  Users who don't want this can disable it; the tools are then narrowed to
  Read (or Read+Bash if Nano Banana is on).
- **API keys** live at `~/.config/ia-pptx/credentials.json` (mode 0600 on
  POSIX). They are loaded into the Python process and passed to subprocess
  calls. They are never logged, but they are visible via `ps aux` while a
  child process is running with them in argv (this is the API server's
  design — we don't pass keys via argv ourselves).
- **The skill bundle** runs untrusted Claude code via Node + LibreOffice
  + WeasyPrint subprocesses. None of these have network ACLs by default.
