# Mangiato

A private restaurant diary for your phone, the third of the family after Visto (films) and Letto (books). Each visit gets dine-in or takeaway, 1–5 stars with halves, the city, the cuisine and what you spent; plus a list of places you want to try.
It works offline, needs no account, and your entries never leave the phone unless you export them.

Address: **https://rosariocalifano10.github.io/visto/mangiato/** (it lives in the same repository as Visto, in the `mangiato/` folder).

## Install

**iPhone:** open the address in Safari → Share → **Add to Home Screen** → Add. Open Mangiato from the Home Screen icon and log visits there; Safari and the Home Screen app keep separate diaries.

**Android:** open the address in Chrome → ⋮ menu → **Add to Home screen** (or **Install app**) → Install.

Mangiato, Letto and Visto are separate apps with separate diaries, even though they share a web address.

## The restaurant list

Every named restaurant and fast-food place in Italy on OpenStreetMap, downloaded once and then available offline.

- **Been there?** shows the places around you, nearest first, when you allow location. Your position stays on the phone.
- Search by name ("da michele"), city ("salerno"), cuisine ("sushi"), or a mix ("sushi milano"). With location on, the nearest come first.
- Abroad, or for a place too new for the list, typing a name also searches OpenStreetMap online through Photon (komoot). Only what you type and your rough area (about 10 km) are sent. Turn it off in Settings → Online search.

GitHub rebuilds the list on the 1st of every month (`.github/workflows/places.yml` runs `tools/build_places.py`).
Restaurant data © OpenStreetMap contributors, available under the Open Database License (ODbL); the list in `catalog.json` stays under the same licence. Anyone can add or fix a restaurant at openstreetmap.org and it will reach the app with the next monthly refresh.

## Backups

Settings → **Export backup** saves your diary and To try list as a file (Save to Files / iCloud Drive). **Import backup** merges a file back in; for an entry present in both, the more recently edited copy wins. Deleting the app from the Home Screen deletes its data, so export first.

## Updating the app

Replace `mangiato/index.html` in the repo and bump the version at the top of `mangiato/sw.js` (`mangiato-v1` → `mangiato-v2`). The installed app picks it up after you open it, close it and open it again. Your entries are untouched.
