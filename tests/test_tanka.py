"""日用品の単価比較サイトのテスト(楽天APIには接続しません)。"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "sites" / "tanka"
sys.path.insert(0, str(SITE))
sys.path.insert(0, str(ROOT / "sites" / "common"))

import unitprice as tr  # noqa: E402
from quantity import parse_quantity  # noqa: E402

CATS = {c["slug"]: c for c in json.loads((SITE / "config.json").read_text(encoding="utf-8"))["categories"]}


def raw(code, name, price, reviews=50, postage=0, shop="normalshop", pmax=None):
    return {"itemCode": code, "itemName": name, "itemPrice": price, "itemPriceMin3": price, "itemPriceMax3": pmax or price,
            "affiliateUrl": "https://example.com/" + code, "mediumImageUrls": [], "shopName": "店", "shopCode": shop,
            "reviewCount": reviews, "reviewAverage": 4.2, "postageFlag": postage}


class SheetQuantityTests(unittest.TestCase):
    def test_sheets(self):
        cases = [("メリーズ パンツ Mサイズ 186枚 62枚x3セット", 186), ("グーン パンツ M 58枚 【3個セット】", 174),
                 ("ゴミ袋 45L 50枚入 ×4袋", 200), ("【2個セット】サージマスク 2箱 100枚", None),
                 ("M 58枚 L 44枚 3個セット", None)]
        for name, expected in cases:
            self.assertEqual(parse_quantity(name, "sheet"), expected, name)


class RankTests(unittest.TestCase):
    def test_water_rank(self):
        raws = [raw("a", "天然水 2L×12本", 1900), raw("b", "天然水 2L×9本", 1070),
                raw("c", "天然水 2L×12本", 900, postage=1),               # 送料別は外す
                raw("d", "天然水 2L×6本 2L×12本", 1000, pmax=1900),       # 選べる商品は外す
                raw("e", "【ふるさと納税】天然水 2L×12本", 5000, shop="f012345-x"),  # ふるさと納税は外す
                raw("f", "天然水 500ml×24本", 1200),                    # 2Lではない
                raw("g", "炭酸水 2L×6本", 900)]                          # 炭酸は外す
        ranked = tr.rank_category(raws, CATS["water-2l"])
        self.assertEqual([p.code for p in ranked], ["b", "a"])
        self.assertAlmostEqual(ranked[0].unit_price, 1070 / 18, places=3)

    def test_diaper_size_filter(self):
        raws = [raw("m", "メリーズ パンツ Mサイズ 6〜11kg 186枚 62枚x3セット", 6197),
                raw("l", "メリーズ パンツ Lサイズ 9〜14kg 44枚×3", 5800),
                raw("cake", "おむつケーキ パンパース パンツ Mサイズ", 9000),
                raw("adult", "ライフリー 超うす型パンツ Mサイズ 24枚×3", 6100)]
        self.assertEqual([p.code for p in tr.rank_category(raws, CATS["omutsu-pants-m"])], ["m"])
        self.assertEqual([p.code for p in tr.rank_category(raws, CATS["omutsu-pants-l"])], ["l"])


class ReviewBadgeTests(unittest.TestCase):
    def test_badges(self):
        from reviews import review_badges
        self.assertEqual(review_badges(1200, 4.6), ["レビュー1,000件以上", "★4.5以上"])
        self.assertEqual(review_badges(150, 4.2), ["レビュー100件以上"])
        self.assertEqual(review_badges(5, 5.0), [])  # 件数が少ない高評価は目印にしない


class BuildTests(unittest.TestCase):
    def test_demo_build(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "site"
            r = subprocess.run([sys.executable, str(SITE / "build.py"), "--demo", "--out", str(out), "--today", "2026-11-03"],
                               capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            index = (out / "index.html").read_text(encoding="utf-8")
            self.assertIn('class="pr-tag">PR', index)
            self.assertIn('name="robots" content="noindex"', index)
            water = (out / "water-2l" / "index.html").read_text(encoding="utf-8")
            self.assertIn('rel="nofollow sponsored noopener"', water)
            self.assertNotIn("送料別", water)  # 送料別のダミー商品は載らない
            listing = water[water.index("data-list"):]
            self.assertLess(listing.index("2L×9本"), listing.index("2L×12本"))  # 59.4円/L が 79.2円/L より上
            for f in ("favicon.ico", "sitemap.xml", "robots.txt", "about/index.html", "privacy/index.html"):
                self.assertTrue((out / f).exists(), f)


if __name__ == "__main__":
    unittest.main()
