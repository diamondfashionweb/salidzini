"""Igauņu nosaukumi un kategorijas Hind.ee plūsmai (tulkotas no LV kategorijām pa līmeņiem)."""
import re

SEGMENTS = {
    "Sporta deju apģērbs": "Võistlustantsu riided",
    "Sporta deju apavi": "Tantsukingad",
    "Sporta deju aksesuāri": "Tantsuaksessuaarid",
    "Bērniem": "Lastele",
    "Meitenēm": "Tüdrukutele",
    "Zēniem": "Poistele",
    "Sievietēm": "Naistele",
    "Vīriešiem": "Meestele",
    "Vīriešiem un zēniem": "Meestele ja poistele",
    "Deju bodiji": "Tantsubodid (trikood)",
    "Deju krekli-bodiji": "Tantsusärgid-bodid",
    "Deju svārki": "Tantsuseelikud",
    "Deju svārki ar šortiem": "Tantsuseelikud lühikeste pükstega",
    "Deju bikses": "Tantsupüksid",
    "Deju šorti": "Tantsu lühikesed püksid",
    "Deju krekli": "Tantsusärgid",
    "Deju topi": "Tantsutopid ja -pluusid",
    "Deju halāti": "Tantsumantlid",
    "Deju kombinezoni": "Tantsukombinesoonid",
    "Deju jakas un kardigāni": "Tantsujakid ja kardiganid",
    "Treniņu tērpi": "Treeningriided",
    "Treniņu komplekti": "Treeningkomplektid",
    "Deju tērpi": "Tantsukostüümid",
    "Komplekti": "Komplektid",
    "Deju tērpi un treniņu komplekti": "Tantsukostüümid ja treeningkomplektid",
    "Sacensību tērpi": "Võistlusriided",
    "Sacensību komplekti": "Võistluskomplektid",
    "Sacensību tērpi un komplekti": "Võistluskostüümid ja -komplektid",
    "Sporta deju kleitas": "Võistlustantsu kleidid",
    "Sacensību kleitas": "Võistluskleidid",
    "Treniņkleitas": "Treeningkleidid",
    "Deju treniņkleitas": "Treeningkleidid",
    "Deju kurpes bērniem": "Laste tantsukingad",
    "Deju kurpes meitenēm": "Tüdrukute tantsukingad",
    "Deju kurpes zēniem": "Poiste tantsukingad",
    "Deju kurpes sievietēm": "Naiste tantsukingad",
    "Deju kurpes vīriešiem": "Meeste tantsukingad",
    "Standartdeju (balles deju) kurpes": "Standardtantsu kingad",
    "Latīņamerikas deju kurpes": "Ladina tantsu kingad",
    "Balles deju kurpes": "Standardtantsu kingad",
    "Deju kurpju aksesuāri un kopšana": "Tantsukingade tarvikud ja hooldus",
    "Deju zeķes": "Tantsusokid",
    "Deju getras un kāju sildītāji": "Tantsusäärised ja sääresoojendajad",
    "Deju somas": "Tantsukotid",
    "Deju aproces un cimdi": "Tantsukäevõrud ja kindad",
    "Deju jostas": "Tantsuvööd",
    "Matu aksesuāri dejām": "Juukseaksessuaarid tantsuks",
    "Deju rotaslietas": "Tantsuehted",
    "Deju gurnu lakati": "Tantsu puusasallid",
}


def category_et(cat_lv):
    """'A >> B' (LV) -> ('A > B' ET, nezināmie segmenti vai None)."""
    parts, unknown = [], []
    for seg in (s.strip() for s in cat_lv.split(">>")):
        parts.append(SEGMENTS.get(seg, seg))
        if seg not in SEGMENTS:
            unknown.append(seg)
    return " > ".join(parts)[:200], (", ".join(unknown) or None)


# Zīmols tulkots/locīts mašīntulkojumā: "Diamond Fashioni", "DiamondFashioni", "teemantmood", "Teemandi moe"
_BRAND = re.compile(r"Diamond\s*Fashion(?:i|['’]i)?\b|teemant\s*mood|teemandi\s+moe", re.I)
_WORDS = [("lükraboo", "trikoo"), ("tantsubodü", "tantsubodi")]


def clean_name_et(title):
    segs = re.split(r"\s*\|\s*", title)
    segs = [_BRAND.sub(" ", s) for s in segs]
    segs = [re.sub(r"\s{2,}", " ", s).strip(" -–,") for s in segs]
    segs = [s for s in segs if s]
    n = ", ".join(segs)
    for a, b in _WORDS:
        n = n.replace(a, b)
    n = re.sub(r"\s+([,.])", r"\1", n).strip()
    n = n[:1].upper() + n[1:]
    return ("Diamond Fashion " + n)[:200]
