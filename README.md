# Visto

A private film diary for iPhone. Popcorn = seen at the cinema, laptop = seen at home, 1–5 stars with halves, plus a watchlist of films you want to see.
It works offline, needs no account, and your entries never leave the phone unless you export them.

## 1. Put it online once (free, GitHub Pages)

The app's code has to live at an `https://` address so Safari can install it. Your diary does not go there: it stays in the app's storage on your phone. The code is public; your entries are not.

1. Sign in (or sign up, free) at github.com and create a new repository called `visto`. Leave it **Public** (free Pages needs that).
2. On the empty repo page, choose **uploading an existing file** and drop in every file from this folder: `index.html`, `manifest.webmanifest`, `sw.js`, `catalog.json`, `icon-180.png`, `icon-192.png`, `icon-512.png` (the `.md` files are optional). Commit.
   On iPhone this works too: unzip in the Files app, then in Safari use **Request Desktop Website** on GitHub to get the upload button.
3. Go to **Settings → Pages**. Under *Build and deployment* pick **Deploy from a branch**, branch `main`, folder `/ (root)`, then **Save**.
4. After a minute the site is live at `https://YOUR-USERNAME.github.io/visto/`.

## 2. Install on your iPhone

1. Open that address in **Safari**.
2. Tap **Share → Add to Home Screen → Add**.
3. Open Visto from the Home Screen icon and log films there.

Safari and the Home Screen app keep **separate** storage, so anything typed in the Safari tab won't appear in the installed app. Install first, then log.

## The film list

Visto searches a list of about 77,000 films built from Wikidata (public domain, CC0): every film with an article in at least 5 Wikipedia languages. It lives in `catalog.json`, is downloaded once (about 3 MB) and then works offline.
Search finds films by their English or Italian title. Italian films show their Italian title, everything else its English one.

The list rebuilds itself on the 1st of every month (`.github/workflows/catalog.yml` runs `tools/build_catalog.py` and commits the new `catalog.json`), so new releases arrive without any work. To refresh it now: repo → **Actions → Refresh film catalog → Run workflow**.

IMDb isn't used: its datasets are licensed for personal, non-commercial use and may not be republished, which a public site would do.

## Online search

For anything not in the list yet (a film out this week, an obscure short), typing a title also asks Wikidata directly. Only the text you type is sent. Turn it off in Settings → Online search.

## Backups

Backups include both the diary and the watchlist. Settings → **Export backup** opens the share sheet: choose *Save to Files* (iCloud Drive is a good place).
Settings → **Import backup** merges a backup into what's on the phone; for an entry present in both, the more recently edited copy wins.

Deleting the Visto icon from the Home Screen deletes its data. Export before you do that, or before resetting the phone.

## Updating the app

Replace `index.html` in the repo and bump the version at the top of `sw.js` (`visto-v6` → `visto-v7`). The installed app downloads the new version in the background and uses it from the next launch. Your entries are untouched.
