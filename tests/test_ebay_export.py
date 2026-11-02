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
