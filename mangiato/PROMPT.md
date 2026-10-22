# Mangiato — a personal restaurant diary (Visto's twin, for restaurants)

## Goal
A private log of every meal out (or takeaway): the place, city, cuisine, whether I ate in or took it away, what it cost per person, and 1–5 stars in half steps. Quick to add, effortless to edit, good-looking enough that I enjoy opening it.

## Platform
- Home Screen web app: plain HTML/CSS/JS, no frameworks.
- Works offline after the first load. No accounts, no analytics.
- Restaurant list: every named restaurant and fast-food place in Italy from OpenStreetMap (ODbL), in `catalog.json`, cached for offline use and rebuilt monthly by a GitHub Action (Overpass API, one region at a time). Searchable by name, city and cuisine; "near you" from the phone's location, computed on the phone.
- Optional online search (Photon by komoot, OpenStreetMap data) for places abroad or missing from the list: only the typed text and a rough area (one decimal of latitude/longitude) are sent.
- Data lives only on the phone, with persistent storage requested. JSON export/import for backups.
- Hosted on GitHub Pages next to Visto (`/visto/mangiato/`); separate storage keys and caches.

## Data
One entry per visit; going back is a new entry ("Been 2×"). Fields: name, city, cuisine, € per person (optional), date (defaults to today, can be blank), how (dine in / takeaway / unknown), stars 0–5 in half steps (0 = unrated), note.

## Screens
1. **Diary** — visits grouped by month. Each row: dine-in/takeaway icon, name, city, cuisine, price, date, stars. Search (name, city, cuisine, note), filters (All / Dine in / Takeaway / Unrated), sort (recent / stars / name / city, grouped by city), header stats (visits, this year, average stars), visit count per place.
2. **Add / Edit sheet** — name with autocomplete from the list (nearest first) plus OpenStreetMap online; picking one fills city and cuisine. Dine in / takeaway toggle, stars (left half of a star = ½, slide across, tap again to clear), date, € per person, note. Edits save as you type. Delete with undo.
3. **Been there? picker** — with location on, the places around you in rings (500 m, 1 km, 3 km, 10 km, 25 km); otherwise search by name, city or cuisine. Tick the ones you've been to and add them in one go; they arrive unrated and undated.
4. **To try** — a second tab for places you want to try: name, city, cuisine, note, date added; sort by added / name / city. "Been there" opens the log sheet prefilled and moves the place into the diary.
5. **Settings** — appearance (System / Light / Dark), online search on/off, export/import backup, add from the list, erase all.

## Look
Trattoria-inspired, same layout as Visto and Letto. A wine-red band at the top edged with a red-and-white gingham tablecloth; each visit is a receipt stub whose colour says how you ate (olive for dine in, orange for takeaway, grey when not set). Playfair Display for names, a receipt-printer mono for dates and labels, system sans for everything else; gold stars. Light (linen) and dark (espresso) modes.

## Done when
It works in airplane mode, survives closing and restarting, and an export file restores everything on a fresh install.
