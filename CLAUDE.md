# PPE demó – hajháló/sapka és védőcipő felismerés

Ez a fájl a projekt állandó kontextusa Claude Code számára. Minden munkamenet elején olvasd el,
és tartsd be. A részletes terv: `docs/PLAN.md`, a döntések: `docs/DECISIONS.md`.

## Cél és keret

- **Mit építünk:** egy demó rendszert, ami kameraképen személyenként eldönti, hogy visel-e
  hajhálót vagy sapkát és védőcipőt, és zöld / piros / szürke kerettel jelöli.
- **Miért:** bemutató egy EHS auditra, **október végén**. Ez proof of concept, nem éles rendszer.
- **Célterület:** egy nem HACCP terület, ahol hajháló kötelező, a védőcipő bakancs jellegű.
- **Hatókörön kívül:** füldugó, óra, nyaklánc, fehér köpeny, fehér HACCP-cipő, webes felület,
  REST API, felhő-telepítés. Ne javasolj ilyeneket, hacsak nem kérem.
- **Időkeret:** okt. 12–29. Ha egy megoldás jelentősen több munka, mint egy egyszerűbb,
  ami a demóhoz elég, válaszd az egyszerűbbet, és mondd meg, mit hagytunk ki.

## Futtatási környezetek (fontos)

| Hol | Mit futtat | Megjegyzés |
| --- | --- | --- |
| Google Colab (GPU) | adat-előkészítés, tanítás, ONNX export | Claude Code ezt **nem tudja futtatni**; notebookokat írsz, én futtatom |
| MacBook Air M4 (fejlesztés) | inferencia, PySide app, tesztek | Itt futtathatsz parancsokat |
| Windows laptop + USB webkamera | otthoni teszt, esetleg a demó gépe | A kódnak mindkét OS-en futnia kell |

Munkafolyamat Colabbal:
1. Te megírod/módosítod a notebookot és a `src/` kódot, commitolok és pusholok GitHubra.
2. Colabban a notebook klónozza a repót, `pip install -e .`, felcsatolja a Drive-ot.
3. A nagy fájlok (adat, checkpoint, ONNX) a Drive-on maradnak: `/content/drive/MyDrive/ppe-demo/`.
4. A notebook a végén egy kis `metrics.json`-t ír; ezt bemásolom a repo `reports/` mappájába,
   hogy lásd az eredményt. Ha egy Colab-futás hibára fut, a hibaüzenetet bemásolom neked.

Ezért minden notebook legyen **újrafuttatható elejétől végéig**, minden epoch után mentsen
checkpointot a Drive-ra, és szakadás után tudjon folytatni.

## Architektúra

Két külön detektor, egy közös inferencia-mag, egy PySide kliens.

```
kamera → [fejmodell] + [lábmodell] → hozzárendelés személyhez → követés + időbeli simítás
       → szabálymotor (zöld / piros / szürke) → PySide app
```

- **Fejmodell** (YOLOX-s): `person`, `head_hairnet`, `head_cap`, `head_bare`
- **Lábmodell** (YOLOX-s): `person`, `shoe_safety`, `shoe_other`
- Azért két modell, mert a hajhálós adathalmazokban a cipők nincsenek címkézve, a cipős
  adathalmazban a fejfedők nincsenek. Egy közös modell a ki nem címkézett tárgyakat
  háttérnek tanulná. **Ne vond össze a két modellt.**
- A `person` címkéket az adathalmazokban **nem használjuk**, mert nem következetesek.
  Helyettük egy COCO-n előtanított YOLOX-s-sel automatikusan felcímkézzük a személyeket
  minden képen (pszeudo-címke), így mindkét modell `person` osztálya egységes.
- **Hozzárendelés:** a személykereteket a fejmodelltől vesszük. Fej → az a személy, akinek a
  keretének felső harmadába esik a fej középpontja; cipő → akinek az alsó negyedébe.
- **Követés:** ByteTrack. **Simítás:** személyenként az utolsó N képkockából legalább M egyezzen
  (alapból 15/10, a `configs/rules.yaml`-ből).
- **Állapotok:** zöld = minden kötelező elem megvan; piros = valami hiányzik; szürke = a fej
  vagy a láb nem látszik, ezért nem ellenőrizhető. A szürke soha nem lehet piros.

## Adatforrások

Három publikus Roboflow-adathalmaz, mind CC BY 4.0. A részletek, verziók és osztálytérkép:
`configs/datasets.yaml`. Ez az egyetlen igazságforrás az osztálynevekre, ne égesd be őket a kódba.

Kötelező adat-előkészítési lépések:
1. Letöltés COCO formátumban a `roboflow` csomaggal. Az API-kulcs Colab Secrets-ben van
   (`ROBOFLOW_API_KEY`), **soha ne kerüljön a repóba vagy notebook-kimenetbe**.
2. Osztálytérkép alkalmazása, a nem használt osztályok eldobása.
3. Kérdéses forrású képek kiszűrése fájlnév alapján (`configs/datasets.yaml` → `filename_blocklist`).
4. Duplikátumszűrés perceptuális hash-sel (`imagehash`), adathalmazokon át is.
5. Személyek pszeudo-címkézése COCO YOLOX-s-sel.
6. **Csoportos felbontás:** a Roboflow eredeti train/valid/test bontását eldobjuk. A képeket
   forrásvideó / forrásfájl szerint csoportosítjuk (a fájlnévből a képkockaszám és a Roboflow
   `.rf.<hash>` utótag levágásával), és csoportonként bontunk 70/15/15 arányban, fix seeddel.
   Így ugyanazon videó kockái nem kerülnek több halmazba.
7. Licencnapló: `reports/license_log.csv` (adathalmaz, verzió, letöltés dátuma, licenc, URL,
   képszám szűrés előtt és után).
8. Statisztika osztályonként és halmazonként: `reports/dataset_stats_<modell>.json`.

## Technológiai döntések

- Python 3.11, PyTorch, YOLOX-s fine-tuning COCO-súlyokból. A YOLOX telepítési módját
  (eredeti Megvii repo vagy a `pixeltable-yolox` fork) **ellenőrizd a telepítés előtt**, ne
  emlékezetből dolgozz; válaszd azt, ami a Colab aktuális PyTorch-verziójával gond nélkül megy.
- RF-DETR csak tartalék, ha a YOLOX gyenge. Magadtól ne kezdd el.
- Ultralytics YOLO-t **ne használj** (AGPL-3.0 licenc).
- Inferencia: ONNX Runtime. Macen CoreML execution provider, ha elérhető, különben CPU;
  Windowson CPU (később esetleg DirectML). PyTorch ne legyen futásidejű függőség.
- Kamera: OpenCV. Windowson `cv2.CAP_DSHOW`. A kamera indexe és a forrás (index, fájl, RTSP URL)
  a beállításokból jön, ne legyen beégetve.
- Felület: PySide6. A kameraolvasás és az inferencia `QThread`-ben fut, a GUI szál csak rajzol.
- Kísérletkövetés: TensorBoard (Colabon).
- Konfiguráció: YAML (`configs/`), betöltve pydantic modellekbe, validálva.

## Repo-szerkezet (cél)

```
ppe-demo/
├── CLAUDE.md
├── pyproject.toml
├── configs/          # datasets.yaml, rules.yaml, app.yaml
├── docs/             # PLAN.md, DECISIONS.md
├── notebooks/        # 01_data_prep, 02_train_head, 03_train_feet, 04_export_onnx
├── exps/             # YOLOX experiment fájlok (head_yolox_s.py, feet_yolox_s.py)
├── src/ppe/
│   ├── data/         # letöltés, osztálytérkép, szűrés, dedup, split, pszeudo-címke
│   ├── inference/    # ONNX modellek betöltése, elő- és utófeldolgozás, NMS
│   ├── pipeline/     # hozzárendelés, követés, simítás
│   ├── rules/        # szabálymotor
│   └── camera.py
├── app/              # PySide6 alkalmazás
├── scripts/          # CLI: demo_cli.py, benchmark_fps.py
├── tests/
├── reports/          # kis, commitolt eredményfájlok (metrics, stats, license log)
└── models/           # helyi ONNX fájlok – gitignored
```

## Konvenciók

- Azonosítók, kód és kommentek angolul; a felhasználói felület szövegei magyarul.
- Típusannotációk, `ruff` formázás és lint. Kis, tesztelhető függvények.
- Tesztek `pytest`-tel a `src/ppe/` logikára (osztálytérkép, split, hozzárendelés, simítás,
  szabálymotor). A modellt igénylő tesztek egy kis mintaképpel vagy mockkal fussanak, GPU nélkül.
- Egy feladat = egy commit, beszédes üzenettel. Fázisonként külön branch (`phase-1-data`, …).
- Nagy fájl (kép, checkpoint, ONNX, zip) soha ne kerüljön gitbe.

## Hogyan dolgozz velem

- Magyarul kommunikálj velem. Kezdő-haladó Python-tudásom van (Flask, Django, PySide),
  a CV és a YOLOX új nekem: amikor nem nyilvánvaló döntést hozol, egy-két mondatban mondd el, miért.
- Mielőtt egy fázisba belekezdesz, írj rövid tervet (érintett fájlok, lépések), és várd meg
  a jóváhagyásom.
- Ha valami Colabon fut, mondd meg pontosan, melyik notebookot futtassam, és mit másoljak vissza.
- Ha egy döntés a tervtől eltér, írd be a `docs/DECISIONS.md`-be.
- Ha bizonytalan vagy egy külső könyvtár aktuális API-jában, nézd meg a dokumentációt, ne találgass.

## Aktuális állapot

- [ ] 0. fázis – repo-váz, `pyproject.toml`, konfigurációk validálása
- [ ] 1–2. fázis – adat-előkészítő notebook (okt. 12–14.)
- [ ] 3. fázis – fej- és lábmodell tanítása Colabon (okt. 15–18.)
- [ ] 4. fázis – ONNX export és inferencia-mag (okt. 19–22.)
- [ ] 5. fázis – PySide app (okt. 23–25.)
- [ ] 6. fázis – próbák, küszöbhangolás, demóvideó (okt. 26–29.)

Frissítsd ezt a listát, amikor egy fázis elkészül.
