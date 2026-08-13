"""Feature-based calibrated price model.

Production inference deliberately ignores drawing numbers and part numbers.  The
model uses only drawing-derived material, dimensions and surface-treatment class.
"""

from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from quotation.infrastructure.parser.dimension_parser import parse_dimension
from quotation.infrastructure.parser.material_normalizer import normalize_material
from quotation.infrastructure.smb.client import cached_public_path

DEFAULT_CALIBRATION_MODEL = Path("data/feature-price-calibration-gcs-v1.0.json")
DIMENSION_PATTERN = re.compile(
    r"(?:[φΦØ]\s*)?\d+(?:\.\d+)?\s*[*×xX]\s*\d+(?:\.\d+)?"
    r"(?:\s*[*×xX]\s*\d+(?:\.\d+)?)?"
)


def normalize_surface_family(value: str | None) -> str:
    text = (value or "").casefold()
    groups = (
        ("anodize", ("陽極", "阳极", "anodize")),
        ("chrome", ("鍍鉻", "镀铬", "chrome")),
        ("paint", ("ral9003", "烤漆", "噴塗", "喷涂", "paint")),
        ("heat", ("熱處理", "热处理", "heat")),
        ("black", ("發黑", "发黑", "black")),
    )
    for family, keywords in groups:
        if any(keyword in text for keyword in keywords):
            return family
    return "none"


def canonical_dimensions(raw: str | None) -> tuple[float, float, float] | None:
    parsed = parse_dimension(raw or "")
    values = [
        float(value)
        for value in (parsed.length, parsed.width, parsed.height)
        if value is not None and value > 0
    ]
    if len(values) < 2:
        return None
    values.sort(reverse=True)
    while len(values) < 3:
        values.append(1.0)
    return tuple(values[:3])


def extract_dimensions(texts: Iterable[str]) -> tuple[str, tuple[float, float, float]] | None:
    candidates: list[tuple[int, float, str, tuple[float, float, float]]] = []
    for text in texts:
        for match in DIMENSION_PATTERN.finditer(str(text)):
            raw = match.group(0)
            dimensions = canonical_dimensions(raw)
            if dimensions is None:
                continue
            separator_count = sum(raw.count(separator) for separator in ("*", "×", "x", "X"))
            volume = dimensions[0] * dimensions[1] * dimensions[2]
            candidates.append((separator_count, volume, raw, dimensions))
    if not candidates:
        return None
    _, _, raw, dimensions = max(candidates, key=lambda candidate: (candidate[0], candidate[1]))
    return raw, dimensions


def extract_material(texts: Iterable[str]) -> str | None:
    for text in texts:
        result = normalize_material(str(text))
        if result.normalized and result.confidence >= 0.7:
            return result.normalized
    return None


@dataclass(frozen=True)
class FeaturePricePrediction:
    amount: float
    material: str
    dimensions_raw: str
    dimensions: tuple[float, float, float]
    surface_family: str
    model_version: str
    training_count: int
    validation_wape_pct: float
    confidence: float
    out_of_domain: bool


class FeaturePriceCalibration:
    """Load and evaluate the published feature-calibration model."""

    def __init__(self, path: str | Path | None = None):
        self.path = (
            Path(path)
            if path
            else cached_public_path(
                "prices/published/feature-price-calibration-gcs-v1.0.json",
                DEFAULT_CALIBRATION_MODEL,
            )
        )
        self.version: str | None = None
        self.status: str | None = None
        self.load_error: str | None = None
        self._payload: dict[str, Any] = {}
        self._load()

    @property
    def is_active(self) -> bool:
        return self.status == "ACTIVE_REVIEW_REQUIRED" and bool(self._payload)

    def predict(
        self,
        texts: Iterable[str],
        material: str | None = None,
        surface_treatment: str | None = None,
    ) -> FeaturePricePrediction | None:
        if not self.is_active:
            return None
        text_list = [str(text) for text in texts]
        normalized_material = (
            normalize_material(material or "").normalized or material or extract_material(text_list)
        )
        dimension_result = extract_dimensions(text_list)
        if not normalized_material or dimension_result is None:
            return None
        dimensions_raw, dimensions = dimension_result
        surface_family = normalize_surface_family(surface_treatment or "\n".join(text_list))
        model = self._payload["model"]
        features = self._feature_vector(normalized_material, dimensions, surface_family, model)
        coefficients = [float(value) for value in model["coefficients"]]
        if len(features) != len(coefficients):
            return None
        log_price = sum(
            value * coefficient
            for value, coefficient in zip(features, coefficients, strict=True)
        )
        amount = round(max(1.0, min(math.exp(log_price), 100000.0)), 2)
        domain = self._payload.get("material_dimension_domains", {}).get(normalized_material)
        out_of_domain = self._is_out_of_domain(dimensions, domain)
        confidence = 0.45 if out_of_domain else 0.65
        validation = self._payload.get("validation", {})
        return FeaturePricePrediction(
            amount=amount,
            material=str(normalized_material),
            dimensions_raw=dimensions_raw,
            dimensions=dimensions,
            surface_family=surface_family,
            model_version=str(self.version),
            training_count=int(self._payload.get("training_count") or 0),
            validation_wape_pct=float(validation.get("leave_one_out_wape_pct") or 0),
            confidence=confidence,
            out_of_domain=out_of_domain,
        )

    @staticmethod
    def _feature_vector(
        material: str,
        dimensions: tuple[float, float, float],
        surface_family: str,
        model: dict[str, Any],
    ) -> list[float]:
        d1, d2, d3 = dimensions
        values = [
            1.0,
            math.log(d1 + 1),
            math.log(d2 + 1),
            math.log(d3 + 1),
            math.log(d1 * d2 * d3 + 1),
            math.log(d1 * d2 + 1),
        ]
        values.extend(
            1.0 if material == category else 0.0
            for category in model.get("material_categories", [])[1:]
        )
        values.extend(
            1.0 if surface_family == category else 0.0
            for category in model.get("surface_categories", [])[1:]
        )
        return values

    @staticmethod
    def _is_out_of_domain(
        dimensions: tuple[float, float, float], domain: dict[str, Any] | None
    ) -> bool:
        if not domain:
            return True
        minimum = domain.get("minimum", [])
        maximum = domain.get("maximum", [])
        if len(minimum) != 3 or len(maximum) != 3:
            return True
        return any(
            value < max(float(low) / 2, 0.1) or value > float(high) * 2
            for value, low, high in zip(dimensions, minimum, maximum, strict=True)
        )

    def _load(self) -> None:
        if not self.path.exists():
            self.load_error = f"图纸特征校准模型不存在：{self.path}"
            return
        try:
            self._payload = json.loads(self.path.read_text(encoding="utf-8"))
            self.version = str(self._payload.get("price_version_id") or "") or None
            self.status = str(self._payload.get("status") or "") or None
        except (OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
            self.load_error = f"图纸特征校准模型读取失败：{exc}"
            self._payload = {}
