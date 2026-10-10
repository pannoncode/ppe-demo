# Döntésnapló

Új döntésnél új sor kerül a táblázat tetejére (legújabb elöl).

| Dátum | Döntés | Indoklás |
| --- | --- | --- |
| 2026-10-10 | YOLOX telepítése: `pixeltable-yolox==0.4.2` (PyPI, Apache-2.0), nem az eredeti Megvii repo | Colab most: Python 3.13, torch 2.11 (googlecolab/backend-info, 2026-10-03). A Megvii repo 2023 óta nem frissül; `pip install -e .` build isolation mellett elhasal (#1814), az `onnx-simplifier==0.4.10` pin Python ≥ 3.12-n nem buildel (#1781), torch ≥ 2.6-on a checkpoint-betöltés (#1906) és az ONNX-export (`torch.onnx._export`, #1907) törik. A fork tiszta Python wheel, `torch>=2.2.2`, Python 3.9–3.13. Ismert hibái és megkerülésük: `pycocotools>=2.0.11` kell (különben `KeyError: 'info'` az első kiértékelésnél, #14); torch ≥ 2.6-on az AP-t tartalmazó checkpointok (`best_ckpt`, `last_epoch_ckpt`) csak `weights_only=False`-szal tölthetők be (#11), folytatáshoz a `latest_ckpt.pth` jó; a csomagolt `export_onnx.py` 0.4.2-ben hibás, ezért közvetlenül `torch.onnx.export`-ot hívunk. Megerősítés: `notebooks/00_yolox_smoke_test.ipynb` → `reports/smoke_result.json` |
| 2026-10-10 | Az `exps/` fájlok `YoloxConfig`-alosztályok, nem Megvii-féle Exp-fájlok; adatszerkezet `annotations/instances_{train,val}2017.json` + `train2017/` + `val2017/` | A pixeltable-yolox `-c modul:Osztály` formában kéri a konfigot (nincs `-f exp.py`), a képmappák neve 0.4.2-ben kötött. Az 1. fázis kimenete ehhez igazodik; a kategóriák a `datasets.yaml` sorrendjében, 1..N azonosítóval |
| 2026-10-10 | `requires-python >=3.11` (nem pontosan 3.11) | A Colab már 3.13-at futtat, a fejlesztő Mac 3.12-t; mindhárom támogatott |
| 2026-10-10 | `pyproject` extrák: alap = numpy/pyyaml/pydantic; `[app]` = onnxruntime, opencv-python, PySide6; `[train]` = torch, pixeltable-yolox stb.; `[dev]` = pytest, ruff | Colabon a `.[train]` ne húzza be a GUI-t és ne ütközzön a Colab OpenCV-jével; Macen `.[app,dev]` |
| 2026-10-10 | Csak YOLOX-s, RF-DETR csak tartalék | Az október végi audit miatt nincs idő összehasonlításra |
| 2026-10-10 | A forrás `person` címkéket eldobjuk, COCO YOLOX-s pszeudo-címkézés | A három adathalmaz `person` címkézése nem következetes |
| 2026-10-10 | Csoportos (forrásfájl szerinti) train/val/test bontás | Sok kép videókocka; véletlen bontás adatszivárgást okozna |
| 2026-10-10 | Két külön modell: fej és láb | A hajhálós adatban a cipő, a cipős adatban a fejfedő nincs címkézve |
| 2026-10-10 | Adat: Safety Food, AIProject, PPE-DET (Roboflow, CC BY 4.0); saját adat csak tesztre | Demó jellegű projekt; saját adathalmaz csak pilot esetén |
| 2026-10-10 | Célterület: nem HACCP terület, hajháló kötelező, bakancs jellegű védőcipő | A fehér HACCP-cipő nincs hatókörben, a PPE-DET bakancsai illenek |
| 2026-10-10 | Egyetlen PySide6 felület, nincs web / API | Időkeret, meglévő tudás |
| 2026-10-10 | Folyamatos csarnokfigyelés; füldugó, ékszer, köpeny kihagyva | Kis tárgyak csarnokkamerán megbízhatatlanok |
| 2026-10-10 | Tanítás Google Colabon, inferencia Macen / Windows laptopon | Nincs helyi GPU |
| 2026-10-10 | Ultralytics kizárva | AGPL-3.0 licenc |
