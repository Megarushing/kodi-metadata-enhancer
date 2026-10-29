import json
import threading
from urllib.parse import unquote

import xbmc
import xbmcaddon
import xbmcgui
import xbmcvfs

from resources.lib import enrich, opensubtitles, oshash

ADDON_ID = "service.metadataenhancer"
A4K_ID = "service.subtitles.a4ksubtitles"
OS_API_KEY = "flisTX7xOzAUEofBDs6hvXJjyubgb0iR"  # this add-on's own OpenSubtitles.com consumer (MetadataEnhancer)
A4K_GRACE = 10  # seconds a4k's own auto-search gets before we re-run it

# Home-window properties read by OpenSubtitles.com, SubSource and SubDL (file_operations.py)
PROP_PATH = "videoinfo.current_path"
PROP_SIZE = "videoinfo.current_size"
PROP_HASH = "videoinfo.current_oshash"
PROP_FILENAME = "MetadataEnhancer.Filename"  # real file name for skins; Player.Filename is the plugin link (e.g. "history")
LOG_TAG = "[service.metadataenhancer]"


def log(msg, level=xbmc.LOGINFO):
    xbmc.log("%s %s" % (LOG_TAG, msg), level)


class _VfsFile:
    """xbmcvfs.File reads short over http: loop until n bytes or EOF."""

    def __init__(self, path):
        self.f = xbmcvfs.File(path)

    def size(self):
        return self.f.size()

    def read(self, n):
        out = b""
        while len(out) < n:
            chunk = self.f.readBytes(n - len(out))
            if not chunk:
                break
            out += bytes(chunk)
        return out

    def seek(self, pos):
        self.f.seek(pos, 0)

    def close(self):
        self.f.close()


def _apply(item, changes):
    tag = item.getVideoInfoTag()
    setters = {
        "title": tag.setTitle, "originaltitle": tag.setOriginalTitle, "year": tag.setYear,
        "mediatype": tag.setMediaType, "tvshowtitle": tag.setTvShowTitle,
        "season": tag.setSeason, "episode": tag.setEpisode, "label": item.setLabel,
    }
    for field, value in changes.items():
        if field == "imdb":
            tag.setIMDBNumber(value)
            tag.setUniqueID(value, "imdb")
        elif field == "tmdb":
            tag.setUniqueID(value, "tmdb")
        else:
            setters[field](value)


def _preferred_subtitle_languages():
    """Kodi's 'Languages to download subtitles for' as ISO 639-2 codes (what subtitle streams report)."""
    res = json.loads(xbmc.executeJSONRPC(json.dumps(
        {"jsonrpc": "2.0", "id": 1, "method": "Settings.GetSettingValue",
         "params": {"setting": "subtitles.languages"}})))
    names = (res.get("result") or {}).get("value") or []
    return {xbmc.convertLanguage(n, xbmc.ISO_639_2) for n in names} - {""}


def file_name(path):
    """Last path part of a file path or URL, URL-decoded, without query string or credentials."""
    return unquote(path.split("?", 1)[0].rstrip("/").rsplit("/", 1)[-1])


def _redact(path):
    # the log may be shared; keep only the file name, never a query string or credentials
    return file_name(path)


class Player(xbmc.Player):
    def __init__(self):
        super().__init__()
        self.home = xbmcgui.Window(10000)
        self.generation = 0
        self.lock = threading.Lock()

    def clear(self):
        with self.lock:
            self.generation += 1
        for p in (PROP_PATH, PROP_SIZE, PROP_HASH, PROP_FILENAME):
            self.home.clearProperty(p)

    def onAVStarted(self):
        self.clear()
        try:
            if not self.isPlayingVideo():
                return
            path = self.getPlayingFile()
        except RuntimeError:
            return
        name = file_name(path)
        if name:
            self.home.setProperty(PROP_FILENAME, name)
        with self.lock:
            gen = self.generation
        threading.Thread(target=self._publish, args=(gen, path), daemon=True).start()

    def _publish(self, gen, path):
        try:
            size, h = oshash.hash_file(path, _VfsFile)
        except Exception as e:
            log("hash failed for %s: %s" % (_redact(path), type(e).__name__), xbmc.LOGWARNING)
            return
        with self.lock:
            if gen != self.generation:
                return  # playback changed while hashing
            # all three together: subtitle add-ons stop looking once any one is set
            self.home.setProperty(PROP_PATH, path)
            if size:
                self.home.setProperty(PROP_SIZE, str(size))
            if h:
                self.home.setProperty(PROP_HASH, h)
        log("%s size=%s oshash=%s" % (_redact(path), size, h))
        if h:
            self._enrich(gen, h)

    def _current(self, item):
        tag = item.getVideoInfoTag()
        return {
            "imdb": xbmc.getInfoLabel("VideoPlayer.IMDBNumber") or tag.getIMDBNumber() or tag.getUniqueID("imdb"),
            "tmdb": tag.getUniqueID("tmdb"),
            "title": tag.getTitle(),
            "originaltitle": tag.getOriginalTitle(),
            "label": item.getLabel(),
            "year": tag.getYear(),
            "mediatype": tag.getMediaType(),
            "tvshowtitle": tag.getTVShowTitle(),
            "season": tag.getSeason(),
            "episode": tag.getEpisode(),
        }

    def _enrich(self, gen, h):
        """Fill the playing item's EMPTY metadata fields from an exact OpenSubtitles hash match."""
        addon = xbmcaddon.Addon(ADDON_ID)
        if addon.getSetting("imdb_lookup") != "true":
            return
        try:
            if not enrich.wanted(self._current(self.getPlayingItem())):
                return
        except RuntimeError:
            return
        api_key = addon.getSetting("os_api_key") or OS_API_KEY
        client = opensubtitles.Client(api_key, "MetadataEnhancer v" + addon.getAddonInfo("version"),
                                      addon.getSetting("os_username"), addon.getSetting("os_password"))
        try:
            feature = client.feature_by_hash(h)
        except Exception as e:
            log("OpenSubtitles lookup failed: %s" % type(e).__name__, xbmc.LOGWARNING)
            return
        if not feature:
            log("OpenSubtitles lookup: no exact hash match for %s" % h)
            return
        with self.lock:
            if gen != self.generation:
                return
            try:
                item = self.getPlayingItem()
                changes = enrich.plan(self._current(item), feature)
                if not changes:
                    return
                _apply(item, changes)
                self.updateInfoTag(item)
            except RuntimeError:
                return
        log("filled from hash %s: %s" % (h, ", ".join("%s=%s" % kv for kv in sorted(changes.items()))))
        if "imdb" in changes:
            self._rerun_a4k(gen)

    def _rerun_a4k(self, gen):
        """a4k's auto-search checks once per video and skips it when the IMDb id is missing. The
        hash lookup can land before or after that check, so give a4k A4K_GRACE seconds first, then
        re-run the search only if a4k has auto-search on and there is still no subtitle in a
        preferred language."""
        try:
            a4k = xbmcaddon.Addon(A4K_ID)
        except RuntimeError:
            return  # a4k not installed or disabled
        if a4k.getSetting("general.auto_search") != "true":
            return
        if xbmc.Monitor().waitForAbort(A4K_GRACE):
            return
        with self.lock:
            if gen != self.generation:
                return
        try:
            if not self.isPlayingVideo():
                return
        except RuntimeError:
            return
        wanted = _preferred_subtitle_languages()
        have = set(self.getAvailableSubtitleStreams())
        if wanted & have:
            return
        # mirror a4k's own service: auto-download on -> silent search + load, off -> open the dialog
        if a4k.getSetting("general.auto_download") != "true":
            xbmc.executebuiltin("ActivateWindow(SubtitleSearch)")
            log("opened the subtitle search for a4k (a4k auto-download is off)")
            return
        xbmc.executebuiltin("RunScript(special://home/addons/%s/a4k_search.py)" % ADDON_ID)
        log("re-ran a4k's background subtitle search")

    def onPlayBackStopped(self):
        self.clear()

    def onPlayBackEnded(self):
        self.clear()

    def onPlayBackError(self):
        self.clear()


def run():
    monitor = xbmc.Monitor()
    player = Player()
    log("started")
    monitor.waitForAbort()
    player.clear()
    log("stopped")
