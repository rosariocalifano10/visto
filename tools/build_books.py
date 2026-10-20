#!/usr/bin/env python3
"""Build letto/catalog.json, the book list Letto searches, from Wikidata (public domain, CC0).

Runs on GitHub Actions (.github/workflows/books.yml): on demand and on the 1st of each month,
so new books appear without touching the app. Standard library only.

Data comes from QLever (University of Freiburg), a fast public SPARQL endpoint over Wikidata.

Output: {"v":1, "built":..., "count":N, "books":[[title, year, popularity, author, alt?, author_it?], ...]}
  - title:  Italian title for books written in Italian, English title for everything else
  - alt:    the other-language title when it differs, so searching either name finds the book
  - year:   first publication (negative = BC), null when Wikidata has none
  - author: up to two authors, "" when none is recorded (anonymous classics)
  - author_it: the authors' Italian names when they differ (Dostoevskij, Tolstoj), so either spelling finds them
  - popularity: number of Wikimedia sites (Wikipedias, Wikisource...) with a page on the book
"""
import datetime as dt
import json
import os
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request

ENDPOINT = "https://qlever.cs.uni-freiburg.de/api/wikidata"
UA = "LettoCatalog/1.0 (https://github.com/rosariocalifano10/visto; personal reading diary, monthly refresh)"
MIN_SITELINKS = 2       # a book needs a page on at least this many Wikimedia sites, or an Italian Wikipedia article
MIN_UNDATED = 12        # books with no date at all are kept only when this widely covered (Beowulf, the Mahabharata...)
MAX_BOOKS = 80000       # keep the most widely covered books if there are more
MIN_EXPECTED = 25000    # fewer than this means something broke: keep the previous catalog
ITALIAN_LANG = "http://www.wikidata.org/entity/Q652"
ENGLISH_LANG = "http://www.wikidata.org/entity/Q1860"
ITALY = "http://www.wikidata.org/entity/Q38"

# literary work (novels, poems, plays, collections...), book, and things filed directly as "written work"
# (much non-fiction). Only direct instances of written work: its subclasses include millions of scholarly articles.
QUERY = """PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
PREFIX wikibase: <http://wikiba.se/ontology#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
PREFIX schema: <http://schema.org/>
SELECT ?book (MAX(?s0) AS ?s) (MIN(YEAR(?pd)) AS ?y1) (MIN(YEAR(?id)) AS ?y2)
       (SAMPLE(?it0) AS ?it) (SAMPLE(?en0) AS ?en) (SAMPLE(?itw0) AS ?itw) (SAMPLE(?enw0) AS ?enw)
       (GROUP_CONCAT(DISTINCT STR(?lang); SEPARATOR=" ") AS ?langs)
       (GROUP_CONCAT(DISTINCT STR(?country); SEPARATOR=" ") AS ?countries)
       (GROUP_CONCAT(DISTINCT ?auen; SEPARATOR="|") AS ?auens)
       (GROUP_CONCAT(DISTINCT ?auit; SEPARATOR="|") AS ?auits)
       (GROUP_CONCAT(DISTINCT ?tyl; SEPARATOR="|") AS ?types)
WHERE {
  { ?book wdt:P31/wdt:P279* wd:Q7725634 } UNION { ?book wdt:P31/wdt:P279* wd:Q571 } UNION { ?book wdt:P31 wd:Q47461344 }
  ?book wikibase:sitelinks ?s0 .
  FILTER(xsd:integer(?s0) >= 1)
  OPTIONAL { ?book wdt:P577 ?pd }
  OPTIONAL { ?book wdt:P571 ?id }
  OPTIONAL { ?book wdt:P407 ?lang }
  OPTIONAL { ?book wdt:P495 ?country }
  OPTIONAL { ?book wdt:P50 ?au . OPTIONAL { ?au rdfs:label ?auen FILTER(LANG(?auen) = "en") } OPTIONAL { ?au rdfs:label ?auit FILTER(LANG(?auit) = "it") } }
  OPTIONAL { ?book rdfs:label ?it0 FILTER(LANG(?it0) = "it") }
  OPTIONAL { ?book rdfs:label ?en0 FILTER(LANG(?en0) = "en") }
  OPTIONAL { ?a1 schema:about ?book ; schema:isPartOf <https://it.wikipedia.org/> ; schema:name ?itw0 }
  OPTIONAL { ?a2 schema:about ?book ; schema:isPartOf <https://en.wikipedia.org/> ; schema:name ?enw0 }
  OPTIONAL { ?book wdt:P31 ?ty . ?ty rdfs:label ?tyl FILTER(LANG(?tyl) = "en") }
  FILTER(xsd:integer(?s0) >= %d || BOUND(?itw0))
}
GROUP BY ?book
""" % MIN_SITELINKS

# "Beloved (novel)" -> "Beloved", "It (Stephen King novel)" -> "It", "Il deserto dei Tartari (romanzo)" -> ...
WIKI_SUFFIX = re.compile(
    r"\s*\((?:[^()]*\b(?:novel|novella|novels|book|poem|play|story|stories|collection|memoir|essay|epic|"
    r"romanzo|libro|racconto|racconti|poema|poesia|saggio|opera|dramma|tragedia|commedia|fumetto|manga|comic|comics)\b[^()]*|\d{4})\)$",
    re.I,
)
# Wikidata labels that are not a usable title
BAD_TITLE = re.compile(r"^Q\d+$")
# Things filed under literary work / book that nobody logs as a book they read: websites and wikis, software,
# reference works, laws and treaties, parts of scripture, manuscripts, periodicals, speeches, songs and operas,
# TV, games, and Wikidata housekeeping classes.
BAD_TYPE = re.compile(
    r"\b(website|wiki|wikimedia|software|cryptocurrenc\w*|protocol|database|dictionary|encyclopa?edia|"
    r"book of the bible|biblical|gospel|surah|sura|epistle|chapter(?! book)|psalm|law|legislation|treaty|constitution|"
    r"declaration|charter|resolution|standard|specification|scholarly article|manuscript|codex|"
    r"magazine|newspaper|journal|periodical|speech|anthem|hymn|prayer|wikipedia|glossary|list article|overview article|"
    r"song|single|music|musical|opera|operetta|ballet|track|television|tv series|limited series|miniseries|pilot|"
    r"video game|meme|webcomic|recipe|papal bull|encyclical|parable|female topic|women in|item that needs|report)\b",
    re.I,
)


def norm(s):
    s = unicodedata.normalize("NFD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c)).lower()
    return " ".join("".join(c if c.isalnum() else " " for c in s).split())


def val(b, k):
    v = b.get(k)
    return v["value"] if v else None


def wiki_title(t):
    return WIKI_SUFFIX.sub("", t).strip() if t else None


def open_post(url, data, timeout, hops=5):
    """POST that follows 307/308 redirects (urllib only follows them for GET)."""
    for _ in range(hops):
        req = urllib.request.Request(url, data=data, method="POST", headers={
            "User-Agent": UA,
            "Accept": "application/sparql-results+json",
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept-Encoding": "identity",
        })
        try:
            return urllib.request.urlopen(req, timeout=timeout)
        except urllib.error.HTTPError as e:
            loc = e.headers.get("Location")
            if e.code in (301, 302, 303, 307, 308) and loc:
                url = urllib.parse.urljoin(url, loc)
                print(f"  redirected ({e.code}) to {url}", flush=True)
                continue
            body = e.read()[:400].decode("utf-8", "replace")
            raise RuntimeError(f"HTTP {e.code}: {body}") from None
    raise RuntimeError("too many redirects")


def is_italian(langs, countries):
    """Italian title for books written in Italian (and not also English); when Wikidata lists no
    language, for books from Italy."""
    if ITALIAN_LANG in langs:
        return ENGLISH_LANG not in langs
    return not langs and ITALY in countries


def authors_of(names):
    names = [n.strip() for n in (names or "").split("|") if n.strip() and not BAD_TITLE.match(n.strip())]
    names = sorted(set(names), key=names.index)
    if not names:
        return ""
    if len(names) == 1:
        return names[0]
    if len(names) == 2:
        return f"{names[0]} & {names[1]}"
    return f"{names[0]} et al."


def run_query(sparql, timeout=180):
    """POST the query and stream the answer, printing progress so a stall shows up in the log."""
    data = urllib.parse.urlencode({"query": sparql}).encode()
    t0 = time.time()
    print(f"POST {ENDPOINT} ({len(data)} bytes of query)", flush=True)
    with open_post(ENDPOINT, data, timeout) as r:
        print(f"  HTTP {r.status} after {time.time() - t0:.1f}s, content-type {r.headers.get('Content-Type')}", flush=True)
        chunks, total, last = [], 0, 0
        while True:
            b = r.read(1 << 20)
            if not b:
                break
            chunks.append(b)
            total += len(b)
            if total - last >= 10 << 20:
                print(f"  {total >> 20} MB after {time.time() - t0:.0f}s", flush=True)
                last = total
    print(f"  done: {total / 1e6:.1f} MB in {time.time() - t0:.1f}s", flush=True)
    return json.loads(b"".join(chunks).decode("utf-8"))["results"]["bindings"]


def main(out_path, report_path):
    t0 = time.time()
    last_year = dt.date.today().year + 1
    log = []
    rows = None
    for attempt in range(4):
        try:
            rows = run_query(QUERY)
            break
        except Exception as e:  # timeouts, 5xx, connection resets
            wait = 20 * (attempt + 1)
            msg = f"attempt {attempt + 1}: {type(e).__name__}: {e}; retrying in {wait}s"
            print(msg, flush=True)
            log.append(msg)
            time.sleep(wait)
    if rows is None:
        raise SystemExit("QLever did not answer; keeping the previous catalog")
    log.append(f"{len(rows)} books returned in {time.time() - t0:.0f}s")

    out = []
    fixed_en = fixed_it = undated = no_author = 0
    dropped = {}
    types_seen = {}
    for b in rows:
        pop = int(float(val(b, "s") or 0))
        types = [t for t in (val(b, "types") or "").split("|") if t]
        bad = next((t for t in types if BAD_TYPE.search(t)), None)
        if bad:
            dropped[bad] = dropped.get(bad, 0) + 1
            continue
        if pop >= 10:
            for t in types:
                types_seen[t] = types_seen.get(t, 0) + 1
        # Long manga and comic series have articles in many languages thanks to their anime; count them at half
        # so single books are not crowded out of the browse lists (popularity is only used for ranking).
        if any("series" in t.lower() for t in types):
            pop = max(1, pop // 2)
        y = val(b, "y1") or val(b, "y2")
        year = int(float(y)) if y else None
        if year is not None and not (-3000 <= year <= last_year) or year == 0:
            continue
        if year is None:
            if pop < MIN_UNDATED:
                continue
            undated += 1
        langs = (val(b, "langs") or "").split()
        countries = (val(b, "countries") or "").split()
        italian = is_italian(langs, countries)
        it, en = val(b, "it"), val(b, "en")
        if not en and val(b, "enw"):
            en = wiki_title(val(b, "enw")); fixed_en += 1
        if not it and val(b, "itw"):
            it = wiki_title(val(b, "itw")); fixed_it += 1
        title = (it or en) if italian else (en or it)
        if not title or BAD_TITLE.match(title):
            continue
        # some Italian labels are all lower case ("il diavolaro")
        title = title[0].upper() + title[1:] if title[0].islower() else title
        author = authors_of(val(b, "auens")) or authors_of(val(b, "auits"))
        author_it = authors_of(val(b, "auits"))
        if not author:
            no_author += 1
        other = en if italian else it
        rec = [title, year, pop, author]
        alt = other if other and norm(other) != norm(title) else ""
        extra = author_it if author_it and norm(author_it) != norm(author) else ""
        if alt or extra:
            rec.append(alt)
        if extra:
            rec.append(extra)
        out.append(rec)

    # The same book can come back twice (two items for one work): keep the better-known copy.
    seen = set()
    dedup = []
    for r in sorted(out, key=lambda r: (-r[2], r[0])):
        k = (norm(r[0]), norm(r[3]))
        if k in seen:
            continue
        seen.add(k)
        dedup.append(r)
    out = dedup[:MAX_BOOKS]

    by_period = {}
    for r in out:
        y = r[1]
        p = "undated" if y is None else f"{y // 10 * 10}s" if y >= 1900 else f"{y // 100 * 100}s" if y >= 1500 else "before 1500"
        by_period[p] = by_period.get(p, 0) + 1
    pops = sorted((r[2] for r in out), reverse=True)
    report = [
        f"built {dt.datetime.utcnow().isoformat(timespec='seconds')}Z in {time.time() - t0:.0f}s from {ENDPOINT}",
        f"books kept: {len(out)} (min {MIN_SITELINKS} sites); English title from Wikipedia for {fixed_en}, Italian for {fixed_it}; "
        f"undated {undated}; no author {no_author}",
        "popularity cut-offs: " + ", ".join(f"top {n}: >= {pops[n - 1]}" for n in (1000, 10000, 30000, 50000, 80000) if len(pops) >= n),
        "per period: " + ", ".join(f"{p} {n}" for p, n in sorted(by_period.items(), key=lambda kv: kv[0])),
        "top: " + "; ".join(f"{r[0]} / {r[3]} ({r[1]})" for r in out[:40]),
        "dropped types: " + ", ".join(f"{t} {n}" for t, n in sorted(dropped.items(), key=lambda kv: -kv[1])[:40]),
        "common types (10+ sites): " + ", ".join(f"{t} {n}" for t, n in sorted(types_seen.items(), key=lambda kv: -kv[1])[:60]),
        "low-popularity sample: " + "; ".join(f"{r[0]} / {r[3]} ({r[1]}, {r[2]})" for r in out[-25:]),
        "--- log ---",
        *log,
    ]
    os.makedirs(os.path.dirname(report_path) or ".", exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(report) + "\n")
    print("\n".join(report))
    if len(out) < MIN_EXPECTED:
        raise SystemExit(f"only {len(out)} books: keeping the previous catalog")
    payload = {"v": 1, "built": dt.date.today().isoformat(), "source": "Wikidata (CC0) via QLever", "count": len(out), "books": out}
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, separators=(",", ":"))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "letto/catalog.json",
         sys.argv[2] if len(sys.argv) > 2 else "letto/catalog-report.txt")
