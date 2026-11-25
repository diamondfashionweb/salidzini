"""Lietuviški nosaukumi un kategorijas Kaina24.lt plūsmai.

Kategorijas tiek tulkotas no tām pašām LV kategorijām, ko izmanto Salidzini
(curated.json / feed_rules.classify), pa vienam līmenim.
"""
import re

SEGMENTS = {
    "Sporta deju apģērbs": "Sportinių šokių apranga",
    "Sporta deju apavi": "Sportinių šokių bateliai",
    "Sporta deju aksesuāri": "Sportinių šokių aksesuarai",
    "Bērniem": "Vaikams",
    "Meitenēm": "Mergaitėms",
    "Zēniem": "Berniukams",
    "Sievietēm": "Moterims",
    "Vīriešiem": "Vyrams",
    "Vīriešiem un zēniem": "Vyrams ir berniukams",
    "Deju bodiji": "Šokių bodžiai (triko)",
    "Deju krekli-bodiji": "Šokių marškiniai-bodžiai",
    "Deju svārki": "Šokių sijonai",
    "Deju svārki ar šortiem": "Šokių sijonai su šortais",
    "Deju bikses": "Šokių kelnės",
    "Deju šorti": "Šokių šortai",
    "Deju krekli": "Šokių marškiniai",
    "Deju topi": "Šokių palaidinės ir topai",
    "Deju halāti": "Šokių chalatai",
    "Deju kombinezoni": "Šokių kombinezonai",
    "Deju jakas un kardigāni": "Šokių striukės ir kardiganai",
    "Treniņu tērpi": "Treniruočių apranga",
    "Treniņu komplekti": "Treniruočių komplektai",
    "Deju tērpi": "Šokių kostiumai",
    "Komplekti": "Komplektai",
    "Deju tērpi un treniņu komplekti": "Šokių kostiumai ir treniruočių komplektai",
    "Sacensību tērpi": "Varžybų apranga",
    "Sacensību komplekti": "Varžybų komplektai",
    "Sacensību tērpi un komplekti": "Varžybų kostiumai ir komplektai",
    "Sporta deju kleitas": "Sportinių šokių suknelės",
    "Sacensību kleitas": "Varžybinės suknelės",
    "Treniņkleitas": "Treniruočių suknelės",
    "Deju treniņkleitas": "Treniruočių suknelės",
    "Deju kurpes bērniem": "Vaikiški šokių bateliai",
    "Deju kurpes meitenēm": "Šokių bateliai mergaitėms",
    "Deju kurpes zēniem": "Šokių bateliai berniukams",
    "Deju kurpes sievietēm": "Moteriški šokių bateliai",
    "Deju kurpes vīriešiem": "Vyriški šokių bateliai",
    "Standartdeju (balles deju) kurpes": "Standartinių (pramoginių) šokių bateliai",
    "Latīņamerikas deju kurpes": "Lotynų Amerikos šokių bateliai",
    "Balles deju kurpes": "Standartinių (pramoginių) šokių bateliai",
    "Deju kurpju aksesuāri un kopšana": "Šokių batelių aksesuarai ir priežiūra",
    "Deju zeķes": "Šokių kojinės",
    "Deju getras un kāju sildītāji": "Šokių getrai ir kojų šildytuvai",
    "Deju somas": "Šokių krepšiai",
    "Deju aproces un cimdi": "Šokių apyrankės ir pirštinės",
    "Deju jostas": "Šokių diržai",
    "Matu aksesuāri dejām": "Plaukų aksesuarai šokiams",
    "Deju rotaslietas": "Šokių papuošalai",
    "Deju gurnu lakati": "Šokių klubų skaros",
}


def category_lt(cat_lv):
    """'A >> B' (LV) -> ('A > B' LT, nezināmie segmenti vai None)."""
    parts, unknown = [], []
    for seg in (s.strip() for s in cat_lv.split(">>")):
        if seg in SEGMENTS:
            parts.append(SEGMENTS[seg])
        else:
            parts.append(seg)
            unknown.append(seg)
    return " > ".join(parts)[:200], (", ".join(unknown) or None)


# Mašīntulkojuma atliekas LT nosaukumos (zīmola nosaukums tulkots, vertikālās svītras u.c.)
_B = r"(?:Diamond\s*Fashion|Deimantin(?:ė|ės)\s+mad(?:a|os))"
_BRAND = re.compile(rf"„\s*{_B}\s*“|{_B}", re.I)
LV_CHARS = re.compile(r"[āēīļņķģ]")


def clean_name_lt(title):
    segs = re.split(r"\s*\|\s*", title)
    segs = [_BRAND.sub(" ", s) for s in segs]
    segs = [re.sub(r"\s{2,}", " ", s).strip(" -–,") for s in segs]
    segs = [s for s in segs if s]
    # Pēdējais segments bieži ir tikai produkta tips (piem. "Kostiumas"), ja tas jau ir nosaukumā — nometam
    if len(segs) > 1 and len(segs[-1].split()) == 1 and segs[-1].lower()[:5] in segs[0].lower():
        segs = segs[:-1]
    n = ", ".join(segs)
    n = re.sub(r"\s+([,.])", r"\1", n).strip()
    n = n[:1].upper() + n[1:]
    return (BRAND_PREFIX + n)[:200]


BRAND_PREFIX = "Diamond Fashion "
