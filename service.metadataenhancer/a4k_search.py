"""a4kSubtitles' own background search + download, run as a separate script by the service.

Same steps a4k's service runs when auto-download is on, through a4k's public API (it binds to
a4k's settings by add-on id). A separate script, because importing a4k inside our long-running
service thread failed with ModuleNotFoundError while the same code works here.
"""
import sys
import traceback

import xbmc
import xbmcaddon
import xbmcvfs

LOG_TAG = "[service.metadataenhancer]"


def log(msg, level=xbmc.LOGINFO):
    xbmc.log("%s %s" % (LOG_TAG, msg), level)


def main():
    a4k = xbmcaddon.Addon("service.subtitles.a4ksubtitles")
    path = xbmcvfs.translatePath(a4k.getAddonInfo("path"))
    if path not in sys.path:
        sys.path.insert(0, path)
    from a4kSubtitles import api

    client = api.A4kSubtitlesApi()
    kodi = client.core.kodi
    params = {
        "action": "search",
        "languages": ",".join(kodi.get_kodi_setting("subtitles.languages")),
        "preferredlanguage": kodi.parse_language(kodi.get_kodi_setting("locale.subtitlelanguage")),
    }
    for result in client.search(params):
        subfile = client.download(result)
        if subfile:
            if xbmc.Player().isPlayingVideo():
                xbmc.Player().setSubtitles(subfile)
                log("a4k found and loaded a subtitle in the background")
            return
    log("a4k background search found no subtitle")


try:
    main()
except Exception:
    log("a4k background search failed: " + traceback.format_exc().splitlines()[-1], xbmc.LOGWARNING)
