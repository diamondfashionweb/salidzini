# Salidzini.lv XML — Diamond Fashion

Katru rītu (~06:30) GitHub automātiski izveido svaigu Salidzini.lv XML failu no diamondfashion.co preču datiem:
latviski, ar bildēm, tikai preces, kas pieejamas pārdošanai, bez dāvanu kartēm, lietotām kleitām `<used>1</used>`.

**XML saite Salidzini profilam:** `https://diamondfashionweb.github.io/salidzini/salidzini-lv.xml`

- Palaist ar roku: **Actions → Salidzini XML → Run workflow**
- Pēdējā palaišana: `last-run.txt`, žurnāls: `feed-log.txt`
- Nosaukumi/kategorijas: `curated.json`; jaunām precēm — `feed_rules.py`
- Shopify produkta tagi: `salidzini-exclude` (neiekļaut), `salidzini-no-image` (bez bildes), `salidzini-name:Jauns nosaukums`

## Kaina24.lt XML (Lietuva)

Tas pats GitHub darbs katru rītu izveido arī `kaina24-lt.xml` — lietuviski (`/lt/` saites), pēc Kaina24.lt formāta
(https://www.kaina24.lt/xml/example.xml), ar piegādi uz Lietuvu (paštomāts 4.99 €, 3–4 d.; kurjers 12.00 €, 1–2 d.).

**XML saite Kaina24.lt:** `https://diamondfashionweb.github.io/salidzini/kaina24-lt.xml`

- Kods: `kaina24_feed.py`, kategoriju tulkojumi `lt_rules.py`, LT nosaukumi precēm bez LT tulkojuma: `lt_names.json`
- Žurnāls: `kaina24-log.txt` — ja tur parādās „pavadinimas atrodo latviškas”, pievieno LT nosaukumu `lt_names.json`
- Shopify tagi: `kaina24-exclude` (neiekļaut LT), `kaina24-name:Naujas pavadinimas`
- Iekļauj tikai preces ar bildi un pieejamas pārdošanai. **Precīzs atlikums > 0 un `<stock>`**: repozitorijā
  Settings → Secrets and variables → Actions pievieno `SHOPIFY_STORE`, `SHOPIFY_CLIENT_ID`, `SHOPIFY_CLIENT_SECRET`.
