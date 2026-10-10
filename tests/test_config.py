"""Validation tests for the three YAML configs and their cross-checks."""

from __future__ import annotations

import shutil
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
import yaml

from ppe.config import (
    CONFIG_DIR,
    AppConfig,
    ConfigError,
    DatasetsConfig,
    RulesConfig,
    load_all,
    load_app,
    load_datasets,
    load_rules,
)

# --- the real configs --------------------------------------------------------


def test_datasets_yaml_is_valid() -> None:
    cfg = load_datasets()
    assert isinstance(cfg, DatasetsConfig)
    assert cfg.models.head.classes == ["person", "head_hairnet", "head_cap", "head_bare"]
    assert cfg.models.feet.classes == ["person", "shoe_safety", "shoe_other"]


def test_rules_yaml_is_valid() -> None:
    cfg = load_rules()
    assert isinstance(cfg, RulesConfig)
    assert cfg.zone.head.required
    assert cfg.smoothing.min_agree <= cfg.smoothing.window


def test_app_yaml_is_valid() -> None:
    cfg = load_app()
    assert isinstance(cfg, AppConfig)
    assert cfg.camera.source == 0
    assert cfg.models.input_size == (640, 640)


def test_load_all_runs_cross_validation() -> None:
    configs = load_all()
    assert configs.rules.active_zone in configs.rules.zones


# --- negative cases on a temporary copy --------------------------------------

Mutator = Callable[[dict[str, Any]], None]


@pytest.fixture()
def config_dir(tmp_path: Path) -> Path:
    target = tmp_path / "configs"
    shutil.copytree(CONFIG_DIR, target)
    return target


def mutate(config_dir: Path, filename: str, fn: Mutator) -> None:
    path = config_dir / filename
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    fn(data)
    path.write_text(yaml.safe_dump(data, allow_unicode=True), encoding="utf-8")


def test_copied_configs_are_valid(config_dir: Path) -> None:
    load_all(config_dir)


@pytest.mark.parametrize(
    ("filename", "fn", "message"),
    [
        pytest.param(
            "datasets.yaml",
            lambda d: d["split"].update(train=0.8),
            "sum to 1.0",
            id="split-sum",
        ),
        pytest.param(
            "datasets.yaml",
            lambda d: d["models"]["head"]["sources"][0]["class_map"].update(hairnet="hat"),
            "unknown classes",
            id="class-map-unknown-target",
        ),
        pytest.param(
            "datasets.yaml",
            lambda d: d["models"]["feet"]["classes"].remove("person"),
            "'person' must be one of the classes",
            id="missing-person",
        ),
        pytest.param(
            "datasets.yaml",
            lambda d: d.update(sead=1),
            "Extra inputs are not permitted",
            id="typo-key",
        ),
        pytest.param(
            "rules.yaml",
            lambda d: d.update(active_zone="nope"),
            "active_zone 'nope'",
            id="active-zone-missing",
        ),
        pytest.param(
            "rules.yaml",
            lambda d: d["smoothing"].update(min_agree=20),
            "min_agree",
            id="min-agree-gt-window",
        ),
        pytest.param(
            "rules.yaml",
            lambda d: d["colors_bgr"].update(green=[0, 300, 0]),
            "less than or equal to 255",
            id="color-out-of-range",
        ),
        pytest.param(
            "rules.yaml",
            lambda d: d["zones"]["hairnet_area"]["head"].update(allowed=[]),
            "at least one allowed class",
            id="required-without-allowed",
        ),
        pytest.param(
            "app.yaml",
            lambda d: d["camera"].update(backend="v4l2"),
            "backend",
            id="bad-camera-backend",
        ),
        pytest.param(
            "app.yaml",
            lambda d: d["models"].update(feet_every_n_frames=0),
            "feet_every_n_frames",
            id="feet-every-n-zero",
        ),
    ],
)
def test_invalid_config_is_rejected(
    config_dir: Path, filename: str, fn: Mutator, message: str
) -> None:
    mutate(config_dir, filename, fn)
    with pytest.raises(ConfigError, match=message):
        load_all(config_dir)


def test_rules_with_unknown_class_fails_cross_check(config_dir: Path) -> None:
    mutate(
        config_dir,
        "rules.yaml",
        lambda d: d["zones"]["hairnet_area"]["head"]["allowed"].append("head_helmet"),
    )
    load_rules(config_dir / "rules.yaml")  # valid on its own
    with pytest.raises(ConfigError, match="unknown classes"):
        load_all(config_dir)


def test_feet_class_in_head_rule_fails_cross_check(config_dir: Path) -> None:
    mutate(
        config_dir,
        "rules.yaml",
        lambda d: d["zones"]["hairnet_area"]["head"]["allowed"].append("shoe_safety"),
    )
    with pytest.raises(ConfigError, match="head uses unknown classes"):
        load_all(config_dir)


def test_missing_threshold_fails_cross_check(config_dir: Path) -> None:
    mutate(config_dir, "rules.yaml", lambda d: d["thresholds"].pop("head_cap"))
    with pytest.raises(ConfigError, match="missing thresholds"):
        load_all(config_dir)


def test_camera_source_accepts_path_or_url(config_dir: Path) -> None:
    mutate(config_dir, "app.yaml", lambda d: d["camera"].update(source="rtsp://cam/stream"))
    assert load_all(config_dir).app.camera.source == "rtsp://cam/stream"


def test_missing_file_raises_config_error(tmp_path: Path) -> None:
    with pytest.raises(ConfigError, match="not found"):
        load_datasets(tmp_path / "nope.yaml")
