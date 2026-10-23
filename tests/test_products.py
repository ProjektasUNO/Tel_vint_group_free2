"""Apple produktai (iPad, MacBook, AirPods, iMac, Mac mini) – rinkimo rezimas: atpazinimas,
priedu/daliu/kopiju atmetimas ir kainu kaupimas archyve. Niekas nesiunciama."""
import contextlib
import io
import unittest

from tests.helpers import reset_config, TempDir, item
from tests.test_flow import FakeClient, FakeTelegram
from vinted import archive, config, products
from vinted.finder import Run
from vinted.state import State


class DetectTest(unittest.TestCase):
    def test_looks_converted(self):
        from vinted.util import looks_converted
        for p in (550, 182.5, 219.99, 99.9, 49.95, 19.49, None):
            self.assertFalse(looks_converted(p), p)
        for p in (532.28, 692.64, 166.7, 23.15):
            self.assertTrue(looks_converted(p), p)

    def test_models(self):
        cases = {
            "iPad Pro 11 M1 128GB": ("ipad", "iPad Pro 11 M1", "128 GB"),
            "Apple iPad Pro 12,9 2021 M1 256GB WiFi": ("ipad", "iPad Pro 12.9 M1", "256 GB"),
            "iPad Air 5 64GB": ("ipad", "iPad Air 5", "64 GB"),
            "iPad mini 6 64gb": ("ipad", "iPad mini 6", "64 GB"),
            "iPad 9 kartos 64GB": ("ipad", "iPad 9", "64 GB"),
            "iPad 2021 64gb": ("ipad", "iPad 9", "64 GB"),
            "MacBook Air M1 8GB 256GB": ("macbook", "MacBook Air M1", "256 GB"),
            "MacBook Pro 14 M1 Pro 16GB 512GB": ("macbook", "MacBook Pro M1 Pro 14", "512 GB"),
            "MacBook Pro 2019 13\" i5": ("macbook", "MacBook Pro Intel 2019 13", None),
            "Macbook air 13,6 M2 8/256": ("macbook", "MacBook Air M2 13", "256 GB"),
            "AirPods Pro 2": ("airpods", "AirPods Pro 2", None),
            "AirPods Pro (2nd gen) USB-C": ("airpods", "AirPods Pro 2", None),
            "Airpods 3": ("airpods", "AirPods 3", None),
            "AirPods Max": ("airpods", "AirPods Max", None),
            "iMac 24 M1 8/256": ("imac", "iMac 24 M1", "256 GB"),
            "Mac mini M2 8GB 256GB": ("mac_mini", "Mac mini M2", "256 GB"),
        }
        for title, (cat, model, storage) in cases.items():
            p = products.detect(title)
            self.assertEqual((p["cat"], p["model"], p["storage"]), (cat, model, storage), title)
        self.assertEqual(products.detect("MacBook Air M1 8GB 256GB")["ram"], "8 GB")

    def test_not_products(self):
        for title in ["iPhone 13 + AirPods", "Samsung Galaxy S23", "Apple Watch 8"]:
            self.assertIsNone(products.detect(title), title)

    def test_reject(self):
        for title, why in {"MacBook pakrovėjas 61W": "priedas", "iPad Pro 11 dėklas": "priedas",
                           "Dėklas iPad Air": "priedas", "Magic Keyboard iPad Pro": "priedas",
                           "AirPods Pro 2 kopija": "kopija", "Kairys AirPods Pro ausinukas": "dalis",
                           "MacBook Pro ekranas": "dalis",
                           # lenkiski skelbimai (Vinted LT rodo ir juos)
                           "Etui iPad Air 2": "priedas", "Etui na iPad": "priedas", "Pudełko AirPods": "dalis",
                           "Szkło hartowane iPad Air 1/2 Benks Magic - NOWE-": "priedas",
                           "Magnetyczna ładowarka do Ipad": "priedas",
                           "Etui z klawiaturą Vobafe do iPad Pro 13” M4 (2024)": "priedas",
                           "Płyta główna MacBook Pro 13": "dalis",
                           "Imac baleriny": "ne technika", "Śniegowce IMAC": "ne technika",
                           "Buty chłopięce na rzepy marki IMac": "ne technika", "UAG Plyo -kotelo MacBook Pro 13\" (M1/M2)": "priedas",
                           "Ipad suojakalvo": "priedas",
                           "Ballerina juhlakengät IMAC, koko 37": "ne technika"}.items():
            self.assertEqual(products.reject_reason(title), why, title)
        for title in ["MacBook Air M1 su dėklu", "iPad Pro 11 + Apple Pencil", "AirPods 2 originalūs, ne kopija",
                      "iPad Air 4 64GB dėžutė yra", "AirPods Pro 2",
                      "Ipad air (4th Generation) + Apple Pencil (2nd Generation)", "AirPods Max słuchawki Apple zielone",
                      "Apple MacBook Pro 13″ M1 | 16 GB RAM | 256 GB SSD | A2338 | Stan idealny + nowa",
                      "21.5” Apple iMAC (2013), SSD 500gb, i5 2.7ghz, 8gb ram", "Apple Mac Mini M4 16Gb ram 256 GB",
                      "Apple Ipad 9 generacja 2021 rok 64GB szary. Stan jak nowy brak wad bateria w bar",
                      "Apple Mac mini M1 16 GB RAM 1 TB SSD – z pudełkiem",
                      "MacBook Pro 15 Retina Mid 2015, i7, 16 GB RAM, ładowarka i pokrowiec",
                      "Apple AirPods Pro 3 z etui ładującym (USB-C / MagSafe)",
                      "MacBook Air M1 16/256 GB / bateria 93% / pudełko / zadbany",
                      "Apple MacBook Pro 14\" z wyświetlaczem nanostrukturalnym, M5, 32 GB,1 TB SSD, 96W"]:
            self.assertIsNone(products.reject_reason(title), title)


def run(catalog, users=None, pages=None, statuses=None):
    tg = FakeTelegram()
    with contextlib.redirect_stdout(io.StringIO()) as out:
        Run(FakeClient(catalog, users=users, pages=pages, statuses=statuses), tg,
            sleep=lambda s: None).run()
    return tg, out.getvalue()


class Collected20261023Test(unittest.TestCase):
    """2026-10-23: rinkime LT tarp Apple produktų – dėklai, batai „IMAC“, žaislai, dėžutės, kopijos už 5 €."""

    def test_rejected(self):
        from vinted.products import reject_reason
        cases = {
            "Mielas permatomas AirPods dėkliukas su karvutės raštu ir pakabuku": "priedas",
            "iPad 9th / 8th / 7th gen dėklas su Bluetooth klaviatūra (10.2\")": "priedas",
            "Macbook deklas su priedais": "priedas", "Mac Mini Hub & Stand": "priedas",
            "Burga Airpods gen 1 & 2 dėklas": "priedas", "Apple AirPods Pro 2 ikroviklis": "priedas",
            "Apple airpods pro dezute": "priedas", "MacBook Air dėžutė": "priedas", "IPad įdėkliukas": "priedas",
            "Apple IMac power cord": "priedas", "Imac aulinukai": "ne technika", "IMAC 37 oda": "ne technika",
            "IMAC narvas graužikams": "ne technika", "Žaislinis ipad": "ne technika",
        }
        for title, why in cases.items():
            self.assertEqual(reject_reason(title, 20), why, title)
        self.assertEqual(reject_reason("AirPods pro 3", 5), "per pigu")
        self.assertEqual(reject_reason("Apple iPad 2 64gb", 8), "per pigu")

    def test_kept(self):
        from vinted.products import reject_reason
        for title, price in [("AirPods Pro 3", 120), ("AirPods Pro 2 su dėklu", 80), ("AirPods Pro 2 + dėžutė", 70),
                             ("iPad Air 5 su klaviatūra", 300), ("MacBook Air M1 su pakrovėju ir dėklu", 450),
                             ("iMac 24 M1", 600), ("Mac mini M2", 400), ("AirPods 2nd generation", 25),
                             ("MacBook Pro 13 2015", 150)]:
            self.assertIsNone(reject_reason(title, price), title)
        self.assertIsNone(reject_reason("AirPods pro 3"))         # be kainos – kaina netikrinama


class EnrichTest(unittest.TestCase):
    def test_description_fills_gaps(self):
        r = products.enrich("MacBook Air 13", "2020 m. M1 procesorius, 8GB RAM, 256GB SSD. Baterija 92%.")
        self.assertEqual((r["model"], r["chip"], r["ram"], r["storage"]), ("MacBook Air M1 13", "M1", "8 GB", "256 GB"))
        r = products.enrich("MacBook Pro", "Intel i5, 2017 metai, 13.3 colio, 8/128")
        self.assertEqual((r["model"], r["ram"], r["storage"]), ("MacBook Pro Intel 2017 13", "8 GB", "128 GB"))
        r = products.enrich("Apple MacBook", "MacBook Pro 14 M3 Pro 18GB 512GB")
        self.assertEqual(r["model"], "MacBook Pro M3 Pro 14")
        r = products.enrich("iMac", "24 colių M1 2021, 8GB 256GB")
        self.assertEqual(r["model"], "iMac 24 M1")

    def test_title_wins(self):
        r = products.enrich("MacBook Air M2 8/256", "anksciau turejau M1, bet sis M2")
        self.assertEqual((r["chip"], r["ram"], r["storage"]), ("M2", "8 GB", "256 GB"))

    def test_variants(self):
        self.assertTrue(products.enrich("iPad", "iPad Air 5 kartos, 64GB, Wi-Fi + Cellular")["cell"])
        self.assertEqual(products.enrich("iPad", "iPad Air 5 kartos")["model"], "iPad Air 5")
        self.assertFalse(products.enrich("iPad Pro 11 M1 128GB", "tik wifi, puiki bukle")["cell"])
        self.assertIsNone(products.enrich("iPad 9 64GB", "")["cell"])
        r = products.enrich("AirPods", "AirPods Pro 2 su USB-C dėkliuku")
        self.assertEqual((r["model"], r["case"]), ("AirPods Pro 2", "usb-c"))

    def test_live_gaps(self):
        """Is pirmo gyvo rinkimo su aprasymais (2026-10-14)."""
        self.assertEqual(products.detect("Ipad mini gen 1")["model"], "iPad mini 1")
        self.assertEqual(products.detect("Ipad Air2")["model"], "iPad Air 2")
        self.assertEqual(products.detect("iPad mini4 64GB")["model"], "iPad mini 4")
        self.assertTrue(products.detect("Macbook pro13-inch i5/8gb/1TB SSD")["model"].startswith("MacBook Pro"))
        self.assertEqual(products.enrich("MacBook pro 2019", "")["model"], "MacBook Pro Intel 2019")
        self.assertEqual(products.detect("Apple AirPods 4 (ANC) su triukšmo slopinimu")["model"], "AirPods 4 ANC")
        self.assertEqual(products.detect("airpods 4 gen")["model"], "AirPods 4")
        for t in ("Apple AirPods 4 bez ANC – komplet", "Apple AirPods 4 - without active noise cancellation",
                  "AirPods 4 be triukšmo slopinimo"):
            self.assertEqual(products.detect(t)["model"], "AirPods 4", t)
        self.assertEqual(products.detect("Airpods 4 z anc")["model"], "AirPods 4 ANC")
        self.assertEqual(products.reject_reason("Superku iPad (Air / Pro ) – siūlykite"), "ieskomas")
        self.assertEqual(products.reject_reason("Perku MacBook Air M1"), "ieskomas")

    def test_bundle_and_defects(self):
        self.assertTrue(products.enrich("MacBook Air M1 + iPad 9", "")["bundle"])
        self.assertTrue(products.enrich("iPad Pro 11 + Apple Pencil", "")["bundle"])
        self.assertFalse(products.enrich("MacBook Air M1 8/256", "")["bundle"])
        r = products.enrich("MacBook Pro 13 M1 8/256", "iCloud užrakintas")
        self.assertIn("iCloud užraktas", r["blocking"])
        r = products.enrich("MacBook Air M1", "ekranas sudužęs, kitkas veikia")
        self.assertTrue(r["defects"])
        self.assertEqual(r["blocking"], [])


class ObserveTest(unittest.TestCase):
    def setUp(self):
        reset_config(HEARTBEAT_HOURS=0, PRODUCTS_OBSERVE=True, PRODUCT_QUERIES=["ipad", "macbook"],
                     SEARCH_QUERIES=["iPhone 13"])

    def test_collects_without_sending(self):
        catalog = {"ipad": [item(1, "iPad Air 5 64GB", 300), item(2, "iPad Pro 11 dėklas", 15)],
                   "macbook": [item(3, "MacBook Air M1 8GB 256GB", 500)]}
        with TempDir():
            tg, log = run(catalog)
            self.assertEqual(tg.deals, [])
            self.assertIn("Apple produktai [ipad]: gauta 2, nauju 1", log)
            ev = [e for e in archive.read() if e["e"] in ("pobs", "px", "pprice")]
            pobs = {e["id"]: e for e in ev if e["e"] == "pobs"}
            self.assertEqual(pobs["vinted:1"]["m"], "iPad Air 5")
            self.assertEqual(pobs["vinted:3"]["m"], "MacBook Air M1")
            self.assertEqual(pobs["vinted:3"]["ram"], "8 GB")
            self.assertEqual([e["why"] for e in ev if e["e"] == "px"], ["priedas"])

            # Ka tik tikrinta – antras paleidimas po minutes produktu netikrina (PRODUCTS_EVERY_MINUTES)
            _, log = run(catalog)
            self.assertNotIn("Apple produktai", log)
            # Po 15 min.: tie patys – nekartojama; pasikeitusi kaina – pprice
            st = State.load()
            st.products_at -= 16 * 60
            st.save()
            catalog["ipad"][0] = item(1, "iPad Air 5 64GB", 270)
            run(catalog)
            ev = [e for e in archive.read() if e["e"] in ("pobs", "px", "pprice")]
            self.assertEqual(sum(1 for e in ev if e["e"] == "pobs"), 2)
            self.assertEqual([(e["id"], e["p"], e["pp"]) for e in ev if e["e"] == "pprice"],
                             [("vinted:1", 270.0, 300.0)])
            self.assertEqual(State.load().products["vinted:1"][0], 270.0)

    def test_off_by_default(self):
        reset_config(HEARTBEAT_HOURS=0, SEARCH_QUERIES=["iPhone 13"])
        with TempDir():
            _, log = run({"ipad": [item(1, "iPad Air 5 64GB", 300)]})
            self.assertNotIn("Apple produktai", log)

    def test_only_lithuanian(self):
        """Tik Lietuvos pardavejai: uzsienio kalba ir zlotu kainos (su centais) – be uzklausu,
        uzsienio pardavejas – pagal salies uzklausa; salies nezinant neirasoma."""
        catalog = {"ipad": [item(1, "iPad Air 5 64GB", 300, user_id=1),
                            item(2, "Tablet iPad 9 generacji, świetny stan", 166),
                            item(3, "iPad 9 64GB", 166.7, user_id=3),
                            item(4, "iPad Pro 11 M1 128GB", 450, user_id=4)],
                   "macbook": []}
        with TempDir():
            _, log = run(catalog, users={4: {"country_code": "LV"}})
            ev = [e for e in archive.read() if e["e"] in ("pobs", "px")]
            self.assertEqual([e["id"] for e in ev if e["e"] == "pobs"], ["vinted:1"])
            self.assertEqual(next(e for e in ev if e["e"] == "pobs")["ct"], "LT")
            why = {e["id"]: e["why"] for e in ev if e["e"] == "px"}
            self.assertTrue(why["vinted:2"].startswith("kalba"))
            self.assertEqual(why["vinted:3"], "uzsienio kaina (centai)")
            self.assertEqual(why["vinted:4"], "salis (LV)")
            self.assertIn("pardavejo salies uzklausu 2", log)

    def test_english_allowed(self):
        """Lietuviai neretai raso angliskai – EN leidziama (salis vis tiek tikrinama)."""
        catalog = {"ipad": [], "macbook": [item(1, "MacBook Air M1 8GB 256GB space gray, like new", 450)]}
        with TempDir():
            run(catalog)
            self.assertEqual([e["id"] for e in archive.read() if e["e"] == "pobs"], ["vinted:1"])

    def test_v3_rejections_reconsidered(self):
        from vinted.state import write_json
        with TempDir():
            write_json("state.json", {"products": {"vinted:1": [400, 1, 1], "vinted:2": "x"}, "products_v": 3})
            st = State.load()
            self.assertEqual(st.products, {"vinted:1": [400, 1, 1]})
            write_json("state.json", {"products": {"vinted:1": [400, 1, 1]}, "products_v": 2})
            self.assertEqual(State.load().products, {})

    def test_shop_style_cents_kept(self):
        catalog = {"ipad": [item(1, "iPad Air 5 64GB", 299.99), item(2, "iPad 9 64GB", 182.5),
                            item(3, "iPad Pro 11 M1", 532.28)], "macbook": []}
        with TempDir():
            run(catalog)
            ev = [e for e in archive.read() if e["e"] in ("pobs", "px")]
            self.assertEqual(sorted(e["id"] for e in ev if e["e"] == "pobs"), ["vinted:1", "vinted:2"])
            self.assertEqual([e["why"] for e in ev if e["e"] == "px"], ["uzsienio kaina (centai)"])

    def test_unknown_country_waits(self):
        reset_config(HEARTBEAT_HOURS=0, PRODUCTS_OBSERVE=True, PRODUCT_QUERIES=["ipad"],
                     SEARCH_QUERIES=["iPhone 13"], SELLER_COUNTRY_LOOKUPS=0)
        with TempDir():
            _, log = run({"ipad": [item(1, "iPad Air 5 64GB", 300)]})
            self.assertEqual([e for e in archive.read() if e["e"] in ("pobs", "px")], [])
            self.assertIn("salis nezinoma (kitam paleidimui) 1", log)

    def test_country_lookups_capped(self):
        reset_config(HEARTBEAT_HOURS=0, PRODUCTS_OBSERVE=True, PRODUCT_QUERIES=["ipad"],
                     SEARCH_QUERIES=["iPhone 13"], PRODUCT_COUNTRY_LOOKUPS=2)
        catalog = {"ipad": [item(i, f"iPad Air 5 64GB nr {i}", 300, user_id=i) for i in range(1, 6)]}
        with TempDir():
            _, log = run(catalog)
            self.assertIn("pardavejo salies uzklausu 2, salis nezinoma (kitam paleidimui) 3", log)


    def test_pirkpard(self):
        """Pirkpard: pardavejo salis jau sarase (LT), centai nieko nereiskia, uzklausu nera."""
        from tests.fixtures import pirkpard_response
        from vinted.sources.pirkpard import PirkpardSource

        def row(iid, title, price, country=None):
            return {"id": iid, "title": title, "price": str(price), "currency_code": "EUR",
                    "handle": f"h{iid}", "vendor": {"id": iid, "country": country}}

        class Api:
            last_error = blocked = ""
            def start(self): pass
            def sleep(self, s): pass
            def get_json(self, params, tries=3):
                rows = {"ipad": [row(1, "iPad Air 5 64GB", 299.99), row(2, "iPad dėklas", 10),
                                 row(3, "iPad Pro 11", 400, country="LV")]}.get(params["search"], [])
                return pirkpard_response(rows)

        with TempDir(), contextlib.redirect_stdout(io.StringIO()) as out:
            Run([PirkpardSource(client=Api())], FakeTelegram(), sleep=lambda s: None).run()
            ev = [e for e in archive.read() if e["e"] in ("pobs", "px")]
        self.assertEqual([(e["id"], e["p"], e["ct"]) for e in ev if e["e"] == "pobs"],
                         [("pirkpard:1", 299.99, "LT")])
        self.assertEqual(sorted(e["why"] for e in ev if e["e"] == "px"), ["priedas", "salis (LV)"])
        self.assertIn("Apple produktai [Pirkpard: ipad]: gauta 3, nauju 1", out.getvalue())

    def test_reads_description(self):
        catalog = {"ipad": [], "macbook": [item(1, "MacBook Air 13", 400), item(2, "MacBook Pro 13 M1", 300),
                                          item(3, "MacBook Air M2", 600)]}
        pages = {"1": "M1 2020, 8GB RAM, 256GB SSD", "2": "iCloud užrakintas"}
        statuses = {"3": (404, "")}
        with TempDir():
            _, log = run(catalog, pages=pages, statuses=statuses)
            ev = [e for e in archive.read() if e["e"] in ("pobs", "px")]
            pobs = [e for e in ev if e["e"] == "pobs"]
            self.assertEqual([(e["id"], e["m"], e["ram"], e["st"], e["chip"]) for e in pobs],
                             [("vinted:1", "MacBook Air M1 13", "8 GB", "256 GB", "M1")])
            why = {e["id"]: e["why"] for e in ev if e["e"] == "px"}
            self.assertTrue(why["vinted:2"].startswith("defektas"))
            self.assertEqual(why["vinted:3"], "dingo pries atidarant")
            self.assertIn("atidaryta skelbimu (aprasymui) 3", log)

    def test_details_capped(self):
        reset_config(HEARTBEAT_HOURS=0, PRODUCTS_OBSERVE=True, PRODUCT_QUERIES=["ipad"],
                     SEARCH_QUERIES=["iPhone 13"], PRODUCT_DETAILS_PER_RUN=2)
        catalog = {"ipad": [item(i, f"iPad Air 5 64GB nr {i}", 300) for i in range(1, 6)]}
        with TempDir():
            _, log = run(catalog)
            self.assertEqual(sum(1 for e in archive.read() if e["e"] == "pobs"), 2)
            self.assertIn("atidaryta skelbimu (aprasymui) 2, laukia aprasymo (kitam paleidimui) 3", log)

if __name__ == "__main__":
    unittest.main()
