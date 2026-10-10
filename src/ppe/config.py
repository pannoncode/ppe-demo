"""Pydantic models and loaders for the YAML configs in `configs/`.

`datasets.yaml` is the single source of truth for class names; `validate_cross`
checks that `rules.yaml` only refers to classes defined there.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Literal, TypeVar

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = REPO_ROOT / "configs"

PERSON_CLASS = "person"

Fraction = Annotated[float, Field(gt=0.0, le=1.0)]
Probability = Annotated[float, Field(ge=0.0, le=1.0)]
PositiveInt = Annotated[int, Field(gt=0)]
ColorChannel = Annotated[int, Field(ge=0, le=255)]
BGRColor = tuple[ColorChannel, ColorChannel, ColorChannel]


class ConfigError(ValueError):
    """Raised when a config file is missing, malformed or inconsistent."""


class StrictModel(BaseModel):
    """Base model that rejects unknown keys, so typos in YAML fail loudly."""

    model_config = ConfigDict(extra="forbid")


# --- datasets.yaml -----------------------------------------------------------


class SplitConfig(StrictModel):
    train: Fraction
    val: Fraction
    test: Fraction
    group_by: Literal["source_file"]

    @model_validator(mode="after")
    def _sums_to_one(self) -> SplitConfig:
        total = self.train + self.val + self.test
        if not math.isclose(total, 1.0, abs_tol=1e-6):
            raise ValueError(f"split fractions must sum to 1.0, got {total:.4f}")
        return self


class DedupConfig(StrictModel):
    method: Literal["phash"]
    max_hamming_distance: Annotated[int, Field(ge=0)]
    across_datasets: bool


class PseudoLabelConfig(StrictModel):
    model: str
    min_confidence: Probability
    min_box_height_px: PositiveInt


class SourceDataset(StrictModel):
    name: str
    url: str
    workspace: str
    project: str
    version: PositiveInt
    class_map: dict[str, str] = Field(min_length=1)
    notes: str | None = None


class ModelData(StrictModel):
    classes: list[str] = Field(min_length=1)
    sources: list[SourceDataset] = Field(min_length=1)

    @model_validator(mode="after")
    def _check_classes(self) -> ModelData:
        if len(set(self.classes)) != len(self.classes):
            raise ValueError(f"duplicate class names in {self.classes}")
        if PERSON_CLASS not in self.classes:
            raise ValueError(f"'{PERSON_CLASS}' must be one of the classes")
        for source in self.sources:
            unknown = set(source.class_map.values()) - set(self.classes)
            if unknown:
                raise ValueError(
                    f"source '{source.name}' maps to unknown classes {sorted(unknown)}; "
                    f"allowed: {self.classes}"
                )
        return self


class ModelsData(StrictModel):
    head: ModelData
    feet: ModelData


class ExcludedDataset(StrictModel):
    name: str
    url: str
    reason: str


class DatasetsConfig(StrictModel):
    drive_root: str
    download_format: Literal["coco"]
    seed: int
    split: SplitConfig
    filename_blocklist: list[str] = Field(default_factory=list)
    dedup: DedupConfig
    person_pseudo_label: PseudoLabelConfig
    models: ModelsData
    excluded: list[ExcludedDataset] = Field(default_factory=list)

    @model_validator(mode="after")
    def _unique_source_names(self) -> DatasetsConfig:
        names = [s.name for m in (self.models.head, self.models.feet) for s in m.sources]
        if len(set(names)) != len(names):
            raise ValueError(f"duplicate source dataset names: {names}")
        return self


# --- rules.yaml --------------------------------------------------------------


class PartRule(StrictModel):
    """What is required for one body part (head or feet) in a zone."""

    required: bool
    allowed: list[str] = Field(default_factory=list)
    violation: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _check_lists(self) -> PartRule:
        if self.required and not self.allowed:
            raise ValueError("a required part needs at least one allowed class")
        overlap = set(self.allowed) & set(self.violation)
        if overlap:
            raise ValueError(f"classes both allowed and violation: {sorted(overlap)}")
        return self


class Zone(StrictModel):
    label: str
    head: PartRule
    feet: PartRule


class AssignmentConfig(StrictModel):
    head_region_top_fraction: Fraction
    feet_region_bottom_fraction: Fraction


class SmoothingConfig(StrictModel):
    window: PositiveInt
    min_agree: PositiveInt

    @model_validator(mode="after")
    def _agree_within_window(self) -> SmoothingConfig:
        if self.min_agree > self.window:
            raise ValueError(f"min_agree ({self.min_agree}) > window ({self.window})")
        return self


class TrackingConfig(StrictModel):
    method: Literal["bytetrack"]
    max_lost_frames: Annotated[int, Field(ge=0)]


class ColorsBGR(StrictModel):
    green: BGRColor
    red: BGRColor
    grey: BGRColor


class RulesConfig(StrictModel):
    active_zone: str
    zones: dict[str, Zone] = Field(min_length=1)
    thresholds: dict[str, Probability]
    assignment: AssignmentConfig
    smoothing: SmoothingConfig
    tracking: TrackingConfig
    colors_bgr: ColorsBGR

    @model_validator(mode="after")
    def _active_zone_exists(self) -> RulesConfig:
        if self.active_zone not in self.zones:
            raise ValueError(f"active_zone '{self.active_zone}' not in zones {sorted(self.zones)}")
        return self

    @property
    def zone(self) -> Zone:
        """The currently active zone."""
        return self.zones[self.active_zone]


# --- app.yaml ----------------------------------------------------------------


class CameraConfig(StrictModel):
    source: int | str  # webcam index, video file path or rtsp:// URL
    backend: Literal["auto", "dshow", "avfoundation", "any"]
    width: PositiveInt
    height: PositiveInt
    fps: PositiveInt


class ModelsConfig(StrictModel):
    head_onnx: Path
    feet_onnx: Path
    input_size: tuple[PositiveInt, PositiveInt]
    providers: Literal["auto"] | Annotated[list[str], Field(min_length=1)]
    feet_every_n_frames: PositiveInt


class UIConfig(StrictModel):
    language: str
    show_fps: bool
    show_person_ids: bool
    event_log: bool
    save_frames: bool


class AboutConfig(StrictModel):
    datasets_attribution: list[str] = Field(default_factory=list)


class AppConfig(StrictModel):
    camera: CameraConfig
    models: ModelsConfig
    rules_config: Path
    ui: UIConfig
    about: AboutConfig


# --- loading -----------------------------------------------------------------

T = TypeVar("T", bound=BaseModel)


def load_yaml(path: Path, model: type[T]) -> T:
    """Load a YAML file and validate it into `model`."""
    path = Path(path)
    if not path.is_file():
        raise ConfigError(f"config file not found: {path}")
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ConfigError(f"invalid YAML in {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ConfigError(f"{path}: top level must be a mapping")
    try:
        return model.model_validate(data)
    except ValidationError as exc:
        raise ConfigError(f"{path}: {exc}") from exc


def load_datasets(path: Path = CONFIG_DIR / "datasets.yaml") -> DatasetsConfig:
    return load_yaml(path, DatasetsConfig)


def load_rules(path: Path = CONFIG_DIR / "rules.yaml") -> RulesConfig:
    return load_yaml(path, RulesConfig)


def load_app(path: Path = CONFIG_DIR / "app.yaml") -> AppConfig:
    return load_yaml(path, AppConfig)


def validate_cross(datasets: DatasetsConfig, rules: RulesConfig) -> None:
    """Check that `rules` only uses class names defined in `datasets`.

    Every detector class (both models) must also have a threshold.
    """
    head_classes = set(datasets.models.head.classes)
    feet_classes = set(datasets.models.feet.classes)
    errors: list[str] = []

    for zone_name, zone in rules.zones.items():
        for part, known in (("head", head_classes), ("feet", feet_classes)):
            rule: PartRule = getattr(zone, part)
            unknown = set(rule.allowed + rule.violation) - known
            if unknown:
                errors.append(f"zone '{zone_name}'.{part} uses unknown classes {sorted(unknown)}")

    all_classes = head_classes | feet_classes
    unknown_thresholds = set(rules.thresholds) - all_classes
    if unknown_thresholds:
        errors.append(f"thresholds for unknown classes {sorted(unknown_thresholds)}")
    missing_thresholds = all_classes - set(rules.thresholds)
    if missing_thresholds:
        errors.append(f"missing thresholds for classes {sorted(missing_thresholds)}")

    if errors:
        raise ConfigError("rules.yaml vs datasets.yaml: " + "; ".join(errors))


@dataclass(frozen=True)
class Configs:
    datasets: DatasetsConfig
    rules: RulesConfig
    app: AppConfig


def load_all(config_dir: Path = CONFIG_DIR) -> Configs:
    """Load all three configs and run the cross-checks.

    `app.rules_config` is resolved relative to the repo root (the parent of
    `config_dir`) unless it is absolute.
    """
    config_dir = Path(config_dir)
    app = load_app(config_dir / "app.yaml")
    rules_path = app.rules_config
    if not rules_path.is_absolute():
        rules_path = config_dir.parent / rules_path
    datasets = load_datasets(config_dir / "datasets.yaml")
    rules = load_rules(rules_path)
    validate_cross(datasets, rules)
    return Configs(datasets=datasets, rules=rules, app=app)
