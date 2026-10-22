#!/usr/bin/env python3
"""Build mangiato/catalog.json, the restaurant list Mangiato searches, from OpenStreetMap.

Runs on GitHub Actions (.github/workflows/places.yml): on demand and on the 1st of each month.
Standard library only. Data: OpenStreetMap via the Overpass API.
Licence: the list is a derived database of OpenStreetMap, so it stays under the ODbL 1.0
(© OpenStreetMap contributors); the app shows that credit.

Output: {"v":1, "built":..., "count":N, "places":[[name, city, cuisine, lat, lon, score], ...]}
  - every named restaurant and fast-food place in Italy
  - city:    addr:city when mapped, otherwise the nearest town or village (weighted by size)
  - cuisine: up to two values, readable ("Pizza, Italian")
  - lat/lon: degrees x 10,000 as integers (about 10 m precision), for "near you"
  - score:   how completely the place is mapped (website, hours, phone, Wikidata...), used only to rank
"""
import csv
import datetime as dt
import io
import json
import math
import os
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request

ENDPOINTS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
]
UA = "MangiatoCatalog/1.0 (https://github.com/rosariocalifano10/visto; personal restaurant diary, monthly refresh)"
MIN_EXPECTED = 30000    # fewer than this means something broke: keep the previous catalog

PLACES_QUERY = """[out:csv(::type, ::id, ::lat, ::lon, name, "addr:city", "addr:place", cuisine, amenity,
  website, "contact:website", wikidata, opening_hours, phone, "contact:phone", "diet:vegetarian"; true; "\t")]
[timeout:900][maxsize:2147483648];
area["ISO3166-1"="IT"][admin_level=2]->.it;
nwr["amenity"~"^(restaurant|fast_food)$"]["name"](area.it);
out center;
"""

TOWNS_QUERY = """[out:csv(::lat, ::lon, name, place, population; true; "\t")][timeout:600];
area["ISO3166-1"="IT"][admin_level=2]->.it;
node["place"~"^(city|town|village)$"]["name"](area.it);
out;
"""

CUISINE = {
    "pizza": "Pizza", "italian": "Italian", "regional": "Regional", "italian_pizza": "Pizza",
    "japanese": "Japanese", "sushi": "Sushi", "chinese": "Chinese", "kebab": "Kebab", "burger": "Burger",
    "seafood": "Seafood", "fish": "Fish", "steak_house": "Steakhouse", "indian": "Indian", "mexican": "Mexican",
    "greek": "Greek", "thai": "Thai", "vietnamese": "Vietnamese", "korean": "Korean", "asian": "Asian",
    "chicken": "Chicken", "sandwich": "Sandwiches", "piadina": "Piadina", "friture": "Fried food",
    "ramen": "Ramen", "vegan": "Vegan", "vegetarian": "Vegetarian", "international": "International",
    "mediterranean": "Mediterranean", "french": "French", "spanish": "Spanish", "turkish": "Turkish",
    "american": "American", "brazilian": "Brazilian", "peruvian": "Peruvian", "argentinian": "Argentinian",
    "middle_eastern": "Middle Eastern", "lebanese": "Lebanese", "arab": "Arab", "african": "African",
    "ethiopian": "Ethiopian", "eritrean": "Eritrean", "moroccan": "Moroccan", "pasta": "Pasta",
    "grill": "Grill", "barbecue": "Barbecue", "meat": "Meat", "pub": "Pub", "bistro": "Bistro",
    "local": "Local", "coffee_shop": "Café", "ice_cream": "Gelato", "crepe": "Crêpes", "poke": "Poke",
    "hot_dog": "Hot dogs", "fine_dining": "Fine dining", "tapas": "Tapas", "georgian": "Georgian",
}


def norm(s):
    s = unicodedata.normalize("NFD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c)).lower()
    return " ".join("".join(c if c.isalnum() else " " for c in s).split())


def cuisine_label(raw):
    out = []
    for v in (raw or "").replace(",", ";").split(";"):
        v = v.strip().lower().replace(" ", "_")
        if not v:
            continue
        lab = CUISINE.get(v) or v.replace("_", " ").capitalize()
        if lab not in out:
            out.append(lab)
        if len(out) == 2:
            break
    return ", ".join(out)


def post(url, query, timeout):
    data = urllib.parse.urlencode({"data": query}).encode()
    req = urllib.request.Request(url, data=data, method="POST", headers={"User-Agent": UA, "Accept-Encoding": "identity"})
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=timeout) as r:
        chunks, total, last = [], 0, 0
        while True:
            b = r.read(1 << 20)
            if not b:
                break
            chunks.append(b)
            total += len(b)
            if total - last >= 5 << 20:
                print(f"  {total >> 20} MB after {time.time() - t0:.0f}s", flush=True)
                last = total
    print(f"  done: {total / 1e6:.1f} MB in {time.time() - t0:.0f}s", flush=True)
    return b"".join(chunks).decode("utf-8")


def run(query, label, log, timeout=960):
    for attempt in range(6):
        url = ENDPOINTS[attempt % len(ENDPOINTS)]
        try:
            print(f"{label}: POST {url}", flush=True)
            text = post(url, query, timeout)
            if "runtime error" in text[:2000] or "rate_limited" in text[:2000]:
                raise RuntimeError(text[:300].replace("\n", " "))
            rows = list(csv.DictReader(io.StringIO(text), delimiter="\t", quoting=csv.QUOTE_NONE))
            log.append(f"{label}: {len(rows)} rows from {url}")
            return rows
        except Exception as e:  # timeouts, 429/504, a busy server
            wait = 30 * (attempt + 1)
            msg = f"{label} attempt {attempt + 1} at {url}: {type(e).__name__}: {str(e)[:200]}; retrying in {wait}s"
            print(msg, flush=True)
            log.append(msg)
            time.sleep(wait)
    raise SystemExit(f"Overpass did not answer for {label}; keeping the previous catalog")


class Towns:
    """Nearest town for a point, scaled by size so a restaurant on Rome's outskirts says Roma, not the nearest hamlet."""

    def __init__(self, rows):
        self.grid = {}
        for r in rows:
            try:
                lat, lon = float(r["@lat"]), float(r["@lon"])
            except (TypeError, ValueError):
                continue
            name = (r.get("name") or "").strip()
            if not name:
                continue
            try:
                pop = float(re.sub(r"[^\d.]", "", r.get("population") or "") or 0)
            except ValueError:
                pop = 0
            if not pop:
                pop = {"city": 100000, "town": 10000}.get(r.get("place"), 1000)
            reach = 1.0 + 0.004 * math.sqrt(pop)  # km: village ~1.1, town of 30k ~1.7, Napoli ~4.8, Roma ~7.7
            key = (int(lat * 10), int(lon * 10))
            self.grid.setdefault(key, []).append((lat, lon, name, reach))

    def nearest(self, lat, lon):
        best, best_score = "", 1e9
        gy, gx = int(lat * 10), int(lon * 10)
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                for tlat, tlon, name, reach in self.grid.get((gy + dy, gx + dx), ()):
                    km = math.hypot((tlat - lat) * 111.2, (tlon - lon) * 111.2 * math.cos(math.radians(lat)))
                    score = km / reach
                    if score < best_score:
                        best, best_score = name, score
        return best


def main(out_path, report_path):
    t0 = time.time()
    log = []
    towns = Towns(run(TOWNS_QUERY, "towns", log, timeout=660))
    rows = run(PLACES_QUERY, "places", log)

    out = []
    seen = set()
    from_tag = from_town = no_city = 0
    cuisines, cities, kinds = {}, {}, {}
    for r in rows:
        name = " ".join((r.get("name") or "").split())
        try:
            lat, lon = float(r["@lat"]), float(r["@lon"])
        except (TypeError, ValueError, KeyError):
            continue
        if not name:
            continue
        key = (norm(name), round(lat, 3), round(lon, 3))  # the same place mapped as a point and a building
        if key in seen:
            continue
        seen.add(key)
        city = " ".join((r.get("addr:city") or "").split())
        if city:
            from_tag += 1
        else:
            city = towns.nearest(lat, lon) or " ".join((r.get("addr:place") or "").split())
            if city:
                from_town += 1
            else:
                no_city += 1
        cuisine = cuisine_label(r.get("cuisine"))
        score = (5 if r.get("wikidata") else 0) + (2 if (r.get("website") or r.get("contact:website")) else 0) \
            + (1 if r.get("opening_hours") else 0) + (1 if (r.get("phone") or r.get("contact:phone")) else 0) \
            + (1 if cuisine else 0)
        out.append([name, city, cuisine, round(lat * 1e4), round(lon * 1e4), score])
        for c in cuisine.split(", "):
            if c:
                cuisines[c] = cuisines.get(c, 0) + 1
        cities[city] = cities.get(city, 0) + 1
        kinds[r.get("amenity")] = kinds.get(r.get("amenity"), 0) + 1
    out.sort(key=lambda r: (-r[5], norm(r[1]), norm(r[0])))

    payload = {"v": 1, "built": dt.date.today().isoformat(), "source": "OpenStreetMap via Overpass API",
               "license": "ODbL 1.0, (c) OpenStreetMap contributors", "count": len(out), "places": out}
    text = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    report = [
        f"built {dt.datetime.utcnow().isoformat(timespec='seconds')}Z in {time.time() - t0:.0f}s",
        f"places kept: {len(out)} ({', '.join(f'{k} {v}' for k, v in kinds.items())}); "
        f"city from address {from_tag}, from nearest town {from_town}, none {no_city}; file {len(text.encode()) / 1e6:.1f} MB",
        "top cities: " + ", ".join(f"{c} {n}" for c, n in sorted(cities.items(), key=lambda kv: -kv[1])[:30]),
        "top cuisines: " + ", ".join(f"{c} {n}" for c, n in sorted(cuisines.items(), key=lambda kv: -kv[1])[:40]),
        "sample: " + "; ".join(f"{r[0]} / {r[1]} / {r[2]}" for r in out[:15]),
        "--- log ---",
        *log,
    ]
    os.makedirs(os.path.dirname(report_path) or ".", exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(report) + "\n")
    print("\n".join(report))
    if len(out) < MIN_EXPECTED:
        raise SystemExit(f"only {len(out)} places: keeping the previous catalog")
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write(text)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "mangiato/catalog.json",
         sys.argv[2] if len(sys.argv) > 2 else "mangiato/catalog-report.txt")
