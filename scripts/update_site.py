#!/usr/bin/env python3

import datetime as dt
import json
import os
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
UPDATES_DIR = ROOT / "updates"
MARKDOWN_FILE = ROOT / "reactomics.md"
MARKDOWN_FILE_ZH = ROOT / "reactomics_zh.md"
SELECTION_FILE = DATA_DIR / "selected-updates.json"
HISTORY_FILE = DATA_DIR / "monthly-updates.json"

SECTION_ORDER_ZH = {
    "Paired mass distance and chemical reactions": "配对质量距离与化学反应",
    "PMD network": "PMD网络",
    "Methods and tools": "方法与工具",
    "In-source reactions and independent ion selection": "源内反应与独立峰选择",
    "Applications in drug metabolism": "药物代谢应用",
    "Applications in environmental transformation": "环境转化应用",
    "Applications in endogenous metabolomics": "内源性代谢组学应用",
}

UPDATES_START = "<!-- MONTHLY_UPDATES_START -->"
UPDATES_END = "<!-- MONTHLY_UPDATES_END -->"
ARCHIVE_START = "<!-- MONTHLY_ARCHIVE_START -->"
ARCHIVE_END = "<!-- MONTHLY_ARCHIVE_END -->"
COLLECTION_START = "<!-- COLLECTION_START -->"
COLLECTION_END = "<!-- COLLECTION_END -->"
COLLECTION_FILE = DATA_DIR / "collection.json"


def load_json(path):
    if not path.exists():
        raise FileNotFoundError(f"Required file not found: {path}")
    return json.loads(path.read_text())


def save_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")


def validate_selection(data):
    required = ["month", "generated_at", "mode"]
    missing = [k for k in required if k not in data]
    if missing:
        raise ValueError(f"Selection file missing required keys: {missing}")
    if not isinstance(data.get("updates", []), list):
        raise ValueError("Selection 'updates' must be a list")
    if not isinstance(data.get("review_queue", []), list):
        raise ValueError("Selection 'review_queue' must be a list")
    return data


def render_latest_block(month_entry):
    month = month_entry["month"]
    lines = [f"### {month}", ""]
    updates = month_entry.get("updates", [])
    if updates:
        lines.append("**Highlights:**")
        lines.append("")
        for update in updates:
            lines.append(
                f"- **[{update['title']}]({update['url']})** — {update['summary']}"
            )
        lines.append("")
    papers = month_entry.get("papers", [])
    if papers:
        for paper in papers:
            doi = paper.get("doi", "")
            url = f"https://doi.org/{doi}" if doi else paper.get("url", "")
            journal = paper.get("journal", "")
            date = paper.get("published_date", "")[:7]
            journal_date = f" *{journal}*" if journal else ""
            journal_date += f" ({date})" if date else ""
            lines.append(f"- [{paper['title']}]({url}){journal_date}")
    else:
        lines.append("No papers found for this month.")
    lines.append("")
    return "\n".join(lines).strip()


def render_archive_block(history):
    if not history:
        return "- No monthly archives yet."
    lines = []
    for entry in sorted(history, key=lambda item: item["month"], reverse=True):
        html_path = f"updates/{entry['month']}.html"
        count = len(entry.get("papers", []))
        suffix = f"{count} paper{'s' if count != 1 else ''}"
        if count == 0:
            suffix = "no papers found"
        lines.append(f"- [{entry['month']}]({html_path}) — {suffix}")
    return "\n".join(lines)


SECTION_ORDER = [
    "Paired mass distance and chemical reactions",
    "PMD network",
    "Methods and tools",
    "In-source reactions and independent ion selection",
    "Applications in drug metabolism",
    "Applications in environmental transformation",
    "Applications in endogenous metabolomics",
]


def render_collection_block():
    if not COLLECTION_FILE.exists():
        return "Collection not yet built. Run `python scripts/build_collection.py` to populate."
    data = json.loads(COLLECTION_FILE.read_text())
    papers = data.get("papers", [])
    if not papers:
        return "No papers in collection yet."

    by_section: dict[str, list] = {s: [] for s in SECTION_ORDER}
    other: list = []
    for paper in papers:
        section = paper.get("section", "")
        if section in by_section:
            by_section[section].append(paper)
        else:
            other.append(paper)

    lines = []
    for section in SECTION_ORDER:
        group = by_section[section]
        if not group:
            continue
        lines.append(f"### {section}")
        lines.append("")
        for paper in sorted(group, key=lambda p: p.get("published_date") or "", reverse=True):
            doi = paper.get("doi", "")
            url = f"https://doi.org/{doi}" if doi else paper.get("url", "")
            journal = paper.get("journal", "")
            year = paper.get("year", "")
            meta = ""
            if journal and year:
                meta = f" *{journal}* ({year})"
            elif journal:
                meta = f" *{journal}*"
            elif year:
                meta = f" ({year})"
            annotation = paper.get("annotation", "")
            note = f" — {annotation}" if annotation else ""
            lines.append(f"- [{paper['title']}]({url}){meta}{note}")
        lines.append("")

    if other:
        lines.append("### Other")
        lines.append("")
        for paper in other:
            doi = paper.get("doi", "")
            url = f"https://doi.org/{doi}" if doi else paper.get("url", "")
            annotation = paper.get("annotation", "")
            note = f" — {annotation}" if annotation else ""
            lines.append(f"- [{paper['title']}]({url}){note}")
        lines.append("")

    total = data.get("total", len(papers))
    generated = data.get("generated_at", "")[:10]
    lines.append(f"*{total} papers total. Last updated {generated}.*")
    return "\n".join(lines).strip()


def render_latest_block_zh(month_entry):
    month = month_entry["month"]
    lines = [f"### {month}", ""]
    papers = month_entry.get("papers", [])
    if papers:
        for paper in papers:
            doi = paper.get("doi", "")
            url = f"https://doi.org/{doi}" if doi else paper.get("url", "")
            journal = paper.get("journal", "")
            date = paper.get("published_date", "")[:7]
            journal_date = f" *{journal}*" if journal else ""
            journal_date += f" （{date}）" if date else ""
            lines.append(f"- [{paper['title']}]({url}){journal_date}")
    else:
        lines.append("本月未发现相关论文。")
    lines.append("")
    return "\n".join(lines).strip()


def render_archive_block_zh(history):
    if not history:
        return "- 暂无月度存档。"
    lines = []
    for entry in sorted(history, key=lambda item: item["month"], reverse=True):
        html_path = f"updates/{entry['month']}.html"
        count = len(entry.get("papers", []))
        suffix = f"{count} 篇论文" if count > 0 else "未发现论文"
        lines.append(f"- [{entry['month']}]({html_path}) — {suffix}")
    return "\n".join(lines)


def render_collection_block_zh():
    if not COLLECTION_FILE.exists():
        return "文献集尚未构建。请运行 `python scripts/build_collection.py` 以填充。"
    data = json.loads(COLLECTION_FILE.read_text())
    papers = data.get("papers", [])
    if not papers:
        return "文献集中暂无论文。"

    by_section: dict[str, list] = {s: [] for s in SECTION_ORDER}
    other: list = []
    for paper in papers:
        section = paper.get("section", "")
        if section in by_section:
            by_section[section].append(paper)
        else:
            other.append(paper)

    lines = []
    for section in SECTION_ORDER:
        group = by_section[section]
        if not group:
            continue
        zh_heading = SECTION_ORDER_ZH.get(section, section)
        lines.append(f"### {zh_heading}")
        lines.append("")
        for paper in sorted(group, key=lambda p: p.get("published_date") or "", reverse=True):
            doi = paper.get("doi", "")
            url = f"https://doi.org/{doi}" if doi else paper.get("url", "")
            journal = paper.get("journal", "")
            year = paper.get("year", "")
            meta = ""
            if journal and year:
                meta = f" *{journal}* ({year})"
            elif journal:
                meta = f" *{journal}*"
            elif year:
                meta = f" ({year})"
            annotation = paper.get("annotation", "")
            note = f" — {annotation}" if annotation else ""
            lines.append(f"- [{paper['title']}]({url}){meta}{note}")
        lines.append("")

    if other:
        lines.append("### 其他")
        lines.append("")
        for paper in other:
            doi = paper.get("doi", "")
            url = f"https://doi.org/{doi}" if doi else paper.get("url", "")
            annotation = paper.get("annotation", "")
            note = f" — {annotation}" if annotation else ""
            lines.append(f"- [{paper['title']}]({url}){note}")
        lines.append("")

    total = data.get("total", len(papers))
    generated = data.get("generated_at", "")[:10]
    lines.append(f"*共 {total} 篇论文。最后更新：{generated}。*")
    return "\n".join(lines).strip()


def replace_marker_block(text, start_marker, end_marker, replacement):
    pattern = re.compile(
        re.escape(start_marker) + r".*?" + re.escape(end_marker), re.S
    )
    block = f"{start_marker}\n{replacement}\n{end_marker}"
    if pattern.search(text):
        return pattern.sub(block, text)
    raise ValueError(f"Missing marker block: {start_marker} ... {end_marker}")


def write_month_archive(entry):
    month = entry["month"]
    updates = entry.get("updates", [])
    papers = entry.get("papers", [])
    lines = [f"# {month} reactomics literature collection", ""]
    lines.append(
        "This page is machine-generated from the monthly PubMed scan for reactomics "
        "and PMD-based analysis publications."
    )
    lines.append("")
    if updates:
        lines.append("## Highlights")
        lines.append("")
        for update in updates:
            lines.extend(
                [
                    f"### [{update['title']}]({update['url']})",
                    "",
                    update["summary"],
                    "",
                    f"**Why it matters:** {update['why_it_matters']}",
                    "",
                    f"**Suggested section:** {update['section']}",
                    "",
                ]
            )
    if papers:
        lines.append("## All papers")
        lines.append("")
        for paper in papers:
            doi = paper.get("doi", "")
            url = f"https://doi.org/{doi}" if doi else paper.get("url", "")
            journal = paper.get("journal", "")
            date = paper.get("published_date", "")[:7]
            journal_date = f" *{journal}*" if journal else ""
            journal_date += f" ({date})" if date else ""
            lines.append(f"- [{paper['title']}]({url}){journal_date}")
        lines.append("")
    else:
        lines.append("No papers found for this month.")
        lines.append("")
    UPDATES_DIR.mkdir(parents=True, exist_ok=True)
    archive_path = UPDATES_DIR / f"{month}.md"
    archive_path.write_text("\n".join(lines).rstrip() + "\n")


def main():
    selection = validate_selection(load_json(SELECTION_FILE))

    if HISTORY_FILE.exists():
        history = load_json(HISTORY_FILE)
    else:
        print("  History file not found, creating new one", file=sys.stderr)
        history = {"history": []}

    existing = {entry["month"]: entry for entry in history.get("history", [])}

    month_entry = {
        "month": selection["month"],
        "generated_at": selection["generated_at"],
        "mode": selection["mode"],
        "updates": selection.get("updates", []),
        "papers": selection.get("papers", []),
    }
    existing[month_entry["month"]] = month_entry
    new_history = {"history": [existing[key] for key in sorted(existing.keys())]}
    save_json(HISTORY_FILE, new_history)
    write_month_archive(month_entry)

    if not MARKDOWN_FILE.exists():
        raise FileNotFoundError(f"Main markdown file not found: {MARKDOWN_FILE}")

    markdown = MARKDOWN_FILE.read_text()
    markdown = replace_marker_block(
        markdown, UPDATES_START, UPDATES_END, render_latest_block(month_entry)
    )
    markdown = replace_marker_block(
        markdown, COLLECTION_START, COLLECTION_END, render_collection_block()
    )
    markdown = replace_marker_block(
        markdown,
        ARCHIVE_START,
        ARCHIVE_END,
        render_archive_block(new_history["history"]),
    )
    MARKDOWN_FILE.write_text(markdown)
    print(f"Updated {MARKDOWN_FILE} and archive for {month_entry['month']}")

    if MARKDOWN_FILE_ZH.exists():
        markdown_zh = MARKDOWN_FILE_ZH.read_text()
        markdown_zh = replace_marker_block(
            markdown_zh, UPDATES_START, UPDATES_END, render_latest_block_zh(month_entry)
        )
        markdown_zh = replace_marker_block(
            markdown_zh, COLLECTION_START, COLLECTION_END, render_collection_block_zh()
        )
        markdown_zh = replace_marker_block(
            markdown_zh,
            ARCHIVE_START,
            ARCHIVE_END,
            render_archive_block_zh(new_history["history"]),
        )
        MARKDOWN_FILE_ZH.write_text(markdown_zh)
        print(f"Updated {MARKDOWN_FILE_ZH}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"update_site.py failed: {exc}", file=sys.stderr)
        raise
