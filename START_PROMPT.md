# Első üzenet Claude Code-nak

Másold be ezt az első munkamenet elején (a repo gyökerében megnyitva):

---

Szia! Olvasd el a `CLAUDE.md`-t, a `docs/PLAN.md`-t, a `docs/DECISIONS.md`-t és a `configs/` mappa
három YAML fájlját. Ezek a projekt szabályai és döntései.

Ezután a 0. fázissal kezdünk:
1. Hozd létre a repo-vázat a `CLAUDE.md` szerinti szerkezettel (üres modulokkal, `__init__.py`-kkal).
2. Írd meg a `pyproject.toml`-t: futásidejű függőségek (onnxruntime, opencv-python, PySide6,
   numpy, pyyaml, pydantic) és opcionális `train` / `dev` csoportok. A PyTorch és a YOLOX
   csak a `train` csoportba kerüljön.
3. Írd meg a konfigurációk pydantic modelljeit és betöltőjét (`src/ppe/config.py`), tesztekkel,
   amik mindhárom YAML-t validálják.
4. Ellenőrizd (dokumentáció alapján, ne emlékezetből), hogy a YOLOX melyik telepítési módja
   működik a Colab jelenlegi PyTorch-verziójával, és írd be a döntést a `docs/DECISIONS.md`-be.

Mielőtt bármit írsz, mutasd meg a tervedet röviden, és várd meg a jóváhagyásom.
A végén mondd meg, milyen parancsokkal futtassam a teszteket a Macen.
