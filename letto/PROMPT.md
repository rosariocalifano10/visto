# Letto — a personal reading diary (Visto's twin, for books)

## Goal
A private log of every book I read: title, author, format (paper book or e-reader), and 1–5 stars in half steps. Quick to add, effortless to edit, good-looking enough that I enjoy opening it.

## Platform
- Home Screen web app: plain HTML/CSS/JS, no frameworks, no build step at runtime.
- Works offline after the first load. No accounts, no analytics.
- Book list: about 65,000 books from Wikidata (CC0) in `catalog.json`, cached for offline use and rebuilt monthly by a GitHub Action. Searchable by English or Italian title and by author. (Not Goodreads/Amazon data: not openly licensed.)
- Optional online title search on Wikidata (on by default, switchable in Settings) for books not in the list yet: only the typed text is sent.
- Data lives only on the phone, with persistent storage requested. JSON export/import for backups.
- Hosted on GitHub Pages next to Visto (`/visto/letto/`); separate storage keys and caches, so the two never touch each other's data.

## Data
One entry per reading; a reread is a new entry. Fields: title, author, publication year (optional, negative = BC), date finished (defaults to today, can be blank), format (paper / e-book / unknown), stars 0–5 in half steps (0 = unrated), note.

## Screens
1. **Diary** — entries grouped by month. Each row: format icon, title, author, year, date, stars. Search (title, author, note), filters (All / Paper / E-book / Unrated), sort (recent / stars / title / author), header stats (total, this year, average stars), reread count.
2. **Add / Edit sheet** — title with autocomplete from the book list plus Wikidata (picking a suggestion fills author and year), author, paper/e-book toggle, stars: tap a star (left half = ½) or slide across them, tap the same value to clear, date finished, year published, note. Edits save as you type. Delete with undo.
3. **Read it? picker** — the best-known books of each period to browse (decades since 1900, centuries before), and a search over the whole list (Wikidata as a last resort). Tick the ones you've read and add them in one go; they arrive unrated with format unknown.
4. **To read** — a second tab for books I want to read: title, author, year, note, date added; sort by added / title / author. "Read it" opens the log sheet prefilled and moves the book into the diary; logging a book any other way also takes it off the list. Can be filled from the same book list.
5. **Settings** — appearance (System / Light / Dark), online search on/off, export/import backup, add from the list, erase all.

## Interaction rules
- Rate a book and switch paper/e-book straight from the list, without opening it.
- Swipe left on a row to delete; 5-second undo.
- Adding a book: + → type → pick suggestion → stars → done.

## Catalog conventions
Italian title for books written in Italian, English title for everything else, the other kept as an alternate so either finds the book. Authors' Italian spellings (Dostoevskij, Tolstoj) are searchable too.

## Look
Library-inspired, same layout as Visto. A deep bottle-green band at the top with a shelf of book spines; each diary entry is a library-card stub whose colour says the format (terracotta for paper, teal for e-reader, grey when not set). Fraunces serif for titles, a typewriter mono for dates and labels, system sans for everything else; brass stars. Light (paper cream) and dark (green-black) modes, bottom sheets, safe-area aware, 44pt tap targets.

## Done when
It works in airplane mode, survives closing and restarting, and an export file restores everything on a fresh install.
