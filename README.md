# Salidzini.lv XML — Diamond Fashion

Katru rītu (~06:30) GitHub automātiski izveido svaigu Salidzini.lv XML failu no diamondfashion.co preču datiem:
latviski, ar bildēm, tikai preces, kas pieejamas pārdošanai, bez dāvanu kartēm, lietotām kleitām `<used>1</used>`.

**XML saite Salidzini profilam:** `https://diamondfashionweb.github.io/salidzini/salidzini-lv.xml`

- Palaist ar roku: **Actions → Salidzini XML → Run workflow**
- Pēdējā palaišana: `last-run.txt`, žurnāls: `feed-log.txt`
- Nosaukumi/kategorijas: `curated.json`; jaunām precēm — `feed_rules.py`
- Shopify produkta tagi: `salidzini-exclude` (neiekļaut), `salidzini-no-image` (bez bildes), `salidzini-name:Jauns nosaukums`
