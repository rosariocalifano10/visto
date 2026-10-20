# Letto

A private reading diary for your phone, the twin of Visto. A paper book or an e-reader on each entry, 1–5 stars with halves, the author, and a list of books you want to read.
It works offline, needs no account, and your entries never leave the phone unless you export them.

Address: **https://rosariocalifano10.github.io/visto/letto/** (it lives in the same repository as Visto, in the `letto/` folder).

## Install

**iPhone:** open the address in Safari → Share → **Add to Home Screen** → Add. Open Letto from the Home Screen icon and log books there; Safari and the Home Screen app keep separate diaries.

**Android:** open the address in Chrome → ⋮ menu → **Add to Home screen** (or **Install app**) → Install.

Letto and Visto are separate apps with separate diaries, even though they share a web address.

## The book list

About 65,000 books from Wikidata (public domain, CC0): every book, novel, play or poem with a page on at least two Wikimedia sites, plus every book with an Italian Wikipedia article. It is downloaded once (about 3.5 MB) and then works offline.

- Search by title in English or Italian, or by author ("calvino", "dostoevskij"), or mix the two ("barone calvino").
- Books written in Italian show their Italian title; everything else its English one, with the Italian title as an alternate.
- Browse shows the best-known books of each decade since 1900, each century before that, and the older classics.

GitHub rebuilds the list on the 1st of every month (`.github/workflows/books.yml` runs `tools/build_books.py`), so new books arrive by themselves. For anything newer, typing a title also asks Wikidata directly; only the text you type is sent. Turn that off in Settings → Online search.

## Backups

Settings → **Export backup** saves your diary and reading list as a file (Save to Files / iCloud Drive). **Import backup** merges a file back in; for an entry present in both, the more recently edited copy wins. Deleting the app from the Home Screen deletes its data, so export first.

## Updating the app

Replace `letto/index.html` in the repo and bump the version at the top of `letto/sw.js` (`letto-v1` → `letto-v2`). The installed app picks it up after you open it, close it and open it again. Your entries are untouched.
