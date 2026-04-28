#!/usr/bin/env python3

import datetime as dt
import json
import os
import re
import sys
import urllib.error
import urllib.request
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
INPUT_FILE = DATA_DIR / "papers.json"
OUTPUT_FILE = DATA_DIR / "selected-updates.json"

MAX_RETRIES = 3
BACKOFF_BASE = 2

PRIORITY_JOURNALS = {
    "Nature",
    "Science",
    "Nature Methods",
    "Nature Communications",
    "Analytical Chemistry",
    "Journal of the American Society for Mass Spectrometry",
    "Metabolomics",
    "Journal of Proteome Research",
    "Molecular & Cellular Proteomics",
    "Bioinformatics",
    "PLOS Computational Biology",
    "Communications Chemistry",
}


def load_papers():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Papers file not found: {INPUT_FILE}. "
            "Run fetch_monthly_papers.py first."
        )
    data = json.loads(INPUT_FILE.read_text())
    if "month" not in data or "papers" not in data:
        raise ValueError(
            "Invalid papers.json structure: missing 'month' or 'papers' key"
        )
    return data


def score_paper(paper):
    text = " ".join(
        [
            paper.get("title", ""),
            paper.get("abstract", ""),
            " ".join(paper.get("publication_types", [])),
        ]
    ).lower()
    title = paper.get("title", "").lower()
    score = 0

    if "reactomics" in text:
        score += 15
    if "paired mass distance" in text or "paired mass difference" in text:
        score += 12
    if " pmd " in text or text.startswith("pmd ") or " pmd." in text:
        score += 10
    if "global reaction relationship" in text or "grrn" in text:
        score += 12
    if paper.get("journal") in PRIORITY_JOURNALS:
        score += 8
    if any(
        token in text
        for token in ["review", "perspective", "consensus", "benchmark", "framework"]
    ):
        score += 8
    if any(
        token in text
        for token in ["reaction network", "metabolic network", "reaction database"]
    ):
        score += 7
    if any(
        token in text
        for token in ["biotransformation", "transformation product", "metabolite identification"]
    ):
        score += 6
    if any(
        token in text
        for token in ["untargeted metabolomics", "high resolution mass spectrometry", "accurate mass"]
    ):
        score += 5
    if any(
        token in text
        for token in ["drug metabolism", "phase i", "phase ii", "cytochrome p450", "cyp450"]
    ):
        score += 5
    if any(
        token in text
        for token in ["r package", "software", "tool", "workflow", "pipeline", "algorithm"]
    ):
        score += 4
    if any(
        token in title for token in ["case report", "protocol", "conference abstract"]
    ):
        score -= 10
    if any(
        pub_type.lower() == "review"
        for pub_type in paper.get("publication_types", [])
    ):
        score += 5
    return score


def choose_section(paper):
    text = " ".join([paper.get("title", ""), paper.get("abstract", "")]).lower()

    if any(
        token in text
        for token in ["globalstd", "global std", "independent ion", "in-source reaction",
                      "in-source fragment", "adduct removal", "redundant peak",
                      "high-frequency mass", "high frequency mass"]
    ):
        return "In-source reactions and independent ion selection"
    if "reactomics" in text or "paired mass distance" in text:
        return "Paired mass distance and chemical reactions"
    if any(
        token in text
        for token in ["pmd network", "reaction network", "getchain", "reaction chain"]
    ):
        return "PMD network"
    if any(
        token in text
        for token in ["r package", "software", "workflow", "pipeline", "algorithm", "tool", "benchmark"]
    ):
        return "Methods and tools"
    if any(
        token in text
        for token in ["drug metabolism", "phase i", "phase ii", "glucuronidation",
                      "sulfation", "cytochrome", "cyp", "xenobiotic"]
    ):
        return "Applications in drug metabolism"
    if any(
        token in text
        for token in ["environmental", "water", "sediment", "contaminant",
                      "disinfection", "pesticide", "pollutant", "transformation product"]
    ):
        return "Applications in environmental transformation"
    if any(
        token in text
        for token in ["plasma", "urine", "serum", "human", "endogenous",
                      "biomarker", "disease", "clinical", "cohort"]
    ):
        return "Applications in endogenous metabolomics"
    return "Paired mass distance and chemical reactions"


def summarize_fallback(paper):
    section = choose_section(paper)
    title = paper.get("title", "Untitled paper")
    journal = paper.get("journal", "the literature")
    if section == "Paired mass distance and chemical reactions":
        return (
            f"{title} appears relevant because it advances PMD-based analysis "
            f"or reaction-level interpretation of mass spectrometry data in {journal}."
        )
    if section == "Global reaction relationship network (GRRN)":
        return (
            f"{title} appears relevant because it describes reaction network "
            "construction, comparison, or application from untargeted MS data."
        )
    if section == "Methods and tools":
        return (
            f"{title} appears relevant because it introduces or benchmarks a tool, "
            "algorithm, or workflow applicable to reactomics or reaction-based metabolomics."
        )
    if section == "Applications in drug metabolism":
        return (
            f"{title} appears relevant because it applies reaction-based or untargeted "
            "approaches to characterize drug biotransformation."
        )
    if section == "Applications in environmental transformation":
        return (
            f"{title} appears relevant because it traces chemical transformation "
            "products in environmental matrices using mass spectrometry."
        )
    return (
        f"{title} appears relevant to the reactomics field because it connects "
        "metabolomics, mass spectrometry, or reaction networks to biological interpretation."
    )


def llm_available():
    return bool(os.environ.get("LLM_API_KEY")) and bool(os.environ.get("LLM_MODEL"))


def extract_json_block(text):
    cleaned = text.strip()
    fence_pattern = re.compile(r"^```(?:json)?\s*\n(.*?)\n\s*```$", re.S)
    fence_match = fence_pattern.search(cleaned)
    if fence_match:
        cleaned = fence_match.group(1).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass
    start_idx = cleaned.find("{")
    if start_idx == -1:
        raise ValueError("No JSON object found in LLM response")
    depth = 0
    in_string = False
    escape_next = False
    for i in range(start_idx, len(cleaned)):
        ch = cleaned[i]
        if escape_next:
            escape_next = False
            continue
        if ch == "\\":
            escape_next = True
            continue
        if ch == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(cleaned[start_idx : i + 1])
                except json.JSONDecodeError as exc:
                    raise ValueError(
                        f"Found JSON-like block but it failed to parse: {exc}"
                    ) from exc
    raise ValueError("No complete JSON object found in LLM response")


def validate_llm_updates(updates):
    if not isinstance(updates, list):
        print(
            f"  LLM returned non-list updates type: {type(updates).__name__}",
            file=sys.stderr,
        )
        return []
    required_keys = {"title", "url", "section", "summary"}
    validated = []
    for i, update in enumerate(updates):
        if not isinstance(update, dict):
            print(f"  Skipping non-dict update at index {i}", file=sys.stderr)
            continue
        missing = required_keys - set(update.keys())
        if missing:
            print(
                f"  Skipping update '{update.get('title', '?')}': missing {missing}",
                file=sys.stderr,
            )
            continue
        validated.append(update)
    return validated


def _scrub_key(message):
    api_key = os.environ.get("LLM_API_KEY", "")
    if api_key and api_key in str(message):
        return str(message).replace(api_key, "***REDACTED***")
    return str(message)


def call_llm(candidates, month):
    base_url = os.environ.get("LLM_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    api_key = os.environ["LLM_API_KEY"]
    model = os.environ["LLM_MODEL"]

    prompt = {
        "month": month,
        "task": (
            "Select at most 5 papers that are textbook-worthy updates for a public reactomics webpage. "
            "Reactomics is the study of chemical reactions using paired mass distances (PMDs) in mass spectrometry data. "
            "Keep only papers that advance PMD methodology, reaction network analysis (GRRN), "
            "major software tools, broad reviews, or important application studies that reshape understanding of "
            "drug metabolism, environmental transformation, or endogenous metabolic networks. "
            "Reject narrow incremental studies."
        ),
        "required_output_schema": {
            "updates": [
                {
                    "title": "paper title",
                    "url": "doi or official url",
                    "section": "matching section heading from the webpage",
                    "importance": "high or medium",
                    "summary": "2-3 sentence textbook-style summary",
                    "why_it_matters": "1 sentence",
                }
            ]
        },
        "section_headings": [
            "Paired mass distance and chemical reactions",
            "PMD network",
            "Methods and tools",
            "Applications in drug metabolism",
            "Applications in environmental transformation",
            "Applications in endogenous metabolomics",
        ],
        "candidates": candidates,
    }

    body = {
        "model": model,
        "temperature": 0.2,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are curating a reactomics literature collection webpage focused on PMD-based "
                    "reaction network analysis in mass spectrometry. "
                    "Return strict JSON only (no markdown fences). Be conservative. Prefer major reviews, "
                    "new tools, methodological advances, and field-shaping papers over narrow application studies."
                ),
            },
            {"role": "user", "content": json.dumps(prompt)},
        ],
    }

    request = urllib.request.Request(
        f"{base_url}/chat/completions",
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
            "User-Agent": "reactomics-monthly-updater/1.0",
        },
        method="POST",
    )

    last_exc = None
    for attempt in range(MAX_RETRIES):
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                payload = json.load(response)
            content = payload["choices"][0]["message"]["content"]
            parsed = extract_json_block(content)
            raw_updates = parsed.get("updates", [])
            return validate_llm_updates(raw_updates)
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
            last_exc = exc
            if attempt < MAX_RETRIES - 1:
                wait = BACKOFF_BASE ** (attempt + 1)
                print(
                    f"  LLM retry {attempt + 1}/{MAX_RETRIES} after {wait}s: {_scrub_key(exc)}",
                    file=sys.stderr,
                )
                time.sleep(wait)
        except (json.JSONDecodeError, ValueError, KeyError) as exc:
            print(f"  LLM response parse error: {_scrub_key(exc)}", file=sys.stderr)
            return []

    print(
        f"  LLM call failed after {MAX_RETRIES} attempts: {_scrub_key(last_exc)}",
        file=sys.stderr,
    )
    return []


def main():
    data = load_papers()
    month = data["month"]
    papers = data["papers"]
    print(f"Scoring {len(papers)} papers for {month}")

    ranked = []
    for paper in papers:
        paper_copy = dict(paper)
        paper_copy["score"] = score_paper(paper)
        paper_copy["suggested_section"] = choose_section(paper_copy)
        ranked.append(paper_copy)
    ranked.sort(
        key=lambda item: (item["score"], item.get("published_date", ""), item["title"]),
        reverse=True,
    )

    candidates = []
    for paper in ranked[:25]:
        candidates.append(
            {
                "title": paper["title"],
                "journal": paper.get("journal", ""),
                "published_date": paper.get("published_date", ""),
                "url": paper.get("url", ""),
                "doi": paper.get("doi", ""),
                "publication_types": paper.get("publication_types", []),
                "score": paper["score"],
                "suggested_section": paper["suggested_section"],
                "abstract": paper.get("abstract", "")[:2500],
            }
        )

    if llm_available():
        print("  LLM configured — running automatic selection")
        updates = call_llm(candidates, month)
        mode = "llm" if updates else "llm_no_results"
    else:
        print("  LLM not configured — generating review queue only")
        updates = []
        mode = "review_queue_only"

    payload = {
        "generated_at": dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
        "month": month,
        "mode": mode,
        "updates": updates,
        "papers": [
            {
                "title": paper["title"],
                "url": paper.get("url", ""),
                "doi": paper.get("doi", ""),
                "journal": paper.get("journal", ""),
                "published_date": paper.get("published_date", ""),
                "authors": paper.get("authors", []),
                "section": paper["suggested_section"],
                "score": paper["score"],
            }
            for paper in ranked
        ],
    }
    OUTPUT_FILE.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
    print(f"Wrote monthly selection data to {OUTPUT_FILE} (mode: {mode})")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"select_monthly_updates.py failed: {exc}", file=sys.stderr)
        raise
