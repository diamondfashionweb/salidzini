"""Automātiskie nosaukuma un kategorijas noteikumi precēm, kuras nav curated.json.

curated.json satur ar roku veidotos nosaukumus/kategorijas (no vecā Liquid feed);
šie noteikumi tiek izmantoti tikai jaunām precēm, kas tur vēl nav ierakstītas.
"""


def clean_name(title, tags):
    for t in tags:
        if t.startswith("salidzini-name:"):
            return t.split(":", 1)[1].strip()[:200]
    n = title
    for a, b in [("| ar kristāliem", ""), ("| Diamond Fashion", ""), ("DiamondFashion", ""),
                 ("Diamond Fashion", ""), ("Dimanta modeļa ", ""), (" | ", ", "), ("|", ", "),
                 ("  ", " "), (" ,", ","), (",,", ",")]:
        n = n.replace(a, b)
    n = n.strip()
    if n[:2] in ("- ", "– ", ", "):
        n = n[2:].strip()
    if n[-1:] in (",", "-", "–"):
        n = n[:-1].strip()
    return ("Diamond Fashion " + n)[:200]


def classify(ptype, title, handle):
    """Atgriež (category_full, used) ar ' >> ' atdalītāju."""
    ty = ptype.lower()
    kt = (title + " " + handle).lower()
    k = ty + " " + kt

    def has(s, *w):
        return any(x in s for x in w)

    if has(k, "zēn", "boys", "boy-", "boy’"):
        aud = "mb" if has(kt, "vīrieš", "mens", "men-", "men’s") else "b"
    elif has(k, "meiten", "girls", "junior"):
        aud = "g"
    elif has(k, "bērn", "kids", "jaunie", "juvenile"):
        aud = "k"
    elif has(k, "sieviet", "women"):
        aud = "w"
    elif has(k, "vīrieš", "mens", "men’s", "men-s"):
        aud = "m"
    else:
        aud = "w"
    root = {
        "g": "Sporta deju apģērbs >> Bērniem >> Meitenēm",
        "k": "Sporta deju apģērbs >> Bērniem",
        "b": "Sporta deju apģērbs >> Bērniem >> Zēniem",
        "m": "Sporta deju apģērbs >> Vīriešiem",
        "mb": "Sporta deju apģērbs >> Vīriešiem un zēniem",
    }.get(aud, "Sporta deju apģērbs >> Sievietēm")
    used = has(k, "preloved", "lietot")
    comp = has(k, "sacensīb", "competition")

    if has(ty, "shoes", "apavi"):
        if aud == "g":
            cat = "Sporta deju apavi >> Deju kurpes bērniem >> Deju kurpes meitenēm"
        elif aud == "k":
            cat = "Sporta deju apavi >> Deju kurpes bērniem"
        elif aud == "b":
            cat = "Sporta deju apavi >> Deju kurpes bērniem >> Deju kurpes zēniem"
        elif aud in ("m", "mb"):
            cat = "Sporta deju apavi >> Deju kurpes vīriešiem >> Balles deju kurpes"
        elif has(kt, "standart", "standard", "balles"):
            cat = "Sporta deju apavi >> Deju kurpes sievietēm >> Standartdeju (balles deju) kurpes"
        else:
            cat = "Sporta deju apavi >> Deju kurpes sievietēm >> Latīņamerikas deju kurpes"
    elif has(ty, "accessor", "aksesu", "socks", "zeķ", "bag", "soma"):
        if has(kt, "kurpju", "apavu", "papēž", "heel", "shoe"):
            cat = "Sporta deju apavi >> Deju kurpju aksesuāri un kopšana"
        elif has(k, "zeķ", "socks"):
            cat = "Sporta deju aksesuāri >> Deju zeķes"
        elif has(kt, "getr", "sildītāj", "warmer"):
            cat = "Sporta deju aksesuāri >> Deju getras un kāju sildītāji"
        elif has(k, "soma", "bag"):
            cat = "Sporta deju aksesuāri >> Deju somas"
        elif has(kt, "aproc", "cimd", "glove", "wrist"):
            cat = "Sporta deju aksesuāri >> Deju aproces un cimdi"
        elif has(kt, "jost", "belt"):
            cat = "Sporta deju aksesuāri >> Deju jostas"
        elif has(kt, "galvas", "head"):
            cat = "Sporta deju aksesuāri >> Matu aksesuāri dejām"
        elif has(kt, "kaklarot", "necklace"):
            cat = "Sporta deju aksesuāri >> Deju rotaslietas"
        elif has(kt, "lakat", "scarf"):
            cat = "Sporta deju aksesuāri >> Deju gurnu lakati"
        else:
            cat = "Sporta deju aksesuāri"
    elif has(ty, "set", "komplekt", "costume", "kostīm"):
        if comp and "kleit" in kt:
            cat = root + " >> Sporta deju kleitas >> Sacensību kleitas"
        elif comp:
            cat = root + " >> Sacensību tērpi un komplekti"
        else:
            cat = root + " >> Deju tērpi un treniņu komplekti"
    elif has(ty, "dress", "kleit"):
        cat = root + (" >> Sporta deju kleitas >> Sacensību kleitas" if comp or used
                      else " >> Sporta deju kleitas >> Deju treniņkleitas")
    elif has(ty, "bodysuit", "bodij"):
        cat = root + (" >> Deju krekli-bodiji" if aud in ("b", "m", "mb") else " >> Deju bodiji")
    elif has(ty, "jumpsuit", "kombinez"):
        cat = root + " >> Deju kombinezoni"
    elif has(ty, "skirt", "svārk"):
        cat = root + (" >> Deju svārki ar šortiem" if has(kt, "šort", "shorts") else " >> Deju svārki")
    elif has(ty, "shorts", "šort"):
        cat = root + " >> Deju šorti"
    elif has(ty, "trousers", "bikses"):
        cat = root + " >> Deju bikses"
    elif has(ty, "robe", "halāt"):
        cat = root + " >> Deju halāti"
    elif has(ty, "jacket", "jaka"):
        cat = root + " >> Deju jakas un kardigāni"
    elif has(ty, "shirt", "krekl"):
        cat = root + " >> Deju krekli"
    elif has(ty, "top", "augša"):
        cat = root + " >> Deju topi"
    else:
        cat = root
    return cat[:200], used
