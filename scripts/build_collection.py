#!/usr/bin/env python3
"""
Build the full reactomics publication collection.

Sources (merged and deduplicated by DOI):
  1. reactomics.bib       — manually curated entries
  2. PubMed queries       — "reactomics" and "paired mass distance" in title/abstract
  3. NCBI elink           — PubMed-tracked citations of seed papers
  4. OpenCitations         — broader citation index for seed papers
  5. CrossRef metadata     — fills in details for DOI-only entries not in PubMed

Seed papers (Miao Yu / PMD method):
  PMID 34337162 — "Untargeted high-resolution paired mass distance data mining…" (Commun Chem 2020)
  PMID 32600037 — "Metabolism of SCCPs and MCCPs … Based on Paired Mass Distance" (ES&T 2020)

Outputs data/collection.json.
"""

import datetime as dt
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
BIB_FILE = ROOT / "reactomics.bib"
SOURCES_FILE = DATA_DIR / "source_queries.json"
OUTPUT_FILE = DATA_DIR / "collection.json"
SECTION_OVERRIDES_FILE = DATA_DIR / "section_overrides.json"
EXCLUDE_DOIS_FILE = DATA_DIR / "exclude_dois.json"
ANNOTATIONS_FILE = DATA_DIR / "annotations.json"

START_DATE = dt.date(2019, 1, 1)

# PMIDs of seed papers whose citations we want to collect
SEED_PMIDS = ["34337162", "32600037", "30661584"]
# DOIs of seed papers for OpenCitations lookup
SEED_DOIS = ["10.1038/s42004-020-00403-z", "10.1016/j.aca.2018.10.062"]

MAX_RETRIES = 3
BACKOFF_BASE = 2


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

def _get(url, params=None, *, parse_json=False, extra_headers=None):
    if params:
        url = f"{url}?{urllib.parse.urlencode(params)}"
    headers = {"User-Agent": "reactomics-collection-builder/1.0"}
    if extra_headers:
        headers.update(extra_headers)
    req = urllib.request.Request(url, headers=headers)
    last_exc = None
    for attempt in range(MAX_RETRIES):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.load(r) if parse_json else r.read().decode("utf-8")
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
            last_exc = exc
            if attempt < MAX_RETRIES - 1:
                wait = BACKOFF_BASE ** (attempt + 1)
                print(f"  Retry {attempt + 1}/{MAX_RETRIES} after {wait}s: {exc}", file=sys.stderr)
                time.sleep(wait)
    print(f"  Request failed after {MAX_RETRIES} attempts: {url} — {last_exc}", file=sys.stderr)
    return None


# ---------------------------------------------------------------------------
# BibTeX parser
# ---------------------------------------------------------------------------

BIB_MONTH_MAP = {
    "jan": "01", "feb": "02", "mar": "03", "apr": "04",
    "may": "05", "jun": "06", "jul": "07", "aug": "08",
    "sep": "09", "oct": "10", "nov": "11", "dec": "12",
}


def _bib_field(entry_text, field):
    pattern = re.compile(
        rf"\b{re.escape(field)}\s*=\s*"
        r"(?:\{((?:[^{}]|\{[^{}]*\})*)\}|\"([^\"]*)\"|(\w+))",
        re.IGNORECASE,
    )
    m = pattern.search(entry_text)
    if not m:
        return ""
    raw = m.group(1) or m.group(2) or m.group(3) or ""
    raw = re.sub(r"\\text\w+\{([^}]*)\}", r"\1", raw)
    raw = re.sub(r"\$[^$]*\$", "", raw)
    raw = re.sub(r"\\[a-zA-Z]+\s*", "", raw)
    raw = re.sub(r"[{}]", "", raw)
    return raw.strip()


def parse_bib(bib_path):
    if not bib_path.exists():
        return []
    text = bib_path.read_text(encoding="utf-8", errors="replace")
    entries = re.split(r"(?=@\w+\s*\{)", text)
    papers = []
    for entry in entries:
        if not re.match(r"@\w+\s*\{", entry.strip()):
            continue
        doi = _bib_field(entry, "doi").strip().lstrip("{").rstrip("}")
        if not doi:
            continue
        title = _bib_field(entry, "title")
        journal = _bib_field(entry, "journal")
        year_str = _bib_field(entry, "year")
        month_str = _bib_field(entry, "month").lower()[:3]
        month_num = BIB_MONTH_MAP.get(month_str, "01")
        try:
            year = int(year_str)
        except ValueError:
            year = 0
        published_date = f"{year}-{month_num}-01" if year else ""
        raw_authors = _bib_field(entry, "author")
        authors = []
        for part in re.split(r"\s+and\s+", raw_authors, flags=re.IGNORECASE):
            part = part.strip()
            if "," in part:
                last, _, first = part.partition(",")
                authors.append(f"{first.strip()} {last.strip()}")
            elif part:
                authors.append(part)
        papers.append({
            "title": title,
            "doi": doi,
            "url": f"https://doi.org/{doi}",
            "journal": journal,
            "year": year,
            "published_date": published_date,
            "authors": authors,
            "abstract": "",
            "source": "bib",
        })
    print(f"  Parsed {len(papers)} entries from bib file")
    return papers


# ---------------------------------------------------------------------------
# PubMed helpers
# ---------------------------------------------------------------------------

PUBMED_MONTH_MAP = {abbr.lower(): f"{i:02d}" for i, abbr in enumerate(
    ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
     "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"], 1
)}


def first_text(node, path):
    child = node.find(path)
    return "" if child is None or child.text is None else child.text.strip()


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
        month = PUBMED_MONTH_MAP.get(month.lower(), month).zfill(2) if month else "01"
        return f"{year}-{month}-{(day or '01').zfill(2)}"
    return ""


def esearch_range(query, start, end):
    date_filter = f'("{start:%Y/%m/%d}"[Date - Publication] : "{end:%Y/%m/%d}"[Date - Publication])'
    data = _get(
        "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi",
        params={"db": "pubmed", "term": f"({query}) AND {date_filter}",
                "retmode": "json", "retmax": 500, "sort": "pub date"},
        parse_json=True,
    )
    if data is None:
        return []
    result = data.get("esearchresult", {})
    if "ERROR" in result:
        print(f"  PubMed warning: {result['ERROR']}", file=sys.stderr)
    return result.get("idlist", [])


def elink_citing(pmid):
    """Return PMIDs of papers that cite the given PMID (PubMed Central index)."""
    data = _get(
        "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/elink.fcgi",
        params={"dbfrom": "pubmed", "db": "pubmed", "id": pmid,
                "linkname": "pubmed_pubmed_citedin", "retmode": "json"},
        parse_json=True,
    )
    if data is None:
        return []
    for ls in data.get("linksets", []):
        for lsd in ls.get("linksetdbs", []):
            if lsd.get("linkname") == "pubmed_pubmed_citedin":
                return lsd.get("links", [])
    return []


def opencitations_citing(doi):
    """Return citing DOIs from OpenCitations COCI index."""
    data = _get(
        f"https://opencitations.net/index/coci/api/v1/citations/{doi}",
        parse_json=True,
    )
    if not data:
        return []
    return [c.get("citing", "").strip() for c in data if c.get("citing")]


def chunked(items, size):
    for i in range(0, len(items), size):
        yield items[i : i + size]


def fetch_pubmed_details(pmids):
    """Fetch full metadata for a list of PMIDs. Returns dict keyed by DOI (lower)."""
    papers = {}
    for group in chunked(list(pmids), 100):
        xml_text = _get(
            "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi",
            params={"db": "pubmed", "id": ",".join(group), "retmode": "xml"},
        )
        if xml_text is None:
            continue
        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError as exc:
            print(f"  XML parse error: {exc}", file=sys.stderr)
            continue
        for article in root.findall(".//PubmedArticle"):
            medline = article.find("MedlineCitation")
            if medline is None:
                continue
            pmid = first_text(medline, "PMID")
            article_meta = medline.find(".//Article")
            if article_meta is None:
                continue
            title_node = article_meta.find("ArticleTitle")
            title = "".join(title_node.itertext()).strip() if title_node is not None else "Untitled"
            abstract_parts = []
            for section in article_meta.findall(".//Abstract/AbstractText"):
                text = "".join(section.itertext()).strip()
                if text:
                    abstract_parts.append(text)
            authors = []
            for author in article_meta.findall(".//AuthorList/Author"):
                last = first_text(author, "LastName")
                fore = first_text(author, "ForeName")
                collective = first_text(author, "CollectiveName")
                name = collective or " ".join(p for p in [fore, last] if p)
                if name:
                    authors.append(name)
            doi = ""
            for article_id in article.findall(".//ArticleId"):
                if article_id.attrib.get("IdType") == "doi" and article_id.text:
                    doi = article_id.text.strip()
                    break
            pub_date = parse_pub_date(article_meta)
            try:
                year = int(pub_date[:4]) if pub_date else 0
            except ValueError:
                year = 0
            if not doi:
                continue  # skip if no DOI — can't dedup reliably
            papers[doi.lower()] = {
                "title": title,
                "doi": doi,
                "url": f"https://doi.org/{doi}",
                "journal": first_text(article_meta, "Journal/Title"),
                "year": year,
                "published_date": pub_date,
                "authors": authors,
                "abstract": " ".join(abstract_parts),
                "source": "pubmed",
                "pmid": pmid,
            }
        time.sleep(0.34)
    return papers


def fetch_crossref_details(dois):
    """Fetch metadata for DOIs not found in PubMed, via CrossRef."""
    papers = {}
    for doi in dois:
        data = _get(
            f"https://api.crossref.org/works/{urllib.parse.quote(doi, safe='')}",
            parse_json=True,
            extra_headers={"User-Agent": "reactomics-collection-builder/1.0 (mailto:admin@reactomics.org)"},
        )
        if data is None:
            continue
        msg = data.get("message", {})
        title_list = msg.get("title", [])
        title = title_list[0] if title_list else "Untitled"
        container = msg.get("container-title", [])
        journal = container[0] if container else ""
        authors = []
        for auth in msg.get("author", []):
            given = auth.get("given", "")
            family = auth.get("family", "")
            name = f"{given} {family}".strip() if family else given
            if name:
                authors.append(name)
        date_parts = msg.get("published", {}).get("date-parts", [[]])[0]
        year = date_parts[0] if date_parts else 0
        month = f"{date_parts[1]:02d}" if len(date_parts) > 1 else "01"
        day = f"{date_parts[2]:02d}" if len(date_parts) > 2 else "01"
        pub_date = f"{year}-{month}-{day}" if year else ""
        real_doi = msg.get("DOI", doi)
        papers[real_doi.lower()] = {
            "title": title,
            "doi": real_doi,
            "url": f"https://doi.org/{real_doi}",
            "journal": journal,
            "year": year,
            "published_date": pub_date,
            "authors": authors,
            "abstract": "",
            "source": "crossref",
        }
        time.sleep(0.2)
    return papers


# ---------------------------------------------------------------------------
# Section assignment
# ---------------------------------------------------------------------------

def assign_section(paper):
    text = (paper.get("title", "") + " " + paper.get("abstract", "")).lower()
    if any(t in text for t in ["globalstd", "global std", "independent ion", "in-source reaction",
                                "in-source fragment", "adduct removal", "redundant peak",
                                "high-frequency mass", "high frequency mass"]):
        return "In-source reactions and independent ion selection"
    if any(t in text for t in ["reactomics", "paired mass distance", "pmd network", "getchain"]):
        if any(t in text for t in ["method", "algorithm", "software", "r package", "workflow",
                                    "tool", "benchmark", "database", "review", "perspective"]):
            return "Methods and tools"
        # fall through to application section detection
    if any(t in text for t in ["drug metabolism", "phase i", "phase ii", "glucuronidation",
                                "sulfation", "cytochrome", "cyp", "xenobiotic", "pharmacokinetic",
                                "leukemia", "cancer", "clinical", "therapeutic"]):
        return "Applications in drug metabolism"
    if any(t in text for t in ["dissolved organic matter", "dom", "wastewater", "water treatment",
                                "disinfection", "environmental", "sediment", "soil", "wildfire",
                                "sludge", "contaminant", "pesticide", "pollutant", "biochar"]):
        return "Applications in environmental transformation"
    if any(t in text for t in ["plasma", "urine", "serum", "human", "endogenous",
                                "biomarker", "metabolomics", "cohort", "disease", "biological"]):
        return "Applications in endogenous metabolomics"
    if any(t in text for t in ["r package", "software", "workflow", "algorithm", "tool"]):
        return "Methods and tools"
    return "Applications in environmental transformation"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    today = dt.date.today()
    all_papers: dict[str, dict] = {}  # keyed by doi.lower()

    # 1. Parse bib file
    print("1. Parsing bib file…")
    for p in parse_bib(BIB_FILE):
        key = p["doi"].lower()
        all_papers[key] = p

    # 2. PubMed tight queries
    print("2. PubMed tight queries (reactomics + paired mass distance)…")
    queries = json.loads(SOURCES_FILE.read_text()) if SOURCES_FILE.exists() else []
    pmid_set = set()
    for source in queries:
        pmids = esearch_range(source["query"], START_DATE, today)
        print(f"   {source['name']}: {len(pmids)} papers")
        pmid_set.update(pmids)
        time.sleep(0.34)
    print(f"   Unique PMIDs from queries: {len(pmid_set)}")

    # 3. elink citing papers
    print("3. NCBI elink citations…")
    for pmid in SEED_PMIDS:
        citing = elink_citing(pmid)
        print(f"   PMID {pmid}: {len(citing)} citing papers")
        pmid_set.update(citing)
        time.sleep(0.34)
    print(f"   Total PMIDs after elink: {len(pmid_set)}")

    # 4. Fetch PubMed details for all collected PMIDs
    print(f"4. Fetching PubMed metadata for {len(pmid_set)} PMIDs…")
    pubmed_papers = fetch_pubmed_details(pmid_set)
    print(f"   Got details for {len(pubmed_papers)} papers (with DOIs)")
    for doi_key, paper in pubmed_papers.items():
        if doi_key in all_papers:
            # PubMed fills in abstract and metadata; keep existing source tag
            existing = all_papers[doi_key]
            paper["source"] = "bib+pubmed" if existing["source"] == "bib" else "pubmed"
            if not paper["abstract"] and existing.get("abstract"):
                paper["abstract"] = existing["abstract"]
        all_papers[doi_key] = paper

    # 5. OpenCitations + CrossRef for papers not in PubMed
    print("5. OpenCitations citing papers for seed DOIs…")
    oc_dois: set[str] = set()
    for doi in SEED_DOIS:
        citing_dois = opencitations_citing(doi)
        print(f"   {doi}: {len(citing_dois)} citing DOIs")
        oc_dois.update(d.lower() for d in citing_dois if d)
        time.sleep(0.5)

    missing_dois = oc_dois - set(all_papers.keys())
    print(f"   {len(missing_dois)} DOIs not yet in collection — fetching via CrossRef…")
    crossref_papers = fetch_crossref_details(list(missing_dois))
    print(f"   Got CrossRef metadata for {len(crossref_papers)} papers")
    for doi_key, paper in crossref_papers.items():
        if doi_key not in all_papers:
            all_papers[doi_key] = paper

    # Mark papers also found via OpenCitations
    for doi_key in oc_dois:
        if doi_key in all_papers and "oc" not in all_papers[doi_key].get("source", ""):
            src = all_papers[doi_key]["source"]
            all_papers[doi_key]["source"] = f"{src}+oc" if src else "oc"

    # 6. Load manual overrides, exclusions, and annotations
    overrides = json.loads(SECTION_OVERRIDES_FILE.read_text()) if SECTION_OVERRIDES_FILE.exists() else {}
    overrides = {k.lower(): v for k, v in overrides.items()}
    exclude_dois = set(json.loads(EXCLUDE_DOIS_FILE.read_text())) if EXCLUDE_DOIS_FILE.exists() else set()
    annotations = json.loads(ANNOTATIONS_FILE.read_text()) if ANNOTATIONS_FILE.exists() else {}
    annotations = {k.lower(): v for k, v in annotations.items()}

    # 7. Assign sections and apply overrides/annotations
    print("7. Assigning sections…")
    for doi_key, paper in all_papers.items():
        if doi_key in overrides:
            paper["section"] = overrides[doi_key]
        else:
            paper["section"] = assign_section(paper)
        if doi_key in annotations:
            paper["annotation"] = annotations[doi_key]
        # Strip abstract from output to keep file size reasonable
        paper.pop("abstract", None)

    # 8. Filter: exclude listed DOIs and apply date range
    # Seed DOIs are always included regardless of date (first-published vs issue date discrepancy)
    force_include = {d.lower() for d in SEED_DOIS}

    def is_in_range(doi_key, paper):
        if doi_key in force_include:
            return True
        date_str = paper.get("published_date", "")
        if not date_str:
            return True
        try:
            return dt.date.fromisoformat(date_str[:10]) >= START_DATE
        except ValueError:
            return True

    filtered = {k: v for k, v in all_papers.items()
                if is_in_range(k, v) and k not in exclude_dois}
    print(f"   Kept {len(filtered)} papers (from {START_DATE} onward)")

    # 9. Sort by date descending
    sorted_papers = sorted(
        filtered.values(),
        key=lambda p: (p.get("published_date") or "", p.get("title") or ""),
        reverse=True,
    )

    payload = {
        "generated_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "start_date": START_DATE.isoformat(),
        "end_date": today.isoformat(),
        "total": len(sorted_papers),
        "papers": sorted_papers,
    }
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
    print(f"Wrote {len(sorted_papers)} papers to {OUTPUT_FILE}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"build_collection.py failed: {exc}", file=sys.stderr)
        raise
