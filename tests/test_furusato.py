"""ふるさと納税コスパ比較サイトのテスト(楽天APIには接続しません)。"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "sites" / "furusato"
sys.path.insert(0, str(SITE))

from quantity import parse_quantity, to_display  # noqa: E402
from rank import rank_category, short_name  # noqa: E402

CONFIG = json.loads((SITE / "config.json").read_text(encoding="utf-8"))
CATS = {c["slug"]: c for c in CONFIG["categories"]}


class QuantityTests(unittest.TestCase):
    def test_reads_single_amounts(self):
        cases = [
            ("【ふるさと納税】米 10kg 令和8年産", "weight", 10000),
            ("こめ油 900g × 5本 セット 900g", "weight", 4500),
            ("豚肉 5種 合計3.7kg 500g×4", "weight", 3700),
            ("天然水 2L×6本×2箱", "volume", 24000),
            ("天然水 ２Ｌ×１２本", "volume", 24000),
            ("トイレットペーパー 12ロール×8パック 2倍巻き", "roll", 192),
            ("シングル 144ロール相当 48ロール 3倍巻き", "roll", 144),
            ("ティッシュ 5箱×12パック", "box", 60),
            ("みかん 約5kg", "weight", 5000),
        ]
        for name, family, expected in cases:
            self.assertEqual(parse_quantity(name, family), expected, name)

    def test_rejects_ambiguous(self):
        cases = [
            ("米 300g〜30kg 1回 3回", "weight"),
            ("米 5kg 10kg 20kg", "weight"),
            ("水 2L×6本 2L×12本", "volume"),
            ("米 定期便 10kg 6ヶ月", "weight"),
            ("容量が選べる 米 5kg", "weight"),
            ("米 産地直送", "weight"),
        ]
        for name, family in cases:
            self.assertIsNone(parse_quantity(name, family), name)

    def test_display(self):
        self.assertEqual(to_display(10000, "weight"), "10kg")
        self.assertEqual(to_display(3700, "weight"), "3.7kg")
        self.assertEqual(to_display(24000, "volume"), "24L")
        self.assertEqual(to_display(96, "roll"), "96ロール")


def raw(code, name, price, reviews=50, pmax=None, shop_code="f012345-test"):
    return {"itemCode": code, "itemName": name, "itemPrice": price, "itemPriceMin3": price,
            "itemPriceMax3": pmax or price, "affiliateUrl": "https://example.com/" + code,
            "mediumImageUrls": ["https://thumbnail.image.rakuten.co.jp/x.jpg?_ex=128x128"],
            "shopName": "テスト町", "shopCode": shop_code, "reviewCount": reviews, "reviewAverage": 4.5}


class RankTests(unittest.TestCase):
    def test_rank_order_and_split(self):
        raws = [
            raw("a", "【ふるさと納税】米 5kg", 10000),               # 5.0kg/万円
            raw("b", "【ふるさと納税】米 計10kg 5kg×2袋", 14000),     # 7.1kg/万円
            raw("c", "【ふるさと納税】米 5kg 10kg", 6000, pmax=12000),  # 選べる → popular
            raw("d", "【ふるさと納税】米油 900g", 3000),             # 除外ワード
            raw("e", "【ふるさと納税】米 5kg", 10000, reviews=2),    # レビュー不足
            raw("f", "米 5kg", 5000, shop_code="normalshop"),       # ふるさと納税ではない
            raw("g", "【ふるさと納税】米 100kg", 5000),              # 範囲外(読み取りミス扱い)
            raw("b", "【ふるさと納税】米 計10kg 5kg×2袋", 14000),     # 重複
        ]
        ranked, popular = rank_category(raws, CATS["rice"])
        self.assertEqual([g.code for g in ranked], ["b", "a"])
        self.assertEqual(sorted(g.code for g in popular), ["c", "g"])
        self.assertIn("_ex=240x240", ranked[0].image)

    def test_overrides(self):
        raws = [raw("a", "【ふるさと納税】米 5kg", 10000), raw("c", "【ふるさと納税】米 5kg 10kg", 6000, pmax=12000)]
        ov = {"a": {"exclude": True}, "c": {"amount": 5000, "note": "確認済み"}}
        ranked, _ = rank_category(raws, CATS["rice"], ov)
        self.assertEqual([g.code for g in ranked], ["c"])
        self.assertEqual(ranked[0].note, "確認済み")

    def test_short_name(self):
        self.assertEqual(short_name("【ふるさと納税】＼新米／ 米 5kg [テスト町]"), "新米 米 5kg")


class BuildTests(unittest.TestCase):
    def test_demo_build(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "site"
            r = subprocess.run([sys.executable, str(SITE / "build.py"), "--demo", "--out", str(out),
                                "--today", "2026-11-03"], capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            index = (out / "index.html").read_text(encoding="utf-8")
            self.assertIn("プロモーション(広告)", index)     # 広告の表示
            self.assertIn("あと<strong>58</strong>日", index)                     # 締め切りまでの日数
            self.assertIn('name="robots" content="noindex"', index)  # デモは検索に載せない
            rice = (out / "rice" / "index.html").read_text(encoding="utf-8")
            self.assertIn('rel="nofollow sponsored noopener"', rice)
            self.assertIn("楽天で寄付する(PR)", rice)
            self.assertLess(rice.index("計10kg"), rice.index("サンプル米 5kg"))  # 7.1kg/万円 が 5.6kg/万円 より上
            self.assertTrue((out / "sitemap.xml").exists())
            self.assertIn("Disallow: /", (out / "robots.txt").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
