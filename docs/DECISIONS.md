# Döntésnapló

Új döntésnél új sor kerül a táblázat tetejére (legújabb elöl).

| Dátum | Döntés | Indoklás |
| --- | --- | --- |
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
