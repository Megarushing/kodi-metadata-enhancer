# Metadata Enhancer for Kodi

Streamed videos often reach Kodi with no info: no title, no IMDb id, nothing. Subtitle add-ons then can't find subtitles, and the player shows odd titles like "history" or "play".

Metadata Enhancer fixes that in the background, for anything you play (torrent streams, debrid, plugins, local files).

## What it does

When a video starts, it:

1. **Fingerprints the file.** It computes the OpenSubtitles "movie hash" (file size + first and last 64 KB), even for streams.
2. **Shares the fingerprint** with subtitle add-ons that know how to use it: OpenSubtitles.com, SubSource and SubDL. They can then find subtitles made for your exact file.
3. **Fills in missing info.** It asks OpenSubtitles which movie or episode the fingerprint belongs to. Then it fills in **only the empty fields**: IMDb id, TMDb id, title, year, type, and show / season / episode. Anything already there is never changed.
4. **Retries a4kSubtitles.** a4kSubtitles needs an IMDb id. If the id was missing and has now been filled in, and a4k's auto-search is on, the search runs again in the background.

Nothing happens when OpenSubtitles doesn't know the file. The add-on never guesses from the file name.

## Install

1. Download the zip from [Releases](../../releases).
2. In Kodi: **Settings → Add-ons → Install from zip file** → pick the zip.

Needs Kodi 20 or newer (tested on Kodi 21, Android).

## Settings

- **Fill missing metadata**: on by default.
- **OpenSubtitles.com username / password**: optional. **Import** copies them from the OpenSubtitles.com add-on if you have it.
- **API key**: optional. The add-on ships its own key.

## Good to know

- Works best with popular releases. New or rare files are often not in the OpenSubtitles database yet.
- Kodi's "file name" label for plugin streams comes from the plugin link, not the real file. This add-on doesn't change that.

## License

MIT
