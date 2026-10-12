"""Uzblokuoti pardavejai (/blokuoti): ju skelbimai nesiunciami ir neina i rinkos kaina.
2026-10-12: savininkas paprase nebesiusti vieno Vinted pardavejo skelbimu."""
import contextlib
import io
import unittest

from tests.helpers import reset_config, TempDir, item, listing
from tests.test_flow import FakeClient, FakeTelegram
from vinted import commands, config
from vinted.finder import Run
from vinted.state import State
from vinted.util import is_blocked_seller, seller_key

MARKET = [item(2000 + i, "iPhone 13 128GB", p, user_id=600 + i)
          for i, p in enumerate([230, 240, 250, 260, 270, 280, 290, 300, 310])]


def run(user):
    config.cfg["SEARCH_QUERIES"] = ["iPhone 13"]
    with TempDir():
        tg = FakeTelegram()
        target = item(9, "iPhone 13 128GB", 150, user_id=9)
        target["user"] = user
        client = FakeClient({"iPhone 13": MARKET + [target]}, pages={"9": "Veikia puikiai, siunčiu per Vinted"})
        with contextlib.redirect_stdout(io.StringIO()) as out:
            Run(client, tg, sleep=lambda s: None).run()
        return [d for d, _ in tg.deals if d["id"] == "vinted:9"], out.getvalue()


class SellerKeyTest(unittest.TestCase):
    def test_forms(self):
        self.assertEqual(seller_key("@Antanas19991"), "antanas19991")
        self.assertEqual(seller_key(" antanas19991 "), "antanas19991")
        self.assertEqual(seller_key("https://www.vinted.lt/member/123456-antanas19991"), "123456")
        self.assertEqual(seller_key("Šarūnas"), "sarunas")

    def test_match_by_login_or_id(self):
        lst = listing(1, "iPhone 13", 150, user_id=123456)
        lst.raw["user"]["login"] = "Antanas19991"
        self.assertTrue(is_blocked_seller(lst, ["antanas19991"]))
        self.assertTrue(is_blocked_seller(lst, ["https://www.vinted.lt/member/123456-x"]))
        self.assertFalse(is_blocked_seller(lst, ["kitas"]))
        self.assertFalse(is_blocked_seller(lst, []))


class BlockedFlowTest(unittest.TestCase):
    def setUp(self):
        reset_config(HEARTBEAT_HOURS=0, MIN_SAMPLES=8, DEAL_MODE="rank", MIN_BATTERY=0, MIN_PROFIT_EUR=0)

    def test_blocked_seller_not_sent(self):
        sent, log = run({"id": 9, "login": "Antanas19991"})
        self.assertTrue(sent, "be blokavimo sis skelbimas turi buti siunciamas\n" + log)
        config.cfg["BLOCKED_SELLERS"] = ["antanas19991"]
        sent, log = run({"id": 9, "login": "Antanas19991"})
        self.assertFalse(sent)
        self.assertIn("užblokuotas pardavėjas", log)


class CommandTest(unittest.TestCase):
    def setUp(self):
        reset_config()

    def test_block_and_unblock(self):
        with TempDir():
            state = State()
            self.assertIn("antanas19991", commands.handle("/blokuoti @Antanas19991", state))
            self.assertEqual(config.cfg["BLOCKED_SELLERS"], ["antanas19991"])
            self.assertEqual(state.overrides["BLOCKED_SELLERS"], ["antanas19991"])
            commands.handle("/blokuoti antanas19991", state)            # antra karta – nedubliuojama
            self.assertEqual(config.cfg["BLOCKED_SELLERS"], ["antanas19991"])
            self.assertIn("antanas19991", commands.handle("/blokuoti", state))
            commands.handle("/atblokuoti antanas19991", state)
            self.assertEqual(config.cfg["BLOCKED_SELLERS"], [])


if __name__ == "__main__":
    unittest.main()
