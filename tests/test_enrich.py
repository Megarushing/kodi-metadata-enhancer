import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "service.metadataenhancer"))
from resources.lib.enrich import plan, wanted  # noqa: E402
from resources.lib.opensubtitles import pick_feature, imdb_tt  # noqa: E402

EMPTY = {"imdb": "", "tmdb": "", "title": "", "originaltitle": "", "label": "", "year": 0,
         "mediatype": "", "tvshowtitle": "", "season": -1, "episode": -1}
MOVIE = {"feature_type": "Movie", "title": "The Runner", "year": None, "imdb_id": 34564059, "tmdb_id": 1386315}
EPISODE = {"feature_type": "Episode", "title": "Pilot", "year": 2024, "imdb_id": 111, "tmdb_id": 222,
           "parent_title": "Some Show", "parent_imdb_id": 1234567, "parent_tmdb_id": 999,
           "season_number": 2, "episode_number": 5}


class PlanTest(unittest.TestCase):
    def test_fills_every_empty_movie_field(self):
        self.assertEqual(plan(EMPTY, MOVIE), {
            "imdb": "tt34564059", "tmdb": "1386315", "title": "The Runner",
            "originaltitle": "The Runner", "label": "The Runner", "mediatype": "movie"})

    def test_never_overwrites(self):
        current = dict(EMPTY, imdb="tt0000001", title="56 up", label="56 up", mediatype="episode", year=2012)
        self.assertEqual(plan(current, MOVIE), {"tmdb": "1386315", "originaltitle": "The Runner"})

    def test_null_year_is_skipped(self):
        self.assertNotIn("year", plan(EMPTY, MOVIE))

    def test_episode_uses_show_ids(self):
        p = plan(EMPTY, EPISODE)
        self.assertEqual((p["imdb"], p["tmdb"], p["tvshowtitle"], p["season"], p["episode"], p["year"]),
                         ("tt1234567", "999", "Some Show", 2, 5, 2024))

    def test_wanted(self):
        self.assertTrue(wanted(EMPTY))
        self.assertFalse(wanted(dict(EMPTY, imdb="tt1", tmdb="1", title="x", year=2000)))


class PickTest(unittest.TestCase):
    def test_only_hash_matches(self):
        sub = lambda m, i: {"attributes": {"moviehash_match": m, "feature_details": {"imdb_id": i}}}
        self.assertIsNone(pick_feature({"data": [sub(False, 1)]}))
        self.assertEqual(pick_feature({"data": [sub(False, 1), sub(True, 2)]})["imdb_id"], 2)
        self.assertIsNone(pick_feature({}))

    def test_imdb_tt(self):
        self.assertEqual(imdb_tt(12345), "tt0012345")
        self.assertEqual(imdb_tt(None), "")


if __name__ == "__main__":
    unittest.main()
