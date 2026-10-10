# Projektterv – PPE demó

Az élő, részletes terv a Claude-on készült dokumentumban van; ez a fájl a fejlesztéshez szükséges kivonat.

## Hatókör

- Hajháló / sapka és védőcipő felismerése csarnok jellegű kameraképen, személyenként.
- Két YOLOX-s modell (fej, láb), ONNX Runtime inferencia, egy PySide6 asztali app.
- Demó az október végi EHS auditra; proof of conceptként mutatjuk be.

## Ütemezés

| Időszak | Fázis | Kimenet | Kész, ha |
| --- | --- | --- | --- |
| okt. 12. | 0. Repo-váz | `pyproject.toml`, könyvtárszerkezet, konfig-betöltés pydantic-kal, CI nélkül | `pytest` zöld, a három YAML validál |
| okt. 12–14. | 1–2. Adat | `notebooks/01_data_prep.ipynb` + `src/ppe/data/` | két COCO adathalmaz a Drive-on (fej, láb), license log, stats |
| okt. 15–18. | 3. Tanítás | `exps/*.py`, `02_train_head`, `03_train_feet` | mAP@50 ≥ 0,8 a teszthalmazon mindkét modellen (célérték) |
| okt. 19–22. | 4. Inferencia-mag | `04_export_onnx`, `src/ppe/inference`, `pipeline`, `rules`, `scripts/demo_cli.py` | CLI demó élő webkamerán, ≥ 10 FPS a Macen |
| okt. 23–25. | 5. PySide app | `app/` | a demóforgatókönyv végigvihető az appból |
| okt. 26–29. | 6. Próba | küszöbhangolás, demóvideó | 50 próbajelenet: téves riasztás < 5%, kihagyás < 10% |

## Tesztfotók

50–100 saját fotó a próbahelyiségben, önkéntesekről, írásos hozzájárulással. Csak ellenőrzésre,
nem tanításra. Ha a modell ezeken gyenge: előcímkézés a modellel, kézi javítás, rövid finomhangolás.

## Kockázatok röviden

- Domain-eltérés (más kamera, fény, fejfedő típus) → tesztfotók korán.
- Colab-session megszakad → checkpoint minden epoch után, folytatható tanítás.
- Windows laptop lassú → `feet_every_n_frames: 2`, kisebb bemeneti méret.
- Lábtakarás → szürke állapot, nem piros.
