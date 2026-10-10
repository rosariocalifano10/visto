# Visto — a personal film diary for iPhone

## Goal
A private log of every film I watch: title, where I saw it (popcorn = cinema, laptop = home), and 1–5 stars in half steps. Quick to add, effortless to edit, good-looking enough that I enjoy opening it.

## Platform
- Home Screen web app: plain HTML/CSS/JS, no frameworks, no build step.
- Works offline after the first load. No accounts, no analytics.
- Optional online title search on Wikidata (on by default, switchable in Settings): only the typed title is sent, the diary never leaves the phone. Without a connection it falls back to the built-in list.
- Data lives only on the phone, with persistent storage requested. JSON export/import for backups.
- Code hosted once on free static hosting (GitHub Pages). The hosted code contains no personal data.

## Data
One entry per viewing; a rewatch is a new entry. Fields: title, year (optional), date watched (defaults to today, can be blank), venue (cinema / home / unknown), stars 0–5 in half steps (0 = unrated), note.

## Screens
1. **Diary** — entries grouped by month. Each row: venue icon, title, year, date, stars. Search, filters (All / Cinema / Home / Unrated), sort (recent / stars / title), header stats (total, this year, average stars), rewatch count.
2. **Add / Edit sheet** — title with autocomplete from a bundled film catalog plus Wikidata, popcorn/laptop toggle, stars: tap a star (left half = ½) or slide across them, tap the same value to clear, date, note. Edits save as you type. Delete with undo.
3. **Already seen? picker** — several hundred well-known films grouped by decade; its search also queries Wikidata so any film can be found. Tick the ones you've seen and add them in one go; they arrive unrated with venue unknown.
4. **Watchlist** — a second tab (bottom bar: Diary / Watchlist) for films I want to see: title, year, note, date added; sort by added / title / year. "Seen it" opens the log sheet prefilled and moves the film into the diary; logging a film any other way also takes it off the watchlist. Can be filled from the same 647-film list.
5. **Settings** — appearance (System / Light / Dark), online search on/off, export/import backup, add from the list, erase all.

## Interaction rules
- Rate a film and switch cinema/home straight from the list, without opening it.
- Swipe left on a row to delete; 5-second undo.
- Adding a film: + → type → pick suggestion → stars → done.

## Catalog conventions
English titles for English-language films, Italian titles for everything else.

## Look
Cinema-inspired. A dark marquee band with a row of bulbs at the top; each diary entry is a ticket stub whose colour says where you watched it (popcorn-bucket red for cinema, screen blue for home, grey when not set). Condensed marquee type for titles, a ticket-printer mono for dates and labels, system sans for everything else. Light and dark modes, bottom sheets, safe-area aware, 44pt tap targets.

## Done when
It works in airplane mode, survives closing and restarting, and an export file restores everything on a fresh install.
