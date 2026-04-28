#!/usr/bin/env python3

import datetime as dt
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
SOURCES_FILE = DATA_DIR / "source_queries.json"
OUTPUT_FILE = DATA_DIR / "papers.json"

MAX_RETRIES = 3
BACKOFF_BASE = 2  # seconds


def resolve_month():
    target = os.environ.get("TARGET_MONTH", "").strip()
    if target:
        try:
            year, month = map(int, target.split("-"))
        except (ValueError, IndexError) as exc:
            raise ValueError(
                f"TARGET_MONTH must be YYYY-MM format, got '{target}'"
            ) from exc
        if not (1 <= month <= 12):
            raise ValueError(f"TARGET_MONTH month must be 1–12, got {month}")
        if year < 1900 or year > 2100:
            raise ValueError(f"TARGET_MONTH year out of range, got {year}")
        start = dt.date(year, month, 1)
    else:
        today = dt.date.today().replace(day=1)
        last_day_previous = today - dt.timedelta(days=1)
        start = last_day_previous.replace(day=1)
    if start.month == 12:
        end = dt.date(start.year + 1, 1, 1) - dt.timedelta(days=1)
    else:
        end = dt.date(start.year, start.month + 1, 1) - dt.timedelta(days=1)
    return start, end


def _http_request(url, params, *, parse_json=False):
    query = urllib.parse.urlencode(params)
    full_url = f"{url}?{query}"
    req = urllib.request.Request(
        full_url, headers={"User-Agent": "reactomics-monthly-updater/1.0"}
    )
    last_exc = None
    for attempt in range(MAX_RETRIES):
        try:
            with urllib.request.urlopen(req, timeout=60) as response:
                if parse_json:
                    return json.load(response)
                return response.read().decode("utf-8")
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
            last_exc = exc
            if attempt < MAX_RETRIES - 1:
                wait = BACKOFF_BASE ** (attempt + 1)
                print(
                    f"  Retry {attempt + 1}/{MAX_RETRIES} after {wait}s: {exc}",
                    file=sys.stderr,
                )
                time.sleep(wait)
    raise RuntimeError(
        f"HTTP request failed after {MAX_RETRIES} attempts: {full_url}"
    ) from last_exc


def http_get_json(url, params):
    return _http_request(url, params, parse_json=True)


def http_get_text(url, params):
    return _http_request(url, params, parse_json=False)


def load_queries():
    if not SOURCES_FILE.exists():
        raise FileNotFoundError(f"Source queries file not found: {SOURCES_FILE}")
    return json.loads(SOURCES_FILE.read_text())


def esearch(query, start, end):
    date_filter = f'("{start:%Y/%m/%d}"[Date - Publication] : "{end:%Y/%m/%d}"[Date - Publication])'
    term = f"({query}) AND {date_filter}"
    data = http_get_json(
        "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi",
        {
            "db": "pubmed",
            "term": term,
            "retmode": "json",
            "retmax": 200,
            "sort": "pub date",
        },
    )
    result = data.get("esearchresult", {})
    if "ERROR" in result:
        print(f"  PubMed search warning: {result['ERROR']}", file=sys.stderr)
    return result.get("idlist", [])


def chunked(items, size):
    for index in range(0, len(items), size):
        yield items[index : index + size]


def first_text(node, path):
    child = node.find(path)
    return "" if child is None or child.text is None else child.text.strip()


MONTH_MAP = {abbr.lower(): f"{i:02d}" for i, abbr in enumerate(
    ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
     "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"], 1
)}


def parse_pub_date(article):
    article_date = article.find(".//ArticleDate")
    if article_date is not None:
        year = first_text(article_date, "Year")
        month = first_text(article_date, "Month")
        day = first_text(article_date, "Day")
        if year and len(year) == 4:
            return f"{year}-{(month or '01').zfill(2)}-{(day or '01').zfill(2)}"

    pub_date = article.find(".//PubDate")
    if pub_date is not None:
        year = first_text(pub_date, "Year")
        month = first_text(pub_date, "Month")
        day = first_text(pub_date, "Day")
        if not year or len(year) != 4:
            return ""
        month = MONTH_MAP.get(month.lower(), month).zfill(2) if month else "01"
        return f"{year}-{month}-{(day or '01').zfill(2)}"
    return ""


def fetch_details(pmids):
    papers = {}
    for group in chunked(pmids, 100):
        xml_text = http_get_text(
            "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi",
            {
                "db": "pubmed",
                "id": ",".join(group),
                "retmode": "xml",
            },
        )
        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError as exc:
            print(f"  XML parse error for batch, skipping: {exc}", file=sys.stderr)
            continue

        for article in root.findall(".//PubmedArticle"):
            medline = article.find("MedlineCitation")
            if medline is None:
                print("  Skipping article with missing MedlineCitation", file=sys.stderr)
                continue
            pmid = first_text(medline, "PMID")
            article_meta = medline.find(".//Article")
            if article_meta is None:
                print(f"  Skipping PMID {pmid}: missing Article element", file=sys.stderr)
                continue
            title_node = article_meta.find("ArticleTitle")
            title_text = (
                "".join(title_node.itertext()).strip() if title_node is not None else ""
            )
            if not title_text:
                title_text = "Untitled article"
            abstract_parts = []
            for section in article_meta.findall(".//Abstract/AbstractText"):
                label = section.attrib.get("Label", "").strip()
                text = "".join(section.itertext()).strip()
                if not text:
                    continue
                abstract_parts.append(f"{label}: {text}" if label else text)
            authors = []
            for author in article_meta.findall(".//AuthorList/Author"):
                last = first_text(author, "LastName")
                fore = first_text(author, "ForeName")
                collective = first_text(author, "CollectiveName")
                name = collective or " ".join(part for part in [fore, last] if part)
                if name:
                    authors.append(name)
            doi = ""
            for article_id in article.findall(".//ArticleId"):
                if article_id.attrib.get("IdType") == "doi" and article_id.text:
                    doi = article_id.text.strip()
                    break
            publication_types = []
            for pub_type in article_meta.findall(".//PublicationType"):
                if pub_type.text:
                    publication_types.append(pub_type.text.strip())
            papers[pmid] = {
                "pmid": pmid,
                "title": title_text,
                "abstract": " ".join(abstract_parts),
                "journal": first_text(article_meta, "Journal/Title"),
                "published_date": parse_pub_date(article_meta),
                "doi": doi,
                "url": f"https://doi.org/{doi}"
                if doi
                else f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                "authors": authors,
                "publication_types": publication_types,
                "source_queries": [],
            }
        time.sleep(0.34)
    return papers


def main():
    start, end = resolve_month()
    print(f"Fetching papers for {start:%Y-%m} ({start} to {end})")
    queries = load_queries()
    pmid_to_queries = {}
    query_summaries = []

    for source in queries:
        pmids = esearch(source["query"], start, end)
        query_summaries.append({"name": source["name"], "count": len(pmids)})
        print(f"  {source['name']}: {len(pmids)} papers")
        for pmid in pmids:
            pmid_to_queries.setdefault(pmid, []).append(source["name"])
        time.sleep(0.34)

    all_pmids = sorted(pmid_to_queries.keys())
    print(f"  Total unique PMIDs: {len(all_pmids)}")

    if not all_pmids:
        print("  No papers found for this month", file=sys.stderr)

    papers = fetch_details(all_pmids)
    for pmid, source_names in pmid_to_queries.items():
        if pmid in papers:
            papers[pmid]["source_queries"] = sorted(source_names)

    payload = {
        "generated_at": dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
        "month": start.strftime("%Y-%m"),
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "query_summaries": query_summaries,
        "papers": sorted(
            papers.values(),
            key=lambda item: (item["published_date"], item["title"]),
            reverse=True,
        ),
    }
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
    print(f"Wrote {len(payload['papers'])} papers to {OUTPUT_FILE}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"fetch_monthly_papers.py failed: {exc}", file=sys.stderr)
        raise
