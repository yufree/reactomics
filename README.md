# Reactomics

A self-updating textbook-style webpage for **PMD (Paired Mass Distance)-based reactomics** — the study of chemical reactions in biological and environmental systems using mass spectrometry data.

## What this is

The site auto-collects new papers monthly from PubMed and uses an LLM to curate the most textbook-worthy updates. The main page (`index.html`) is a static, readable introduction to reactomics; the monthly updates section surfaces field-shaping developments as they are published.

The concept is introduced in [Reactomics: using mass spectrometry as a chemical reaction detector](https://doi.org/10.1038/s42004-020-00403-z) (Communications Chemistry, 2020) and implemented in the [`pmd` R package](https://cran.r-project.org/package=pmd).

## Repository structure

```
reactomics.md            main textbook content (source of truth)
index.html               rendered HTML (generated)
reactomics.html          rendered HTML (generated)
updates/YYYY-MM.html     monthly archive pages (generated)
data/
  source_queries.json    PubMed search queries
  papers.json            raw monthly fetch output (gitignored)
  selected-updates.json  LLM-curated monthly selection
  monthly-updates.json   cumulative history
scripts/
  fetch_monthly_papers.py   fetch papers from PubMed
  select_monthly_updates.py score and LLM-curate candidates
  update_site.py            write updates into reactomics.md
  render_site.py            render markdown to HTML
.github/workflows/
  monthly-update.yml        GitHub Actions cron workflow
```

## Running locally

```bash
pip install -r requirements.txt

# Fetch papers for a specific month (omit TARGET_MONTH for previous month)
TARGET_MONTH=2026-03 python scripts/fetch_monthly_papers.py

# Score and select (set LLM_API_KEY + LLM_MODEL for LLM curation)
python scripts/select_monthly_updates.py

# Update markdown and archive
python scripts/update_site.py

# Render HTML
python scripts/render_site.py
```

## GitHub Actions setup

The workflow runs automatically on the 3rd of each month. To enable LLM curation, add these secrets/variables to the repository:

| Name | Where | Description |
|------|-------|-------------|
| `LLM_API_KEY` | Secret | API key for your LLM provider |
| `LLM_MODEL` | Secret | Model name, e.g. `claude-sonnet-4-6` or `gpt-4o` |
| `LLM_BASE_URL` | Variable | Base URL (default: `https://api.openai.com/v1`; for Claude use `https://api.anthropic.com/v1`) |

The workflow also supports manual dispatch with an optional `target_month` (YYYY-MM) to rebuild any past month.

## Hosting

Push to GitHub and enable GitHub Pages from the repository root to host the site at `https://<user>.github.io/<repo>/`.
