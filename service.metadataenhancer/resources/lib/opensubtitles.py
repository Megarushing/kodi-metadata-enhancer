"""Minimal OpenSubtitles.com REST client: movie hash -> feature details (ids, title, year, type).

Only a result OpenSubtitles flags as moviehash_match counts; no title/name fallback.
"""
import json
import urllib.error
import urllib.parse
import urllib.request

API = "https://api.opensubtitles.com/api/v1"
TIMEOUT = 15


class Client:
    def __init__(self, api_key, user_agent, username="", password=""):
        self.api_key, self.user_agent = api_key, user_agent
        self.username, self.password = username, password
        self.token = None
        self.base = API

    def _request(self, method, url, body=None, auth=True):
        headers = {"Api-Key": self.api_key, "User-Agent": self.user_agent, "Accept": "application/json"}
        data = None
        if body is not None:
            data = json.dumps(body).encode()
            headers["Content-Type"] = "application/json"
        if auth and self.token:
            headers["Authorization"] = "Bearer " + self.token
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            return json.loads(r.read().decode())

    def login(self):
        if not (self.username and self.password) or self.token:
            return
        res = self._request("POST", API + "/login", {"username": self.username, "password": self.password},
                            auth=False)
        self.token = res.get("token")
        host = res.get("base_url")
        if host:
            self.base = "https://%s/api/v1" % host

    def feature_by_hash(self, oshash):
        """feature_details of a subtitle matching this exact file, else None."""
        url = self.base + "/subtitles?" + urllib.parse.urlencode({"moviehash": oshash})
        try:
            self.login()
            res = self._request("GET", url)
        except urllib.error.HTTPError as e:
            if e.code != 401 or not self.token:
                raise
            self.token = None  # expired token: log in again once
            self.login()
            res = self._request("GET", url)
        return pick_feature(res)


def pick_feature(res):
    for sub in res.get("data") or []:
        attrs = sub.get("attributes") or {}
        if attrs.get("moviehash_match") and attrs.get("feature_details"):
            return attrs["feature_details"]
    return None


def imdb_tt(number):
    """OpenSubtitles stores IMDb ids as ints; Kodi wants 'tt' + at least 7 digits."""
    return "tt%07d" % number if isinstance(number, int) and number > 0 else ""
