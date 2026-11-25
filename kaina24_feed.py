#!/usr/bin/env python3
"""Kaina24.lt XML plūsma (Lietuva) — Diamond Fashion.

Tie paši veikala dati kā Salidzini.lv, bet lietuviski (/lt/), pēc Kaina24.lt formāta
(https://www.kaina24.lt/xml/example.xml). Izvade: kaina24-lt.xml

  python3 kaina24_feed.py

Noteikumi kā Salidzini: bez dāvanu kartēm, 0 € dāvanām, TEST precēm, tikai pieejamās preces,
lietotām kleitām <condition>used</condition>. Tags kaina24-exclude (vai salidzini-exclude)
izslēdz preci, kaina24-name:Jauns pavadinimas aizvieto nosaukumu.
"""
import html
import json
import re
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from feed_rules import classify  # noqa: E402
from lt_rules import LV_CHARS, category_lt, clean_name_lt  # noqa: E402
from salidzini_feed import SHOP, access_token, fetch_products, gql, load_env  # noqa: E402

FILENAME = "kaina24-lt.xml"
LOGFILE = "kaina24_feed.log"
UTM = "utm_source=kaina24.lt&utm_medium=referral&utm_campaign=product_catalog"
EXCLUDE_TAGS = {"do-not-publish", "internal-gift", "salidzini-exclude", "kaina24-exclude"}
BRAND = "Diamond Fashion"
MAX_EXTRA_IMAGES = 4
# Pristatymas į Lietuvą (diamondfashion.co/lt/pages/pristatymas)
DELIVERY = {
    "parcel_locker_delivery": ("3-4", "4.99"),
    "home_delivery": ("1-2", "12.00"),  # skubus pristatymas
}


def log(msg):
    line = f"{datetime.now():%Y-%m-%d %H:%M:%S} {msg}"
    print(line)
    with open(HERE / LOGFILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def cdata(s):
    return "<![CDATA[" + str(s).replace("]]>", "]]]]><![CDATA[>") + "]]>"


def plain_text(body, limit=1500):
    s = re.sub(r"<(script|style).*?</\1>", " ", body or "", flags=re.S | re.I)
    s = re.sub(r"<br\s*/?>|</p>|</h\d>|</li>", "\n", s, flags=re.I)
    s = html.unescape(re.sub(r"<[^>]+>", " ", s))
    s = "\n".join(re.sub(r"[ \t\xa0]+", " ", ln).strip() for ln in s.splitlines())
    s = re.sub(r"\n{2,}", "\n", s).strip()
    if len(s) > limit:
        s = s[:limit].rsplit(" ", 1)[0] + "…"
    return s


def fetch_qty(env, token):
    """{variant_id: daudzums}; neizsekotiem variantiem None (pieejams, daudzums nezināms)."""
    qty, cursor = {}, None
    while True:
        d = gql(env, token, """query($c:String){ productVariants(first:250, after:$c){
            pageInfo{ hasNextPage endCursor }
            nodes{ legacyResourceId inventoryQuantity inventoryItem{ tracked } } } }""",
                {"c": cursor})["productVariants"]
        for n in d["nodes"]:
            qty[int(n["legacyResourceId"])] = (n["inventoryQuantity"] or 0) if n["inventoryItem"]["tracked"] else None
        if not d["pageInfo"]["hasNextPage"]:
            return qty
        cursor = d["pageInfo"]["endCursor"]


def build_items(qty=None):
    curated = json.loads((HERE / "curated.json").read_text(encoding="utf-8"))
    lt_names = json.loads((HERE / "lt_names.json").read_text(encoding="utf-8"))
    lt = fetch_products("/lt")
    items, skipped, warn = [], [], []
    for p in lt:
        tags = set(p.get("tags", []))
        if qty is not None:
            # tikai atlikums > 0 (neizsekotus variantus neiekļaujam — daudzums nav zināms)
            avail = [v for v in p["variants"] if (qty.get(v["id"]) or 0) > 0]
        else:
            avail = [v for v in p["variants"] if v["available"]]
        avail.sort(key=lambda v: float(v["price"]))
        ptype = (p.get("product_type") or "").lower()
        title_up = p["title"].upper()
        reason = None
        if "gift card" in ptype or "dovanų kortel" in ptype or "dāvanu karte" in ptype:
            reason = "dovanų kortelė"
        elif not avail:
            reason = "nav noliktavā"
        elif float(avail[0]["price"]) <= 0:
            reason = "cena 0"
        elif not p.get("images"):
            reason = "nav bildes"
        elif tags & EXCLUDE_TAGS:
            reason = "izslēgšanas tags"
        elif any(t in title_up for t in ("TEST PRODUCT", "TESTA PRODUKTS", "BANDOMOJI PREKĖ", "BANDOMASIS PRODUKTAS")):
            reason = "testa prece"
        if reason:
            skipped.append((reason, p["title"]))
            continue

        c = curated.get(str(p["id"]))
        if c:
            cat_lv, used = c["category"], c["used"]
        else:
            cat_lv, used = classify(p.get("product_type", ""), p["title"], p["handle"])
        cat, unknown = category_lt(cat_lv)
        if unknown:
            warn.append(f"kategorija bez LT tulkojuma: {unknown} ({p['handle']})")
        override = next((t.split(":", 1)[1].strip() for t in tags if t.startswith("kaina24-name:")), None)
        if not override and str(p["id"]) in lt_names:
            override = "Diamond Fashion " + lt_names[str(p["id"])]
        name = override or clean_name_lt(p["title"])
        if LV_CHARS.search(name):
            warn.append(f"pavadinimas atrodo latviškas (pridėk į lt_names.json): {p['id']} {name}")

        v = avail[0]
        images = [i["src"] for i in p.get("images") or []]
        stock = None
        if qty is not None:
            stock = sum(qty[x["id"]] for x in avail)
        items.append({
            "id": str(p["id"]),
            "title": name[:200],
            "price": f"{float(v['price']):.2f}",
            "condition": "used" if used else "new",
            "stock": stock,
            "ean": (v.get("barcode") or "").strip(),
            "image": images[0] if images else "",
            "extra_images": images[1:1 + MAX_EXTRA_IMAGES],
            "url": f"{SHOP}/lt/products/{p['handle']}?variant={v['id']}&{UTM}",
            "category": cat,
            "description": plain_text(p.get("body_html")),
        })
    return items, skipped, warn


def to_xml(items):
    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           f"<!-- Diamond Fashion; Kaina24.lt; generated {datetime.now(timezone.utc).isoformat(timespec='seconds')} -->",
           "<products>"]
    for it in items:
        out += [f'<product id="{it["id"]}">',
                f"<title>{cdata(it['title'])}</title>",
                f"<price>{it['price']}</price>",
                f"<condition>{it['condition']}</condition>"]
        if it["stock"] is not None:
            out.append(f"<stock>{it['stock']}</stock>")
        if re.fullmatch(r"\d{8,13}", it["ean"]):
            out.append(f"<ean_code>{it['ean']}</ean_code>")
        out += [f"<manufacturer>{cdata(BRAND)}</manufacturer>",
                f"<image_url>{cdata(it['image'])}</image_url>"]
        if it["extra_images"]:
            out.append("<additional_images>")
            out += [f"<image>{cdata(u)}</image>" for u in it["extra_images"]]
            out.append("</additional_images>")
        out += [f"<product_url>{cdata(it['url'])}</product_url>",
                f"<category_name>{cdata(it['category'])}</category_name>",
                f"<description>{cdata(it['description'])}</description>",
                "<delivery>"]
        for tag, (days, price) in DELIVERY.items():
            out.append(f"<{tag}><working_days>{days}</working_days><price>{price}</price></{tag}>")
        out += ["</delivery>", "</product>"]
    out.append("</products>")
    return "\n".join(out) + "\n"


def main():
    try:
        env = load_env()
        qty = None
        if env.get("SHOPIFY_STORE") and (env.get("SHOPIFY_ADMIN_TOKEN") or
                                         (env.get("SHOPIFY_CLIENT_ID") and env.get("SHOPIFY_CLIENT_SECRET"))):
            qty = fetch_qty(env, access_token(env))
        else:
            log("Brīdinājums: nav Shopify atslēgu — pieejamība pēc publiskās 'available', bez <stock>")
        items, skipped, warn = build_items(qty)
        xml = to_xml(items)
        ET.fromstring(xml.encode("utf-8"))  # validācija
        minimum = int(env.get("SHOPIFY_MIN_ITEMS", "50"))
        if len(items) < minimum:
            raise RuntimeError(f"tikai {len(items)} preces (< {minimum}) — failu neaizvietoju")
        (HERE / FILENAME).write_text(xml, encoding="utf-8")
        log(f"OK: {len(items)} preces, izslēgtas {len(skipped)} -> {FILENAME}")
        for w in warn:
            log("  " + w)
    except Exception as e:  # noqa: BLE001
        log(f"KĻŪDA: {type(e).__name__}: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
