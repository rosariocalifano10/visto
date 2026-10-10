# Visto

A private film diary for iPhone. Popcorn = seen at the cinema, laptop = seen at home, 1–5 stars.
It works offline, needs no account, and your entries never leave the phone unless you export them.

## 1. Put it online once (free, GitHub Pages)

The app's code has to live at an `https://` address so Safari can install it. Your diary does not go there: it stays in the app's storage on your phone. The code is public; your entries are not.

1. Sign in (or sign up, free) at github.com and create a new repository called `visto`. Leave it **Public** (free Pages needs that).
2. On the empty repo page, choose **uploading an existing file** and drop in every file from this folder: `index.html`, `manifest.webmanifest`, `sw.js`, `icon-180.png`, `icon-192.png`, `icon-512.png` (the `.md` files are optional). Commit.
   On iPhone this works too: unzip in the Files app, then in Safari use **Request Desktop Website** on GitHub to get the upload button.
3. Go to **Settings → Pages**. Under *Build and deployment* pick **Deploy from a branch**, branch `main`, folder `/ (root)`, then **Save**.
4. After a minute the site is live at `https://YOUR-USERNAME.github.io/visto/`.

## 2. Install on your iPhone

1. Open that address in **Safari**.
2. Tap **Share → Add to Home Screen → Add**.
3. Open Visto from the Home Screen icon and log films there.

Safari and the Home Screen app keep **separate** storage, so anything typed in the Safari tab won't appear in the installed app. Install first, then log.

## Online search

When you type a title, Visto also looks it up on Wikidata (free, no account), so new releases and films outside the built-in list show up. Only the text you type is sent. Turn it off in Settings → Online search; without a connection the app uses its built-in list of 647 films.

## Backups

Settings → **Export backup** opens the share sheet: choose *Save to Files* (iCloud Drive is a good place).
Settings → **Import backup** merges a backup into what's on the phone; for an entry present in both, the more recently edited copy wins.

Deleting the Visto icon from the Home Screen deletes its data. Export before you do that, or before resetting the phone.

## Updating the app

Replace `index.html` in the repo and change `visto-v1` to `visto-v2` at the top of `sw.js`. The installed app downloads the new version in the background and uses it from the next launch. Your entries are untouched.
