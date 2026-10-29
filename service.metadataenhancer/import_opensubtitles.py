"""Copy username and password from the OpenSubtitles.com subtitle add-on.

Values go add-on to add-on inside Kodi and are never logged.
"""
import xbmc
import xbmcaddon
import xbmcgui

SOURCE = "service.subtitles.opensubtitles-com"
# their APIKey is that add-on's own app key, not the user's - this add-on ships its own
MAPPING = {"OSuser": "os_username", "OSpass": "os_password"}


def main():
    me = xbmcaddon.Addon("service.metadataenhancer")
    try:
        src = xbmcaddon.Addon(SOURCE)
    except RuntimeError:
        xbmcgui.Dialog().notification("Metadata Enhancer", "OpenSubtitles.com add-on not installed",
                                      xbmcgui.NOTIFICATION_WARNING)
        return
    copied = []
    for theirs, ours in MAPPING.items():
        value = src.getSetting(theirs)
        if value:
            me.setSetting(ours, value)
            copied.append(ours)
    xbmc.log("[service.metadataenhancer] imported from %s: %s" % (SOURCE, ", ".join(copied) or "nothing"),
             xbmc.LOGINFO)
    xbmcgui.Dialog().notification("Metadata Enhancer", "Imported %d of %d settings" % (len(copied), len(MAPPING)))


main()
