"""SNS投稿の下書きのテスト(ネットには接続しません)。"""
import sys
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "sites" / "social"))

import make_posts as mp  # noqa: E402

FURUSATO = {"url": "https://furusato-yosan.com", "updated": "11月5日 05:20", "days_left": 56,
            "genres": [{"slug": "rice", "title": "お米", "short": "お米", "unit": "kg", "count": 20, "typical": 5.7,
                        "top": {"per10k": 8.9, "shop": "熊本県甲佐町", "name": "米", "price": 22500, "amount_text": "20kg"}}],
            "plans": [{"budget": 50000, "slug": "5man", "name": "お米と肉でがっつり", "total": 48000,
                       "items": [{"short": "お米", "amount_text": "20kg", "price": 22500},
                                 {"short": "豚肉", "amount_text": "5kg", "price": 16000}]}]}
TANKA = {"url": "https://tanka-erabu.com", "updated": "11月5日 05:45",
         "categories": [{"slug": "kome", "title": "お米", "group": "食品", "per": "1kg", "count": 30, "typical": 420.0,
                         "max": 900.0, "top": {"unit_price": 319.3, "shop": "店", "name": "米", "price": 9580,
                                               "amount_text": "30kg"}},
                        {"slug": "water-2l", "title": "水 2L", "group": "飲みもの", "per": "1L", "count": 17,
                         "typical": 90.0, "max": 150.0, "top": {"unit_price": 59.4, "shop": "店", "name": "水",
                                                                "price": 1070, "amount_text": "18L"}}]}


class PostTests(unittest.TestCase):
    def test_posts_have_pr_link_and_fit(self):
        posts = mp.make_posts(FURUSATO, TANKA, date(2026, 11, 5))
        self.assertGreaterEqual(len(posts), 3)
        for p in posts:
            self.assertIn("(PR)", p["threads"].split("\n")[0])   # 1行目に広告の表示
            self.assertIn("※広告を含みます", p["threads"])
            self.assertTrue(p["x"].endswith("(PR)"))
            self.assertIn("https://", p["x"])
            self.assertLessEqual(len(p["threads"]), mp.THREADS_LIMIT)
            self.assertLessEqual(mp.x_length(p["x"]), mp.X_LIMIT)
            self.assertIn("《", p["threads"])                    # 自分の言葉を入れる欄
            self.assertNotIn("最安", p["threads"] + p["x"])       # 断定的な言葉は使わない

    def test_one_site_missing(self):
        posts = mp.make_posts(None, TANKA, date(2026, 11, 5))
        self.assertTrue(posts)
        self.assertTrue(all("日用品" in p["title"] for p in posts))

    def test_x_length(self):
        self.assertEqual(mp.x_length("abc"), 3)
        self.assertEqual(mp.x_length("あいう"), 6)
        self.assertEqual(mp.x_length("見て https://example.com/very/long/path"), 4 + 1 + 23)


if __name__ == "__main__":
    unittest.main()
