# -*- coding: utf-8 -*-
"""Apple produktai be telefonu: iPad, MacBook, AirPods, iMac, Mac mini.

RINKIMO REZIMAS (PRODUCTS_OBSERVE): skelbimai tik atpazistami ir irasomi i archyva
(`pobs` – pirma karta pamatytas, `pprice` – pasikeite kaina, `px` – atmestas: priedas,
dalis, kopija). Nieko nesiunciama. Kai kiekvienam modeliui susikaups pakankamai kainu,
is to paties archyvo bus skaiciuojama rinkos kaina ir ijungiamas siuntimas i APPLE tema.

Uzklausos: tik katalogo puslapiai (be skelbimo puslapio ir be pardavejo salies), ir
paieska sustoja, kai puslapyje visi skelbimai jau matyti – iprastai 1 uzklausa produktui.
"""

import re

from .util import fold

CATEGORIES = ("ipad", "macbook", "airpods", "imac", "mac_mini")
LABELS = {"ipad": "iPad", "macbook": "MacBook", "airpods": "AirPods", "imac": "iMac", "mac_mini": "Mac mini"}

_PHONE_RE = re.compile(r"\biphone\b|\bgalaxy\b|\bsamsung\b|\bxiaomi\b|\bpixel\b")

# Priedas bet kurioje pavadinimo vietoje, jei nera „su / + / dovanu“ (tada tai produktas su priedu):
# „MacBook pakrovėjas“, „iPad Pro 11 dėklas“, „AirPods Pro dėkliukas“
_ACCESSORY_RE = re.compile(
    r"\b(?:dekl\w*|dekliuk\w*|case|cases|cover|futliar\w*|pakrov\w*|krovikl\w*|charger|adapter\w*|"
    r"kabel\w*|cable|laidas|laidai|klaviatur\w*|keyboard|pencil|piestuk\w*|stylus|plevel\w*|"
    r"stiklel\w*|screen protector|apsaugin\w*|sleeve|krepsel\w*|kuprin\w*|maisel\w*|stovel\w*|stovas|"
    r"stand|laikikl\w*|holder|dock\w*|hub|pele|mouse|trackpad|ear ?tips|antgal\w*|kamstel\w*|"
    r"lipduk\w*|sticker\w*|skin)\b")
_BUNDLE_RE = re.compile(r"\+|&|\b(?:su|with|ir|bei|kartu|plius|komplekt\w*|dovan\w*|pridedu|"
                        r"pridedam\w*|gratis|included|iskaitant)\b")
# Priedas TAM produktui: „skirtas iPad“, „for MacBook Air“, „tinka AirPods Pro“
_FOR_PRODUCT_RE = re.compile(r"\b(?:for|skirt\w*|tinka|compatible|fur|pour)\s+(?:apple\s+)?"
                             r"(?:i ?pad|mac ?book|air ?pods?|imac|mac ?mini)")
# Dalis, ne visas produktas
_PART_RE = re.compile(
    r"\b(?:dalims|for parts|parts only|detal\w*|donor\w*|ekranas|ekrano|matric\w*|lcd|display|"
    r"korpus\w*|motinin\w*|plokst\w*|logic board|motherboard|baterija|battery|"
    r"(?:vienas|viena|tik|kairys|kaire|desinys|desine|left|right|single|one)\s+(?:ausinuk\w*|earbud\w*|airpod\b)|"
    r"(?:kairys|kaire|desinys|desine|left|right)\s+(?:air ?pods?\s+)?(?:pro\s+)?(?:\d\s+)?ausinuk\w*|"
    r"tik (?:dezut\w*|dekl\w*|pakrov\w*)|box only|empty box|tuscia dezute)\b")
# Kopijos / replikos (ypac AirPods)
_FAKE_RE = re.compile(r"(?<!\bne )\b(?:kopij\w*|replik\w*|replica|clone|klon\w*|fake|high copy|"
                      r"aaa|master copy|1\s?:\s?1|ne originali\w*|neoriginal\w*)\b")

_CHIP_RE = re.compile(r"\bm\s?([1-5])(?:\s?(pro|max|ultra))?\b")
_INTEL_RE = re.compile(r"\bintel\b|\bi[3579]\b|\bcore\b")
_YEAR_RE = re.compile(r"\b(20(?:0[89]|1\d|2[0-6]))\b")


def _norm(title):
    t = fold((title or "").lower())
    t = re.sub(r"(\d)[\.,](\d)", r"\1.\2", t)           # 12,9 -> 12.9
    return re.sub(r"[\-_/,()\[\]|!?\"'“”„]+", " ", t)


def category(title):
    t = _norm(title)
    if _PHONE_RE.search(t):
        return None                                       # telefonai tikrinami atskirai
    if re.search(r"\bmac\s?mini\b", t):
        return "mac_mini"
    if re.search(r"\bimac\b", t):
        return "imac"
    if re.search(r"\bmac\s?book\b", t):
        return "macbook"
    if re.search(r"\bair\s?pods?\b", t):
        return "airpods"
    if re.search(r"\bi\s?pad\b", t):
        return "ipad"
    return None


_GB_RE = re.compile(r"\b(8|16|18|24|32|36|48|64|96|128|256|512)\s?(?:gb|g)\b(\s?(?:ram|unified))?")
_TB_RE = re.compile(r"\b([1248])\s?tb\b")


_SLASH_RE = re.compile(r"\b(8|16|18|24|32|36|48|64)\s?(?:gb)?\s?/\s?(128|256|512|1|2)\s?(gb|tb)?\b", re.I)


def _slash(text):
    """„8/256“, „16GB/512GB“, „16/1TB“ -> (RAM, diskas)."""
    m = _SLASH_RE.search(text or "")
    if not m:
        return None
    disk = m.group(2)
    return f"{m.group(1)} GB", (f"{disk} TB" if disk in ("1", "2") else f"{disk} GB")


def extract_storage(text, computer=False):
    """Diskas. Kompiuteriu pavadinime dazniausiai abu: „16GB 512GB“ – diskas didesnysis
    (>=128 GB arba TB), RAM – mazesnysis. iPad ir AirPods – pirmas skaicius."""
    if computer and _slash(text):
        return _slash(text)[1]
    t = _norm(text)
    tb = _TB_RE.search(t)
    gbs = [(int(m.group(1)), bool(m.group(2))) for m in _GB_RE.finditer(t)]
    if computer:
        if tb:
            return f"{tb.group(1)} TB"
        disks = [v for v, is_ram in gbs if v >= 128 and not is_ram]
        return f"{max(disks)} GB" if disks else None
    for v, is_ram in gbs:
        if v >= 16 and not is_ram:
            return f"{v} GB"
    return f"{tb.group(1)} TB" if tb else None


def extract_ram(text):
    """Kompiuterio RAM: pazymetas „ram“ arba mazesnis skaicius salia disko („8GB 256GB“)."""
    if _slash(text):
        return _slash(text)[0]
    gbs = [(int(m.group(1)), bool(m.group(2))) for m in _GB_RE.finditer(_norm(text))]
    marked = [v for v, is_ram in gbs if is_ram]
    if marked:
        return f"{marked[0]} GB"
    small = [v for v, _ in gbs if v <= 64]
    return f"{small[0]} GB" if small else None        # kompiuteriu diskas niekada < 128 GB


def _chip(t):
    m = _CHIP_RE.search(t)
    if m:
        return "M" + m.group(1) + (" " + m.group(2).capitalize() if m.group(2) else "")
    if _INTEL_RE.search(t):
        y = _YEAR_RE.search(t)
        return "Intel" + (" " + y.group(1) if y else "")
    return None


def _size(t, allowed):
    for m in re.finditer(r"\b(\d{1,2}(?:\.\d)?)(?![\d.])(?!\s?(?:gb|g\b|tb|w\b|%|mah|hz|ram|gen|th\b|kart))", t):
        v = m.group(1)
        if v in allowed:
            return allowed[v]
    return None


def _ipad_model(t):
    gen = re.search(r"\b(\d{1,2})\s?(?:th|rd|nd|st)?\s?(?:gen\w*|kart\w*|generation)\b", t)
    gen = gen.group(1) if gen else None
    if re.search(r"\bpro\b", t):
        size = _size(t, {"13": "13", "12.9": "12.9", "11": "11", "10.5": "10.5", "9.7": "9.7"})
        chip = _CHIP_RE.search(t)
        parts = ["iPad Pro", size, ("M" + chip.group(1)) if chip else (f"{gen} kart." if gen else None)]
        return " ".join(p for p in parts if p)
    if re.search(r"\bair\b", t):
        chip = _CHIP_RE.search(t)
        if chip:
            size = _size(t, {"13": "13", "11": "11"})
            return " ".join(p for p in ["iPad Air", "M" + chip.group(1), size] if p)
        g = gen or (re.search(r"\bair\s?([2-5])\b", t) or [None, None])[1]
        return f"iPad Air {g}" if g else "iPad Air"
    if re.search(r"\bmini\b", t):
        g = gen or (re.search(r"\bmini\s?([2-7])\b", t) or [None, None])[1]
        if not g and re.search(r"\ba17\b", t):
            g = "7"
        return f"iPad mini {g}" if g else "iPad mini"
    g = gen or (re.search(r"\bi\s?pad\s?(1[01]|[5-9])\b", t) or [None, None])[1]
    if not g:
        y = _YEAR_RE.search(t)
        g = {"2017": "5", "2018": "6", "2019": "7", "2020": "8", "2021": "9", "2022": "10",
             "2025": "11"}.get(y.group(1)) if y else None
    return f"iPad {g}" if g else "iPad"


def _macbook_model(t):
    line = "MacBook Pro" if re.search(r"\bpro\b(?!\s?(?:max|ultra))|\bmac\s?book\s?pro\b", t) else \
        "MacBook Air" if re.search(r"\bair\b", t) else "MacBook"
    chip = _chip(t)
    if chip and chip.startswith("M") and line == "MacBook Pro" and not re.search(r"\bmac\s?book\s?pro\b", t):
        # „MacBook Air M2 Pro“ nebuna – „pro“ buvo cipo dalis (M1 Pro), ne linija
        line = "MacBook Air" if re.search(r"\bair\b", t) else "MacBook Pro"
    size = _size(t, {"13": "13", "13.3": "13", "13.6": "13", "14": "14", "14.2": "14", "15": "15",
                     "15.3": "15", "15.4": "15", "16": "16", "16.2": "16", "12": "12"})
    return " ".join(p for p in [line, chip, size] if p)


def _airpods_model(t):
    if re.search(r"\bmax\b", t):
        return "AirPods Max"
    if re.search(r"\bpro\b", t):
        if re.search(r"\bpro\s?(?:3|iii)\b|\b3(?:rd)?\s?gen", t):
            return "AirPods Pro 3"
        if re.search(r"\bpro\s?(?:2|ii)\b|\b2(?:nd)?\s?gen|\bantr\w* kart|usb\s?c|magsafe usb", t):
            return "AirPods Pro 2"
        return "AirPods Pro"
    m = re.search(r"\bair\s?pods?\s?([1-4])\b|\b([1-4])(?:st|nd|rd|th)?\s?(?:gen\w*|kart\w*)\b", t)
    if m:
        return f"AirPods {m.group(1) or m.group(2)}"
    return "AirPods"


def _desktop_model(t, name, sizes):
    chip = _chip(t)
    size = _size(t, sizes) if sizes else None
    return " ".join(p for p in [name, size, chip] if p)


def detect(title):
    """{'cat', 'model', 'storage', 'ram'} arba None (ne Apple produktas / telefonas)."""
    cat = category(title)
    if cat is None:
        return None
    t = _norm(title)
    model = {"ipad": _ipad_model, "macbook": _macbook_model, "airpods": _airpods_model,
             "imac": lambda s: _desktop_model(s, "iMac", {"24": "24", "27": "27", "21.5": "21.5", "21": "21.5"}),
             "mac_mini": lambda s: _desktop_model(s, "Mac mini", None)}[cat](t)
    computer = cat in ("macbook", "imac", "mac_mini")
    return {"cat": cat, "model": model, "storage": extract_storage(title, computer),
            "ram": extract_ram(title) if computer else None}


def reject_reason(title):
    """Kodel skelbimas netinka rinkos kainai: 'priedas', 'dalis', 'kopija' arba None."""
    t = _norm(title)
    if _FAKE_RE.search(t):
        return "kopija"
    if _PART_RE.search(t):
        return "dalis"
    if _FOR_PRODUCT_RE.search(t):
        return "priedas"
    first = t.split(None, 1)[0] if t.strip() else ""
    if first and _ACCESSORY_RE.fullmatch(first):
        return "priedas"
    if _ACCESSORY_RE.search(t) and not _BUNDLE_RE.search(t):
        return "priedas"
    return None
