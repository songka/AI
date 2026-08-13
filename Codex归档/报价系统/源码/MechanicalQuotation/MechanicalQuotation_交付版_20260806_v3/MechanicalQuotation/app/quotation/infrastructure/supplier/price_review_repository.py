"""Append-only review decisions stored in the SMB public slot."""

from __future__ import annotations

import json
from pathlib import Path

from quotation.domain.price_review import PriceReviewRecord


class PriceReviewRepository:
    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)

    def get(self, price_record_id: str) -> PriceReviewRecord | None:
        path = self._path(price_record_id)
        if not path.is_file():
            return None
        return self._load(path)

    def list(self) -> list[PriceReviewRecord]:
        if not self.root.is_dir():
            return []
        records = [self._load(path) for path in self.root.glob("RV-PR-*.json")]
        return sorted(records, key=lambda item: item.reviewed_at, reverse=True)

    def append(self, review: PriceReviewRecord) -> PriceReviewRecord:
        target = self._path(review.price_record_id)
        target.parent.mkdir(parents=True, exist_ok=True)
        try:
            with target.open("x", encoding="utf-8") as stream:
                json.dump(review.model_dump(mode="json"), stream, ensure_ascii=False, indent=2)
                stream.write("\n")
        except FileExistsError as exc:
            raise ValueError("该供应商报价已经完成审核，不能重复处理") from exc
        return review

    def _path(self, price_record_id: str) -> Path:
        if not price_record_id.startswith("PR-") or any(
            token in price_record_id for token in ("/", "\\", "..")
        ):
            raise ValueError("供应商报价记录编号不合法")
        return self.root / f"RV-{price_record_id}.json"

    @staticmethod
    def _load(path: Path) -> PriceReviewRecord:
        try:
            return PriceReviewRecord.model_validate_json(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise ValueError(f"价格审核记录格式损坏：{path.name}") from exc

