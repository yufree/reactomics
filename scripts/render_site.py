#!/usr/bin/env python3

import html
import sys
from pathlib import Path

import markdown


ROOT = Path(__file__).resolve().parents[1]
MAIN_MD_EN = ROOT / "reactomics.md"
MAIN_MD_ZH = ROOT / "reactomics_zh.md"

SITE_BASE = "https://yufree.github.io/reactomics"
OG_IMAGE = f"{SITE_BASE}/assets/pmd-orbitals.png"
AUTHOR_NAME = "Miao Yu"
AUTHOR_URL = "https://yufree.github.io/"


CSS = """
:root {
  --bg: #f4f5f7;
  --fg: #1a202c;
  --heading: #0d1117;
  --surface: #ffffff;
  --link: #1a56db;
  --link-hover: #1e429f;
  --border: #e2e8f0;
  --muted: #64748b;
  --code-bg: #f1f5f9;
  --accent: #1a56db;
  --accent-light: #eff6ff;
  --tag-bg: #f1f5f9;
  --tag-fg: #475569;
  --sidebar-w: 220px;
  --content-max: 760px;
  --toc-active: #1a56db;
}
@media (prefers-color-scheme: dark) {
  :root {
    --bg: #0f172a;
    --fg: #e2e8f0;
    --heading: #f8fafc;
    --surface: #1e293b;
    --link: #60a5fa;
    --link-hover: #93c5fd;
    --border: #334155;
    --muted: #94a3b8;
    --code-bg: #1e293b;
    --accent: #3b82f6;
    --accent-light: #1e3a5f;
    --tag-bg: #1e293b;
    --tag-fg: #94a3b8;
    --toc-active: #60a5fa;
  }
}
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
html { scroll-behavior: smooth; }
body {
  background: var(--bg);
  color: var(--fg);
  font: 15px/1.75 -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC",
        "Hiragino Sans GB", "Microsoft YaHei", Helvetica, Arial, sans-serif;
}

/* ── Skip link ── */
a.skip-link {
  position: absolute; top: -40px; left: 0;
  background: var(--accent); color: #fff;
  padding: 8px 16px; z-index: 200; transition: top .2s;
}
a.skip-link:focus { top: 0; }

/* ── Top bar ── */
.topbar {
  position: sticky; top: 0; z-index: 100;
  background: var(--surface);
  border-bottom: 1px solid var(--border);
  padding: 0 24px;
  display: flex; align-items: center; gap: 16px;
  height: 48px;
}
.topbar-brand {
  font-weight: 700; font-size: .95rem; color: var(--heading);
  text-decoration: none; letter-spacing: .01em;
  white-space: nowrap;
}
.topbar-brand:hover { color: var(--accent); text-decoration: none; }
.topbar-desc {
  font-size: .8rem; color: var(--muted); flex: 1;
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.lang-switch {
  display: flex; gap: 4px; flex-shrink: 0;
}
.lang-switch a {
  font-size: .78rem; padding: 3px 10px;
  border: 1px solid var(--border); border-radius: 20px;
  color: var(--muted); text-decoration: none; transition: all .15s;
}
.lang-switch a:hover,
.lang-switch a.active {
  background: var(--accent); border-color: var(--accent);
  color: #fff; text-decoration: none;
}

/* ── Page grid ── */
.page-grid {
  display: grid;
  grid-template-columns: var(--sidebar-w) minmax(0, var(--content-max));
  grid-template-rows: 1fr;
  max-width: calc(var(--sidebar-w) + var(--content-max) + 80px);
  margin: 0 auto;
  align-items: start;
  padding: 0 24px;
  gap: 0 40px;
}

/* ── TOC sidebar ── */
.toc-sidebar {
  position: sticky;
  top: 64px;
  max-height: calc(100vh - 80px);
  overflow-y: auto;
  padding: 24px 0 24px;
  font-size: .8rem;
  scrollbar-width: thin;
}
.toc-sidebar::-webkit-scrollbar { width: 4px; }
.toc-sidebar::-webkit-scrollbar-track { background: transparent; }
.toc-sidebar::-webkit-scrollbar-thumb { background: var(--border); border-radius: 2px; }
.toc-label {
  font-size: .7rem; font-weight: 700; letter-spacing: .08em;
  text-transform: uppercase; color: var(--muted);
  padding-bottom: 8px; margin-bottom: 4px;
  border-bottom: 1px solid var(--border);
}
#toc-list {
  list-style: none;
  padding: 0;
}
#toc-list li { margin: 0; }
#toc-list a {
  display: block;
  padding: 3px 8px;
  color: var(--muted);
  text-decoration: none;
  border-left: 2px solid transparent;
  transition: all .15s;
  line-height: 1.4;
}
#toc-list a:hover { color: var(--fg); border-left-color: var(--border); }
#toc-list a.active { color: var(--toc-active); border-left-color: var(--toc-active); font-weight: 600; }
#toc-list .toc-h3 > a { padding-left: 20px; font-size: .76rem; }

/* ── Main content ── */
.content-area {
  background: var(--surface);
  padding: 40px 40px 80px;
  min-height: calc(100vh - 48px);
  border-left: 1px solid var(--border);
  border-right: 1px solid var(--border);
}

/* ── Typography ── */
h1, h2, h3, h4 { color: var(--heading); line-height: 1.3; }
h1 { font-size: 2rem; margin-bottom: .75rem; }
h2 {
  font-size: 1.25rem; margin-top: 2.5rem; margin-bottom: .75rem;
  padding-top: .75rem; border-top: 1px solid var(--border);
}
h3 { font-size: 1rem; margin-top: 1.5rem; margin-bottom: .5rem; color: var(--muted); font-weight: 600; }
p { margin-bottom: 1rem; }
a { color: var(--link); text-decoration: none; }
a:hover { color: var(--link-hover); text-decoration: underline; }
code {
  background: var(--code-bg); padding: .1em .35em;
  border-radius: 4px; font-size: .88em; font-family: ui-monospace, "SF Mono", Menlo, monospace;
}
blockquote {
  margin: 1rem 0; padding: .75rem 1rem;
  border-left: 3px solid var(--accent);
  background: var(--accent-light); border-radius: 0 4px 4px 0;
}

/* ── Figures ── */
figure { margin: 1.5rem 0; text-align: center; }
figure img { max-width: 100%; height: auto; border-radius: 6px; box-shadow: 0 2px 12px rgba(0,0,0,.08); }
figcaption { font-size: .85rem; color: var(--muted); margin-top: .6rem; line-height: 1.5; max-width: 38rem; margin-left: auto; margin-right: auto; }
figcaption a { color: var(--link); }

/* ── Tables ── */
table { border-collapse: collapse; width: 100%; margin: 1rem 0; font-size: .88em; }
th, td { border: 1px solid var(--border); padding: .5rem .75rem; text-align: left; }
th { background: var(--code-bg); font-weight: 600; }
tr:nth-child(even) td { background: var(--code-bg); }

/* ── Lists ── */
ul, ol { padding-left: 1.4rem; margin-bottom: 1rem; }
li { margin-bottom: .3rem; }

/* ── Publication list ── */
.content-area h3 + ul,
.content-area h3 + p + ul {
  padding-left: 0; list-style: none;
}
.content-area h2#all-publications ~ h3 + ul li,
.content-area h2#monthly-literature-collection ~ h3 ~ ul li,
.content-area [id^="paired-mass"] + ul li,
.content-area [id^="pmd-network"] + ul li,
.content-area [id^="methods"] + ul li,
.content-area [id^="applications"] + ul li {
  padding: 0;
}

/* Target all li inside sections below h2#all-publications */
.pub-list {
  list-style: none;
  padding: 0;
  margin: 0 0 1rem;
}
.pub-list li {
  display: flex;
  align-items: baseline;
  gap: 8px;
  padding: 6px 0;
  border-bottom: 1px solid var(--border);
  font-size: .875rem;
  line-height: 1.5;
}
.pub-list li:last-child { border-bottom: none; }
.pub-list li::before { display: none; }
.pub-list .pub-title { flex: 1; }
.pub-list .pub-note { font-size: .8rem; color: var(--muted); }
.pub-list .pub-meta { flex-shrink: 0; font-size: .75rem; color: var(--muted); white-space: nowrap; }

/* ── DOM transformation sub-section indent ── */
h3[id*="dom-transformation"],
h3[id*="dom"] + ul,
h3[id*="dom"] ~ ul:first-of-type {
  margin-left: 1.4rem;
}
h3[id*="dom-transformation"] {
  font-size: .92em;
  color: var(--muted);
  border-left: 3px solid var(--border);
  padding-left: .6rem;
  margin-left: 1rem;
}

/* ── Section badge ── */
.section-heading {
  display: flex; align-items: center; gap: 8px;
}
.section-count {
  font-size: .7rem; background: var(--tag-bg); color: var(--tag-fg);
  padding: 1px 7px; border-radius: 10px; font-weight: 500;
}

/* ── Footer ── */
footer {
  margin-top: 3rem; padding: 1.5rem 40px;
  border-top: 1px solid var(--border);
  font-size: .8rem; color: var(--muted);
  background: var(--surface);
}

/* ── Responsive ── */
@media (max-width: 900px) {
  .page-grid {
    grid-template-columns: 1fr;
    padding: 0;
    gap: 0;
  }
  .toc-sidebar { display: none; }
  .content-area {
    border-left: none; border-right: none;
    padding: 24px 20px 60px;
  }
  footer { padding: 1rem 20px; }
}
"""

JS = """
(function () {
  // Build TOC from headings in the article
  var article = document.querySelector('article');
  var tocList = document.getElementById('toc-list');
  if (!article || !tocList) return;

  var headings = article.querySelectorAll('h2, h3');
  if (headings.length === 0) return;

  headings.forEach(function (h) {
    if (!h.id) return;
    var li = document.createElement('li');
    li.className = h.tagName === 'H3' ? 'toc-h3' : 'toc-h2';
    var a = document.createElement('a');
    a.href = '#' + h.id;
    a.textContent = h.textContent.replace(/\\s*\\d+\\s*$/, '');
    li.appendChild(a);
    tocList.appendChild(li);
  });

  // Highlight active section using IntersectionObserver
  var links = tocList.querySelectorAll('a');
  var activeId = null;

  var observer = new IntersectionObserver(function (entries) {
    entries.forEach(function (entry) {
      if (entry.isIntersecting) {
        activeId = entry.target.id;
        links.forEach(function (a) {
          a.classList.toggle('active', a.getAttribute('href') === '#' + activeId);
        });
      }
    });
  }, { rootMargin: '-20% 0px -70% 0px' });

  headings.forEach(function (h) { if (h.id) observer.observe(h); });

  // Style publication lists: wrap content in .pub-list
  var allPubSection = document.getElementById('all-publications');
  if (allPubSection) {
    var el = allPubSection.nextElementSibling;
    while (el) {
      if (el.tagName === 'H2') break;
      if (el.tagName === 'H3') {
        // Add count badge
        var nextUl = el.nextElementSibling;
        while (nextUl && nextUl.tagName !== 'UL') nextUl = nextUl.nextElementSibling;
        if (nextUl) {
          var count = nextUl.querySelectorAll('li').length;
          var badge = document.createElement('span');
          badge.className = 'section-count';
          badge.textContent = count;
          el.appendChild(badge);
          nextUl.classList.add('pub-list');
          // Wrap li contents
          nextUl.querySelectorAll('li').forEach(function (li) {
            var a = li.querySelector('a');
            var em = li.querySelector('em');
            if (a) {
              // Extract annotation text (text nodes after the <em>)
              var annotationText = '';
              li.childNodes.forEach(function (node) {
                if (node.nodeType === 3 && node.textContent.includes('—')) {
                  annotationText = node.textContent.replace(/^\s*—\s*/, '').trim();
                }
              });
              var titleSpan = document.createElement('span');
              titleSpan.className = 'pub-title';
              titleSpan.appendChild(a.cloneNode(true));
              if (annotationText) {
                var noteSpan = document.createElement('span');
                noteSpan.className = 'pub-note';
                noteSpan.textContent = ' — ' + annotationText;
                titleSpan.appendChild(noteSpan);
              }
              li.innerHTML = '';
              li.appendChild(titleSpan);
              if (em) {
                var metaSpan = document.createElement('span');
                metaSpan.className = 'pub-meta';
                metaSpan.innerHTML = em.outerHTML;
                li.appendChild(metaSpan);
              }
            }
          });
        }
      }
      el = el.nextElementSibling;
    }
  }
})();
"""


def render_markdown_file(source_path, output_path, title, lang="en",
                         alt_lang_url=None, alt_lang_label=None,
                         site_desc="PMD-based reactomics — introduction and monthly literature collection.",
                         description=None, keywords=None, canonical=None):
    if not source_path.exists():
        print(f"  Warning: {source_path} not found, skipping", file=sys.stderr)
        return

    body = markdown.markdown(
        source_path.read_text(),
        extensions=["extra", "toc", "sane_lists"],
        output_format="html5",
        extension_configs={"toc": {"toc_depth": "2-3"}},
    )

    # Language switcher links
    if alt_lang_url and alt_lang_label:
        cur_label = "EN" if lang == "en" else "中文"
        lang_switch = (
            f'<nav class="lang-switch" aria-label="Language">'
            f'<a href="#" class="active">{html.escape(cur_label)}</a>'
            f'<a href="{html.escape(alt_lang_url)}">{html.escape(alt_lang_label)}</a>'
            f'</nav>'
        )
    else:
        lang_switch = ""

    # SEO / discoverability metadata
    desc = description or site_desc
    kw = keywords or "reactomics, paired mass distance, PMD, mass spectrometry, metabolomics"
    page_filename = output_path.name
    canonical_url = canonical or f"{SITE_BASE}/{page_filename}"
    og_locale = "en_US" if lang == "en" else "zh_CN"
    alt_locale = "zh_CN" if lang == "en" else "en_US"
    alt_canonical = (
        f"{SITE_BASE}/{alt_lang_url}" if alt_lang_url else None
    )

    # hreflang alternate links
    hreflang_links = ""
    if alt_canonical:
        alt_hreflang = "zh" if lang == "en" else "en"
        hreflang_links = (
            f'  <link rel="alternate" hreflang="{lang}" href="{html.escape(canonical_url)}" />\n'
            f'  <link rel="alternate" hreflang="{alt_hreflang}" href="{html.escape(alt_canonical)}" />\n'
            f'  <link rel="alternate" hreflang="x-default" href="{SITE_BASE}/index.html" />\n'
        )

    # JSON-LD structured data
    import json as _json
    jsonld = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": title,
        "description": desc,
        "url": canonical_url,
        "image": OG_IMAGE,
        "inLanguage": lang,
        "author": {"@type": "Person", "name": AUTHOR_NAME, "url": AUTHOR_URL},
        "publisher": {"@type": "Person", "name": AUTHOR_NAME, "url": AUTHOR_URL},
        "keywords": kw,
        "mainEntityOfPage": {"@type": "WebPage", "@id": canonical_url},
    }
    jsonld_str = _json.dumps(jsonld, ensure_ascii=False, indent=2)

    html_doc = f"""<!DOCTYPE html>
<html lang="{lang}">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <meta name="color-scheme" content="light dark" />
  <title>{html.escape(title)}</title>
  <meta name="description" content="{html.escape(desc)}" />
  <meta name="keywords" content="{html.escape(kw)}" />
  <meta name="author" content="{html.escape(AUTHOR_NAME)}" />
  <link rel="canonical" href="{html.escape(canonical_url)}" />
{hreflang_links}  <meta property="og:type" content="article" />
  <meta property="og:title" content="{html.escape(title)}" />
  <meta property="og:description" content="{html.escape(desc)}" />
  <meta property="og:url" content="{html.escape(canonical_url)}" />
  <meta property="og:image" content="{html.escape(OG_IMAGE)}" />
  <meta property="og:locale" content="{og_locale}" />
  <meta property="og:locale:alternate" content="{alt_locale}" />
  <meta property="og:site_name" content="Reactomics" />
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:title" content="{html.escape(title)}" />
  <meta name="twitter:description" content="{html.escape(desc)}" />
  <meta name="twitter:image" content="{html.escape(OG_IMAGE)}" />
  <script type="application/ld+json">
{jsonld_str}
  </script>
  <style>{CSS}</style>
</head>
<body>
  <a class="skip-link" href="#content">Skip to content</a>

  <div class="topbar">
    <a class="topbar-brand" href="index.html">Reactomics</a>
    <span class="topbar-desc">{html.escape(site_desc)}</span>
    {lang_switch}
  </div>

  <div class="page-grid">
    <aside class="toc-sidebar" aria-label="Table of contents">
      <div class="toc-label">Contents</div>
      <ul id="toc-list"></ul>
    </aside>

    <div class="content-area" id="content">
      <article>
        {body}
      </article>
      <footer>
        <p>Generated from <a href="https://github.com">source repository</a>. Content is machine-managed with monthly updates.</p>
      </footer>
    </div>
  </div>

  <script>{JS}</script>
</body>
</html>
"""
    output_path.write_text(html_doc)


def main():
    desc_en = (
        "Reactomics uses paired mass distances (PMDs) in untargeted mass "
        "spectrometry data to identify and quantify chemical reactions "
        "directly — without compound identification. Theory, methods (pmd "
        "R package), and monthly-updated publications."
    )
    desc_zh = (
        "反应组学利用非靶向质谱数据中的配对质量距离（PMD）直接识别和"
        "量化化学反应——无需化合物鉴定。涵盖理论、方法（pmd R 包）以及"
        "每月更新的文献集合。"
    )
    kw_en = (
        "reactomics, paired mass distance, PMD, mass spectrometry, "
        "untargeted metabolomics, reaction network, getreact, globalstd, "
        "pmd R package, dissolved organic matter, biotransformation"
    )
    kw_zh = (
        "反应组学, 配对质量距离, PMD, 质谱, 非靶向代谢组学, 反应网络, "
        "getreact, globalstd, pmd R 包, 天然有机质, 生物转化"
    )

    title_en = "Reactomics — paired mass distance analysis for mass spectrometry"
    title_zh = "反应组学 — 基于配对质量距离的质谱分析框架"

    # English pages (index.html is canonical; reactomics.html points to it)
    render_markdown_file(
        MAIN_MD_EN, ROOT / "index.html", title_en,
        lang="en", alt_lang_url="index_zh.html", alt_lang_label="中文",
        description=desc_en, keywords=kw_en,
        canonical=f"{SITE_BASE}/index.html",
    )
    render_markdown_file(
        MAIN_MD_EN, ROOT / "reactomics.html", title_en,
        lang="en", alt_lang_url="reactomics_zh.html", alt_lang_label="中文",
        description=desc_en, keywords=kw_en,
        canonical=f"{SITE_BASE}/index.html",  # duplicate of index.html
    )

    # Chinese pages (index_zh.html is canonical; reactomics_zh.html points to it)
    render_markdown_file(
        MAIN_MD_ZH, ROOT / "index_zh.html", title_zh,
        lang="zh", alt_lang_url="index.html", alt_lang_label="EN",
        site_desc=desc_zh,
        description=desc_zh, keywords=kw_zh,
        canonical=f"{SITE_BASE}/index_zh.html",
    )
    render_markdown_file(
        MAIN_MD_ZH, ROOT / "reactomics_zh.html", title_zh,
        lang="zh", alt_lang_url="reactomics.html", alt_lang_label="EN",
        site_desc=desc_zh,
        description=desc_zh, keywords=kw_zh,
        canonical=f"{SITE_BASE}/index_zh.html",  # duplicate of index_zh.html
    )

    # Monthly archive pages
    updates_dir = ROOT / "updates"
    if updates_dir.exists():
        for md_path in sorted(updates_dir.glob("*.md")):
            if md_path.stem == ".gitkeep":
                continue
            render_markdown_file(
                md_path, md_path.with_suffix(".html"), md_path.stem,
                lang="en",
            )

    print("Rendered HTML pages (EN + ZH)")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"render_site.py failed: {exc}", file=sys.stderr)
        raise
