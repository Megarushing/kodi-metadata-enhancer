"""Decide which empty fields of the playing item to fill from an OpenSubtitles feature.

Pure logic (no Kodi imports) so it is unit-testable. A field is only ever filled when the
current value is empty/unset; nothing that is already there gets overwritten.
"""
from resources.lib.opensubtitles import imdb_tt

FIELDS = ("imdb", "tmdb", "title", "originaltitle", "label", "year", "mediatype",
          "tvshowtitle", "season", "episode")


def is_empty(value):
    # Kodi reports unset year as 0 and unset season/episode as -1 (or 0)
    return value in (None, "", 0, -1)


def wanted(current):
    """True when an OpenSubtitles lookup could fill something."""
    return any(is_empty(current.get(f)) for f in ("imdb", "tmdb", "title", "year"))


def plan(current, feature):
    """current: {field: value} read from the playing item. feature: OpenSubtitles feature_details.
    Returns {field: new value} for the empty fields only."""
    is_episode = feature.get("feature_type") == "Episode"
    title = (feature.get("title") or "").strip()
    year = feature.get("year")
    if is_episode:
        # a4k (and most players) treat an episode's IMDb/TMDb id as the SHOW's id + season/episode
        candidates = {
            "imdb": imdb_tt(feature.get("parent_imdb_id")) or imdb_tt(feature.get("imdb_id")),
            "tmdb": _str_id(feature.get("parent_tmdb_id")) or _str_id(feature.get("tmdb_id")),
            "title": title,
            "label": title,
            "mediatype": "episode",
            "tvshowtitle": (feature.get("parent_title") or "").strip(),
            "season": _int(feature.get("season_number")),
            "episode": _int(feature.get("episode_number")),
        }
    else:
        candidates = {
            "imdb": imdb_tt(feature.get("imdb_id")),
            "tmdb": _str_id(feature.get("tmdb_id")),
            "title": title,
            "originaltitle": title,
            "label": title,
            "mediatype": "movie",
        }
    candidates["year"] = _int(year)
    return {f: v for f, v in candidates.items()
            if not is_empty(v) and is_empty(current.get(f))}


def _int(value):
    try:
        n = int(value)
    except (TypeError, ValueError):
        return None
    return n if n > 0 else None


def _str_id(value):
    n = _int(value)
    return str(n) if n else ""
