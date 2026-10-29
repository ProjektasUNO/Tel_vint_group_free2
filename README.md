# Vinted parsiuntėjas

GitHub Actions darbas (`.github/workflows/fetch.yml`), kuris parsiunčia nurodytus viešus Vinted puslapius
ir grąžina juos savininko serveriui. Jokio vertinimo, filtrų ar pranešimų čia nėra.

- `fetcher/fetch.py` – parsiuntėjas (leidžiami tik `https://*.vinted.*` adresai).
- `tests/` – parsiuntėjo testai: `python -m unittest discover -s tests`.

Log'e rodoma tik suvestinė: kiek puslapių gauta ir perduota.
