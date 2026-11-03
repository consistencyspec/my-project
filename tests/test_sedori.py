"""楽天→Amazon 価格差チェックのテスト(外部APIには接続しません)。"""
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "sedori"))

import config  # noqa: E402
import rakuten_amazon as ra  # noqa: E402


class JanTests(unittest.TestCase):
    def test_check_digit(self):
        self.assertTrue(ra.jan_ok("4901234567894"))
        self.assertFalse(ra.jan_ok("4901234567890"))

    def test_find_in_text(self):
        self.assertEqual(ra.find_jan("商品 JAN:4901234567894 です"), "4901234567894")
        self.assertEqual(ra.find_jan("型番 12345", "ＪＡＮ４９０１２３４５６７８９４"), "4901234567894")
        self.assertEqual(ra.find_jan("49012345678941234"), "")  # 長い数字の一部は拾わない


class RakutenParseTests(unittest.TestCase):
    def test_parse_v2(self):
        data = {"Items": [{"itemName": "収納ボックス 4901234567894", "itemPrice": 2200, "itemUrl": "u",
                           "shopName": "s", "pointRate": 10, "postageFlag": 1}]}
        it = ra.parse_rakuten(data, "収納")[0]
        self.assertEqual(it.jan, "4901234567894")
        self.assertFalse(it.shipping_included)
        self.assertEqual(it.point_rate, 10)


class CalcTests(unittest.TestCase):
    def setUp(self):
        self.saved = (config.EXTRA_POINT_PERCENT, config.RAKUTEN_SHIPPING_ESTIMATE)
        config.EXTRA_POINT_PERCENT, config.RAKUTEN_SHIPPING_ESTIMATE = 0, 700

    def tearDown(self):
        config.EXTRA_POINT_PERCENT, config.RAKUTEN_SHIPPING_ESTIMATE = self.saved

    def test_cost_and_profit(self):
        it = ra.Item(name="x", price=2200, url="", shop="", point_rate=10, shipping_included=False)
        self.assertEqual(it.points, 200)          # 2000円(税抜) × 10%
        self.assertEqual(it.cost, 2200 + 700 - 200)
        it.amazon_price, it.fees = 5000, 1000
        self.assertEqual(it.profit, 5000 - 1000 - config.INBOUND_SHIPPING_PER_ITEM - it.cost)

    def test_breakeven_gives_min_profit(self):
        it = ra.Item(name="x", price=3000, url="", shop="")
        it.amazon_price = it.breakeven_price
        self.assertGreaterEqual(it.profit, config.MIN_PROFIT)

    def test_screen(self):
        self.assertIn("NG", ra.screen(ra.Item(name="訳あり品 4901234567894", price=1, url="", shop="", jan="4901234567894")))
        self.assertIn("ブランド", ra.screen(ra.Item(name="ＬＥＧＯ ブロック", price=1, url="", shop="", jan="4901234567894")))
        self.assertEqual(ra.screen(ra.Item(name="収納", price=1, url="", shop="")), "JANなし")


class AmazonParseTests(unittest.TestCase):
    def test_catalog(self):
        data = {"items": [{"asin": "B000TEST01",
                           "identifiers": [{"identifiers": [{"identifierType": "EAN", "identifier": "4901234567894"}]}],
                           "summaries": [{"itemName": "テスト商品"}],
                           "salesRanks": [{"displayGroupRanks": [{"rank": 1234}]}]}]}
        self.assertEqual(ra.parse_catalog(data, {"4901234567894"}),
                         {"4901234567894": ("B000TEST01", "テスト商品", 1234)})

    def test_offers(self):
        data = {"payload": {"Summary": {"TotalOfferCount": 5, "BuyBoxPrices": [
            {"condition": "New", "LandedPrice": {"Amount": 3980.0}}]},
            "Offers": [{"SellerId": ra.AMAZON_JP_SELLER_ID}]}}
        self.assertEqual(ra.parse_offers(data), (3980, 5, True))

    def test_offers_fallback_lowest(self):
        data = {"payload": {"Summary": {"LowestPrices": [
            {"condition": "new", "LandedPrice": {"Amount": 2500}},
            {"condition": "new", "LandedPrice": {"Amount": 2300}}]}, "Offers": []}}
        self.assertEqual(ra.parse_offers(data), (2300, 0, False))


class OutputTests(unittest.TestCase):
    def test_write_manual_and_auto(self):
        a = ra.Item(name="候補", price=2000, url="u", shop="s", jan="4901234567894", asin="B1",
                    amazon_price=6000, fees=900, sales_rank=100, offer_count=3)
        b = ra.Item(name="除外", price=2000, url="u", shop="s", skip_reason="JANなし")
        with tempfile.TemporaryDirectory() as d:
            for auto in (True, False):
                csv_path, html_path, n = ra.write_outputs([a, b], Path(d), auto)
                self.assertTrue(csv_path.exists() and html_path.exists())
                self.assertEqual(n, 1)


if __name__ == "__main__":
    unittest.main()
