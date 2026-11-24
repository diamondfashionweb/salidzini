#!/usr/bin/env python3
"""Salidzini.lv XML plūsma — Diamond Fashion.

Ģenerē XML no veikala aktuālajiem datiem un aizvieto Shopify Files failu
salidzini-lv.xml (cdn.shopify.com saite, ko Shopify nebloķē Salidzini robotam).

  python3 salidzini_feed.py            # tikai ģenerē salidzini-lv.xml (pārbaudei)
  python3 salidzini_feed.py --upload   # ģenerē un augšupielādē uz Shopify Files

Iestatījumi: .env failā blakus šim skriptam (skat. .env.example).
"""
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from xml.sax.saxutils import escape

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from feed_rules import classify, clean_name  # noqa: E402
SHOP = "https://diamondfashion.co"
FILENAME = "salidzini-lv.xml"
API_VERSION = "2026-10"
UTM = "utm_source=salidzini.lv&utm_medium=referral&utm_campaign=product_catalog"
EXCLUDE_TAGS = {"do-not-publish", "internal-gift", "salidzini-exclude"}
UA = "DiamondFashion-SalidziniFeed/1.0"
ALL_IMAGES = True  # bilde visām precēm (izņemot tagu salidzini-no-image)


def log(msg):
    line = f"{datetime.now():%Y-%m-%d %H:%M:%S} {msg}"
    print(line)
    with open(HERE / "salidzini_feed.log", "a", encoding="utf-8") as f:
        f.write(line + "\n")


def load_env():
    env = {}
    p = HERE / ".env"
    if p.exists():
        for line in p.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip().strip('"').strip("'")
    env.update({k: v for k, v in os.environ.items() if k.startswith("SHOPIFY_")})
    return env


def http(url, data=None, headers=None, method=None, tries=4):
    for attempt in range(tries):
        req = urllib.request.Request(url, data=data, headers={"User-Agent": UA, **(headers or {})},
                                     method=method)
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 504) and attempt < tries - 1:
                time.sleep(15 * (attempt + 1))
                continue
            raise


def fetch_products(prefix):
    products, page = [], 1
    while True:
        batch = json.loads(http(f"{SHOP}{prefix}/products.json?limit=250&page={page}"))["products"]
        products += batch
        if len(batch) < 250:
            return products
        page += 1


def build_items(stock=None):
    """stock: {variant_id: True/False} — vai variantam ir vismaz 1 vienība noliktavā.
    Ja None (nav Shopify atslēgu), izmanto publisko 'available' pazīmi."""
    curated = json.loads((HERE / "curated.json").read_text(encoding="utf-8"))
    lv = fetch_products("/lv")
    en = {p["id"]: p for p in fetch_products("")}
    items, skipped, new = [], [], []
    for p in lv:
        e = en.get(p["id"], p)
        tags = set(e.get("tags", []))
        in_stock = (lambda v: stock.get(v["id"], False)) if stock is not None else (lambda v: v["available"])
        avail = sorted((v for v in e["variants"] if in_stock(v)), key=lambda v: float(v["price"]))
        ptype = e.get("product_type", "").lower()
        reason = None
        if "gift card" in ptype or "dāvanu karte" in p.get("product_type", "").lower():
            reason = "dāvanu karte"
        elif not avail:
            reason = "nav noliktavā"
        elif float(avail[0]["price"]) <= 0:
            reason = "cena 0"
        elif tags & EXCLUDE_TAGS:
            reason = "izslēgšanas tags"
        elif "TEST PRODUCT" in p["title"].upper() or "TESTA PRODUKTS" in p["title"].upper():
            reason = "testa prece"
        if reason:
            skipped.append((reason, p["title"]))
            continue

        v = avail[0]
        c = curated.get(str(p["id"]))
        override = next((t.split(":", 1)[1].strip() for t in tags if t.startswith("salidzini-name:")), None)
        if c:
            name, cat, used, image_ok = clean_name(c["name"], []), c["category"], c["used"], c["image_ok"]
        else:
            name = clean_name(p["title"], list(tags))
            cat, used = classify(p.get("product_type", ""), p["title"], p["handle"])
            image_ok = "salidzini-image" in tags
            new.append(name)
        if override:
            name = override
        if ALL_IMAGES or "salidzini-image" in tags:
            image_ok = True
        if "salidzini-no-image" in tags:
            image_ok = False
        img = (e.get("images") or [{}])[0].get("src", "") if image_ok else ""
        items.append({
            "name": name[:200],
            "link": f"{SHOP}/lv/products/{p['handle']}?variant={v['id']}&{UTM}",
            "price": f"{float(v['price']):.2f}",
            "image": img,
            "category_full": cat[:200],
            "ean": v.get("barcode") or "",
            "used": "1" if used else "",
        })
    return items, skipped, new


def to_xml(items):
    out = ['<?xml version="1.0" encoding="utf-8"?>',
           f"<!-- Diamond Fashion; generated {datetime.now(timezone.utc).isoformat(timespec='seconds')} -->",
           "<root>"]
    for it in items:
        out += ["<item>",
                f"<name><![CDATA[{it['name']}]]></name>",
                f"<link>{escape(it['link'])}</link>",
                f"<price>{it['price']}</price>",
                f"<image>{escape(it['image'])}</image>",
                f"<category_full>{escape(it['category_full'])}</category_full>",
                "<brand>Diamond Fashion</brand>"]
        if it["ean"]:
            out.append(f"<ean>{escape(it['ean'])}</ean>")
        out += [f"<used>{it['used']}</used>", "<adult>no</adult>", "</item>"]
    out.append("</root>")
    return "\n".join(out) + "\n"


# ---------------- Shopify Admin API ----------------

def access_token(env):
    shop = env["SHOPIFY_STORE"]
    if env.get("SHOPIFY_ADMIN_TOKEN"):
        return env["SHOPIFY_ADMIN_TOKEN"]
    body = urllib.parse.urlencode({"grant_type": "client_credentials",
                                   "client_id": env["SHOPIFY_CLIENT_ID"],
                                   "client_secret": env["SHOPIFY_CLIENT_SECRET"]}).encode()
    r = json.loads(http(f"https://{shop}/admin/oauth/access_token", data=body,
                        headers={"Content-Type": "application/x-www-form-urlencoded"}))
    return r["access_token"]


def gql(env, token, query, variables=None):
    r = json.loads(http(f"https://{env['SHOPIFY_STORE']}/admin/api/{API_VERSION}/graphql.json",
                        data=json.dumps({"query": query, "variables": variables or {}}).encode(),
                        headers={"Content-Type": "application/json", "X-Shopify-Access-Token": token}))
    if r.get("errors"):
        raise RuntimeError(f"GraphQL: {r['errors']}")
    return r["data"]


def fetch_stock(env, token):
    """Variantiem ar izsekotu atlikumu: True tikai, ja daudzums > 0.
    Neizsekotiem variantiem (atlikums netiek skaitīts) — True."""
    stock, cursor = {}, None
    while True:
        d = gql(env, token, """query($c:String){ productVariants(first:250, after:$c){
            pageInfo{ hasNextPage endCursor }
            nodes{ legacyResourceId inventoryQuantity inventoryItem{ tracked } } } }""",
                {"c": cursor})["productVariants"]
        for n in d["nodes"]:
            tracked = n["inventoryItem"]["tracked"]
            stock[int(n["legacyResourceId"])] = (n["inventoryQuantity"] or 0) > 0 if tracked else True
        if not d["pageInfo"]["hasNextPage"]:
            return stock
        cursor = d["pageInfo"]["endCursor"]


def multipart(fields, file_field, filename, content, ctype):
    b = uuid.uuid4().hex
    parts = []
    for k, v in fields:
        parts.append(f'--{b}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode())
    parts.append(f'--{b}\r\nContent-Disposition: form-data; name="{file_field}"; filename="{filename}"\r\n'
                 f"Content-Type: {ctype}\r\n\r\n".encode() + content + b"\r\n")
    parts.append(f"--{b}--\r\n".encode())
    return b"".join(parts), f"multipart/form-data; boundary={b}"


def upload(env, token, xml_bytes):
    existing = gql(env, token, """query($q:String!){ files(first:10, query:$q){ nodes{
        id fileStatus ... on GenericFile { url } } } }""", {"q": f"filename:{FILENAME}"})["files"]["nodes"]
    existing = [f for f in existing if (f.get("url") or "").split("?")[0].endswith("/" + FILENAME)]

    target = gql(env, token, """mutation($i:[StagedUploadInput!]!){ stagedUploadsCreate(input:$i){
        stagedTargets{ url resourceUrl parameters{ name value } } userErrors{ field message } } }""",
                 {"i": [{"filename": FILENAME, "mimeType": "text/xml", "resource": "FILE",
                         "httpMethod": "POST", "fileSize": str(len(xml_bytes))}]})["stagedUploadsCreate"]
    if target["userErrors"]:
        raise RuntimeError(target["userErrors"])
    t = target["stagedTargets"][0]
    body, ctype = multipart([(p["name"], p["value"]) for p in t["parameters"]], "file", FILENAME,
                            xml_bytes, "text/xml")
    http(t["url"], data=body, headers={"Content-Type": ctype}, method="POST")

    if existing:
        res = gql(env, token, """mutation($f:[FileUpdateInput!]!){ fileUpdate(files:$f){
            files{ id } userErrors{ field message } } }""",
                  {"f": [{"id": existing[0]["id"], "originalSource": t["resourceUrl"]}]})["fileUpdate"]
    else:
        res = gql(env, token, """mutation($f:[FileCreateInput!]!){ fileCreate(files:$f){
            files{ id } userErrors{ field message } } }""",
                  {"f": [{"originalSource": t["resourceUrl"], "filename": FILENAME,
                          "contentType": "FILE"}]})["fileCreate"]
    if res["userErrors"]:
        raise RuntimeError(res["userErrors"])
    fid = res["files"][0]["id"]

    for _ in range(30):
        node = gql(env, token, """query($id:ID!){ node(id:$id){ ... on GenericFile {
            fileStatus url fileErrors{ message } } } }""", {"id": fid})["node"]
        if node["fileStatus"] == "READY":
            return node["url"]
        if node["fileStatus"] == "FAILED":
            raise RuntimeError(f"Shopify file FAILED: {node['fileErrors']}")
        time.sleep(4)
    raise RuntimeError("Shopify fails nav gatavs pēc 2 min")


def main():
    do_upload = "--upload" in sys.argv
    try:
        env = load_env()
        has_creds = bool(env.get("SHOPIFY_STORE") and (env.get("SHOPIFY_ADMIN_TOKEN") or
                                                       (env.get("SHOPIFY_CLIENT_ID") and env.get("SHOPIFY_CLIENT_SECRET"))))
        token, stock = None, None
        if has_creds:
            token = access_token(env)
            stock = fetch_stock(env, token)  # precīzs atlikums: 0 vienību -> nav failā
        elif do_upload:
            raise RuntimeError(".env failā nav Shopify atslēgu (SHOPIFY_CLIENT_ID / SHOPIFY_CLIENT_SECRET)")
        else:
            log("Brīdinājums: nav Shopify atslēgu — atlikums pēc publiskās 'available' pazīmes")
        items, skipped, new = build_items(stock)
        xml = to_xml(items)
        ET.fromstring(xml.encode("utf-8"))  # validācija
        minimum = int(env.get("SHOPIFY_MIN_ITEMS", "50"))
        if len(items) < minimum:
            raise RuntimeError(f"tikai {len(items)} preces (< {minimum}) — neaugšupielādēju, pārbaudi veikalu")
        out = HERE / FILENAME
        out.write_text(xml, encoding="utf-8")
        log(f"OK: {len(items)} preces, izslēgtas {len(skipped)}, ar bildi {sum(1 for i in items if i['image'])} -> {out.name}")
        for n in new:
            log(f"  jauna prece bez curated nosaukuma: {n}")
        if do_upload:
            url = upload(env, token, xml.encode("utf-8"))
            log(f"Augšupielādēts: {url}")
    except Exception as e:  # noqa: BLE001 — žurnālā jāredz jebkura kļūda
        log(f"KĻŪDA: {type(e).__name__}: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
