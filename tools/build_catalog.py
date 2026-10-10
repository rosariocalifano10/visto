#!/usr/bin/env python3
"""Build catalog.json for Visto from Wikidata (public domain, CC0).

Runs on GitHub Actions (.github/workflows/catalog.yml): on demand and on the 1st of each month,
so new releases appear without touching the app. Standard library only.

Data comes from QLever (University of Freiburg), a fast public SPARQL endpoint over Wikidata;
the main Wikidata query service times out on a query this size.

Output: catalog.json  {"v":1, "built":..., "count":N, "films":[[title, year, popularity, alt?], ...]}
  - title: Italian title for Italian films (made in Italy, in Italian), English title for everything else
  - alt:   the other-language title when it differs, so searching either name finds the film
  - popularity: number of Wikipedia language editions with an article on the film
"""
import datetime as dt
import json
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request

ENDPOINT = "https://qlever.cs.uni-freiburg.de/api/wikidata"
UA = "VistoCatalog/1.0 (https://github.com/rosariocalifano10/visto; personal film diary, monthly refresh)"
MIN_SITELINKS = 5       # a film needs an article in at least this many Wikipedia languages
MAX_FILMS = 80000       # keep the most widely covered films if there are more
MIN_EXPECTED = 20000    # fewer than this means something broke: keep the previous catalog
ITALIAN_LANG = "http://www.wikidata.org/entity/Q652"
ITALY = "http://www.wikidata.org/entity/Q38"
ENGLISH_LANG = "http://www.wikidata.org/entity/Q1860"
US = "http://www.wikidata.org/entity/Q30"
UK = "http://www.wikidata.org/entity/Q145"

QUERY = """PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
PREFIX wikibase: <http://wikiba.se/ontology#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
PREFIX schema: <http://schema.org/>
SELECT ?film (MAX(?s0) AS ?s) (MIN(YEAR(?d)) AS ?y)
       (SAMPLE(?it0) AS ?it) (SAMPLE(?en0) AS ?en) (SAMPLE(?itw0) AS ?itw) (SAMPLE(?enw0) AS ?enw)
       (GROUP_CONCAT(DISTINCT STR(?lang); SEPARATOR=" ") AS ?langs)
       (GROUP_CONCAT(DISTINCT STR(?country); SEPARATOR=" ") AS ?countries)
WHERE {
  ?film wdt:P31/wdt:P279* wd:Q11424 ;
        wikibase:sitelinks ?s0 ;
        wdt:P577 ?d .
  FILTER(xsd:integer(?s0) >= %d)
  OPTIONAL { ?film wdt:P364 ?lang }
  OPTIONAL { ?film wdt:P495 ?country }
  OPTIONAL { ?film rdfs:label ?it0 FILTER(LANG(?it0) = "it") }
  OPTIONAL { ?film rdfs:label ?en0 FILTER(LANG(?en0) = "en") }
  OPTIONAL { ?a1 schema:about ?film ; schema:isPartOf <https://it.wikipedia.org/> ; schema:name ?itw0 }
  OPTIONAL { ?a2 schema:about ?film ; schema:isPartOf <https://en.wikipedia.org/> ; schema:name ?enw0 }
}
GROUP BY ?film
""" % MIN_SITELINKS

# "Parasite (2019 film)" -> "Parasite", "La grande bellezza (film)" -> "La grande bellezza"
WIKI_SUFFIX = re.compile(r"\s*\((?:[^()]*\b(?:film|movie|documentary|documentario|animated|anime)\b[^()]*|\d{4})\)$", re.I)


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
            body = e.read()[:300].decode("utf-8", "replace")
            raise RuntimeError(f"HTTP {e.code}: {body}") from None
    raise RuntimeError("too many redirects")


def is_italian(langs, countries):
    """Italian title for films in Italian (not English), or in both languages but made in Italy
    without the US or UK. The Godfather lists Italy and Italian too, but is American."""
    has_it = ITALIAN_LANG in langs
    has_en = ENGLISH_LANG in langs
    anglo = US in countries or UK in countries
    if has_it and not has_en:
        return True
    if ITALY in countries and not anglo:
        return has_it or not langs
    return False


def run_query(sparql, timeout=120):
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
    last_year = dt.date.today().year + 2
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
    log.append(f"{len(rows)} films returned in {time.time() - t0:.0f}s")

    out = []
    fixed_en = fixed_it = 0
    for b in rows:
        y = val(b, "y")
        if not y:
            continue
        year = int(float(y))
        if not (1880 <= year <= last_year):
            continue
        langs = (val(b, "langs") or "").split()
        countries = (val(b, "countries") or "").split()
        italian = is_italian(langs, countries)
        it, en = val(b, "it"), val(b, "en")
        if not en and val(b, "enw"):
            en = wiki_title(val(b, "enw")); fixed_en += 1
        if not it and val(b, "itw"):
            it = wiki_title(val(b, "itw")); fixed_it += 1
        title = (it or en) if italian else (en or it)
        if not title:
            continue
        other = en if italian else it
        rec = [title, year, int(float(val(b, "s")))]
        if other and norm(other) != norm(title):
            rec.append(other)
        out.append(rec)
    out.sort(key=lambda r: (-r[2], r[0]))
    out = out[:MAX_FILMS]

    by_decade = {}
    for r in out:
        d = r[1] // 10 * 10
        by_decade[d] = by_decade.get(d, 0) + 1
    report = [
        f"built {dt.datetime.utcnow().isoformat(timespec='seconds')}Z in {time.time() - t0:.0f}s from {ENDPOINT}",
        f"films kept: {len(out)} (min {MIN_SITELINKS} Wikipedia languages); English title from Wikipedia for {fixed_en}, Italian for {fixed_it}",
        "per decade: " + ", ".join(f"{d}s {n}" for d, n in sorted(by_decade.items())),
        "top: " + "; ".join(f"{r[0]} ({r[1]})" for r in out[:20]),
        "--- log ---",
        *log,
    ]
    with open(report_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(report) + "\n")
    print("\n".join(report))
    if len(out) < MIN_EXPECTED:
        raise SystemExit(f"only {len(out)} films: keeping the previous catalog")
    payload = {"v": 1, "built": dt.date.today().isoformat(), "source": "Wikidata (CC0) via QLever", "count": len(out), "films": out}
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, separators=(",", ":"))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "catalog.json",
         sys.argv[2] if len(sys.argv) > 2 else "catalog-report.txt")
