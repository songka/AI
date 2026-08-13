"""Role-separated AI review orchestration for quotation jobs."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from typing import Any


class MultiAgentReviewOrchestrator:
    """Coordinate independent note, process, price and supervisor agents."""

    def __init__(self, client: Any) -> None:
        self._client = client

    def analyze_before_pricing(
        self, drawing_number: str, texts: list[str], geometry: dict[str, Any]
    ) -> dict[str, Any]:
        with ThreadPoolExecutor(max_workers=2, thread_name_prefix="quotation-ai") as pool:
            note_future = pool.submit(
                self._client.analyze_drawing_notes, drawing_number, texts
            )
            process_future = pool.submit(
                self._client.classify_processes, drawing_number, texts, geometry
            )
        return {
            "备注理解智能体": note_future.result(),
            "工艺规划智能体": process_future.result(),
        }

    def audit_after_pricing(
        self,
        drawing_number: str,
        texts: list[str],
        items: list[dict[str, Any]],
        prior: dict[str, Any],
    ) -> dict[str, Any]:
        reviews = dict(prior)
        reviews["价格审核智能体"] = self._client.audit_itemized_quote(
            drawing_number, texts, items
        )
        price = reviews["价格审核智能体"]
        process_count = len(reviews.get("工艺规划智能体") or [])
        note_risks = len((reviews.get("备注理解智能体") or {}).get("risks", []))
        verdict = str((price or {}).get("verdict", "REVIEW"))
        reviews["风险汇总智能体"] = {
            "verdict": "PASS" if verdict == "PASS" and note_risks == 0 else "REVIEW",
            "summary": (
                f"工艺建议 {process_count} 项，备注风险 {note_risks} 项，"
                f"价格审核结论 {verdict}"
            ),
            "requires_human_review": verdict != "PASS" or note_risks > 0,
        }
        return reviews
