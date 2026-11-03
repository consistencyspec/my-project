"""eBay輸出ツールのテスト(eBay APIには接続しません)。"""
import importlib
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
D = str(ROOT / "ebay_export")


def load():
    # sedori/config.py と名前がぶつからないよう、ebay_export を先頭にして読み込み直す
    sys.path.insert(0, D)
    for m in ("config", "profit", "ebay_research"):
        sys.modules.pop(m, None)
    cfg = importlib.import_module("config")
    pf = importlib.import_module("profit")
    er = importlib.import_module("ebay_research")
    sys.path.remove(D)
    for m in ("config", "profit", "ebay_research"):
        sys.modules.pop(m, None)
    return cfg, pf, er


config, profit, er = load()


class ProfitTests(unittest.TestCase):
    def test_breakdown_adds_up(self):
        r = profit.calc(3000, 60.0, 5.0, 2500, to_us=True)
        self.assertAlmostEqual(r.revenue_jpy - r.fees_jpy - r.tariff_jpy - r.ship_cost_jpy - r.buy_jpy,
                               r.profit_jpy, delta=2)
        self.assertGreater(r.tariff_jpy, 0)
        self.assertEqual(profit.calc(3000, 60.0, 5.0, 2500, to_us=False).tariff_jpy, 0)

    def test_max_buy_meets_target(self):
        mb = profit.max_buy_price(100.0)
        self.assertTrue(profit.calc(mb, 100.0).ok)
        self.assertFalse(profit.calc(mb + 500, 100.0).ok)

    def test_min_sell_meets_target(self):
        s = profit.min_sell_price(4000)
        self.assertTrue(profit.calc(4000, s).ok)
        self.assertFalse(profit.calc(4000, s - 1).ok)

    def test_csv(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "in.csv"
            p.write_text("name,buy_jpy,sell_usd,ship_usd,ship_cost_jpy,to_us\nA,\"1,000\",$80,0,,1\n", encoding="utf-8")
            profit.HERE = Path(d)
            profit.run_csv(p)
            self.assertEqual(len(list((Path(d) / "output").glob("profit_*.csv"))), 1)


class ResearchTests(unittest.TestCase):
    DATA = {"total": 3, "itemSummaries": [
        {"title": "A", "price": {"value": "40.00"}, "shippingOptions": [{"shippingCost": {"value": "10.00"}}]},
        {"title": "B", "price": {"value": "60.00"}},
        {"title": "C", "price": {"value": "bad"}}]}

    def test_landed_prices(self):
        self.assertEqual(er.landed_prices(self.DATA), [50.0, 60.0])

    def test_summarize(self):
        r = er.summarize("kw", {"total": 10}, self.DATA)
        self.assertEqual((r["total"], r["jp"], r["median"], r["low"]), (10, 3, 55.0, 50.0))
        self.assertEqual(r["max_buy"], profit.max_buy_price(55.0))

    def test_keywords_and_report(self):
        with tempfile.TemporaryDirectory() as d:
            k = Path(d) / "k.txt"
            k.write_text("# memo\nIchiban Kuji | 一番くじ\nGashapon\n", encoding="utf-8")
            self.assertEqual(er.read_keywords(k), [("Ichiban Kuji", "一番くじ"), ("Gashapon", "")])
            r = er.summarize("Ichiban Kuji", {"total": 10}, self.DATA)
            r["ja"] = "一番くじ"
            c, h = er.write_report([r], Path(d))
            self.assertIn("jp.mercari.com", h.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()


def load_sales():
    sys.path.insert(0, D)
    for m in ("config", "sales_report"):
        sys.modules.pop(m, None)
    sr = importlib.import_module("sales_report")
    sys.path.remove(D)
    for m in ("config", "sales_report"):
        sys.modules.pop(m, None)
    return sr


sr = load_sales()


class SalesReportTests(unittest.TestCase):
    def setUp(self):
        self.orders, self.tx = sr.demo_data()
        self.tmp = tempfile.TemporaryDirectory()
        sr.COSTS_FILE = Path(self.tmp.name) / "costs.csv"
        self.saved_here, sr.HERE = sr.HERE, Path(self.tmp.name)

    def tearDown(self):
        sr.HERE = self.saved_here
        self.tmp.cleanup()

    def test_money_by_order(self):
        by, over = sr.money_by_order(self.tx)
        rate = sr.config.USD_JPY
        self.assertAlmostEqual(by["01-0001"]["gross"], 159.99 * rate, places=2)
        self.assertAlmostEqual(by["01-0001"]["net"], (159.99 - 23.5) * rate, places=2)
        self.assertAlmostEqual(by["01-0004"]["refund"], -10 * rate, places=2)
        self.assertAlmostEqual(by["01-0005"]["label"], -21.5 * rate, places=2)
        self.assertNotIn("PAYOUT", over)  # 振込は費用に入れない
        self.assertAlmostEqual(sum(over.values()), -12.3 * rate, places=2)

    def test_costs_preserved_and_profit(self):
        rows = sr.order_rows(self.orders)
        costs, added = sr.update_costs(rows)
        self.assertEqual(added, 6)
        costs[("01-0001", "01-0001-L0")]["buy_jpy"] = "10000"
        with sr.COSTS_FILE.open("w", newline="", encoding="utf-8-sig") as f:
            import csv
            w = csv.DictWriter(f, fieldnames=sr.COST_COLUMNS)
            w.writeheader()
            w.writerows(costs.values())
        costs, added = sr.update_costs(rows)
        self.assertEqual(added, 0)
        self.assertEqual(costs[("01-0001", "01-0001-L0")]["buy_jpy"], "10000")  # 入力が消えない
        by, _ = sr.money_by_order(self.tx)
        lines = {l["line_item_id"]: l for l in sr.build_report(rows, by, costs)}
        l = lines["01-0001-L0"]
        self.assertEqual(l["profit"], round(by["01-0001"]["net"] - 10000 - sr.config.PACKING_COST_JPY))
        self.assertIsNone(lines["01-0002-L0"]["profit"])  # 未入力
        self.assertEqual(lines["01-0005-L0"]["net"], round(by["01-0005"]["net"] / 2))  # 2商品で按分

    def test_groups_and_report(self):
        self.assertEqual(sr.guess_group("Chiikawa Gashapon set"), "ガチャ")
        self.assertEqual(sr.guess_group("random item"), "その他")
        rows = sr.order_rows(self.orders)
        costs, _ = sr.update_costs(rows)
        by, over = sr.money_by_order(self.tx)
        from datetime import datetime
        c, h, missing = sr.write_report(sr.build_report(rows, by, costs), over, datetime(2026, 9, 1), datetime(2026, 10, 31))
        self.assertEqual(missing, 6)
        self.assertIn("グループ別", h.read_text(encoding="utf-8"))

    def test_to_jpy(self):
        self.assertEqual(sr.to_jpy({"value": "1000", "currency": "JPY"}), 1000)
        self.assertEqual(sr.to_jpy({"value": "2", "currency": "USD"}), 2 * sr.config.USD_JPY)
        self.assertEqual(sr.to_jpy(None), 0)


def load_trends():
    sys.path.insert(0, D)
    for m in ("config", "profit", "ebay_research", "japan_trends"):
        sys.modules.pop(m, None)
    jt = importlib.import_module("japan_trends")
    sys.path.remove(D)
    for m in ("config", "profit", "ebay_research", "japan_trends"):
        sys.modules.pop(m, None)
    return jt


jt = load_trends()


class JapanTrendsTests(unittest.TestCase):
    def test_scan_and_report(self):
        from unittest import mock

        def fake_call(token, path, params=None):
            if path == "/item_summary/search" and params.get("fieldgroups"):
                return {"total": 500, "refinement": {"categoryDistributions": [
                    {"categoryId": "10", "categoryName": "Sub A", "matchCount": 300},
                    {"categoryId": "11", "categoryName": "Sub B", "matchCount": 100}]}}
            if path == "/item_summary/search" and "itemLocationCountry" not in params.get("filter", ""):
                return {"total": 1000}
            if path == "/item_summary/search":
                return {"itemSummaries": [{"itemId": "v1|1|0"}, {"itemId": "v1|2|0"}]}
            return {"title": "Japan item " + path, "price": {"value": "30.00"},
                    "estimatedAvailabilities": [{"estimatedSoldQuantity": 12}],
                    "itemCreationDate": "2026-05-01T00:00:00.000Z", "itemWebUrl": "https://e/x"}

        with mock.patch.object(jt, "call", fake_call), mock.patch.object(jt.er, "get_token", lambda: "t"), \
                mock.patch.object(jt.config, "TREND_CATEGORIES", {"1": "Collectibles"}, create=True):
            rows, items = jt.scan()
        self.assertEqual([r["subcategory"] for r in rows], ["Sub A", "Sub B"])
        self.assertEqual(rows[0]["sold"], 24)
        self.assertEqual(rows[0]["jp_share"], 0.3)
        self.assertGreater(rows[0]["per_month"], 0)
        with tempfile.TemporaryDirectory() as d:
            paths = jt.write_report(rows, items, Path(d))
            self.assertTrue(all(p.exists() for p in paths))
            self.assertIn("Sub A", paths[2].read_text(encoding="utf-8"))
