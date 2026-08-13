"""Role-separated AI review orchestration for quotation jobs."""

from __future__ import annotations

import re
from concurrent.futures import ThreadPoolExecutor
from typing import Any


class MultiAgentReviewOrchestrator:
    """Coordinate independent note, process, price and supervisor agents."""

    def __init__(self, client: Any) -> None:
        self._client = client

    def analyze_before_pricing(
        self, drawing_number: str, texts: list[str], geometry: dict[str, Any]
    ) -> dict[str, Any]:
        with ThreadPoolExecutor(max_workers=3, thread_name_prefix="quotation-ai") as pool:
            note_future = pool.submit(
                self._client.analyze_drawing_notes, drawing_number, texts
            )
            process_future = pool.submit(
                self._client.classify_processes, drawing_number, texts, geometry
            )
            category_future = pool.submit(
                self._client.classify_part_category, drawing_number, texts, geometry
            )
        reviews = {
            "备注理解智能体": note_future.result(),
            "工艺规划智能体": process_future.result(),
            "零件分类智能体": category_future.result(),
        }
        reviews["零件分类智能体"] = self._reconcile_category(
            reviews["零件分类智能体"],
            reviews["工艺规划智能体"],
            texts,
        )
        return reviews

    @staticmethod
    def _reconcile_category(
        category: dict[str, Any] | None,
        processes: list[dict[str, Any]] | None,
        texts: list[str],
    ) -> dict[str, Any]:
        """Prevent a plate-shaped machined part from becoming sheet metal later."""
        result = dict(category or {})
        category_value = str(result.get("part_category") or "").upper()
        context = "\n".join(str(text) for text in texts)
        explicit_sheet_fabrication = bool(
            re.search(
                r"钣金|鈑金|板金|折弯|折彎|冲压|沖壓|激光切割|雷射切割|"
                r"折边|折邊|展开图|展開圖",
                context,
                re.IGNORECASE,
            )
        )
        machining_codes = {
            str(item.get("code") or "").upper()
            for item in (processes or [])
            if isinstance(item, dict)
        }
        has_machining_route = bool(machining_codes.intersection(
            {
                "MACHINING",
                "MILL",
                "CNC",
                "LATHE",
                "GRIND",
                "EDM",
                "WIRE_CUT",
                "SLOW_WIRE",
            }
        ))
        if not has_machining_route:
            return result
        explicit_weldment = bool(
            re.search(r"焊接|焊縫|焊缝|滿焊|满焊|點焊|点焊|焊後|焊后", context)
        )
        explicit_frame = bool(
            re.search(r"型材|鋁擠型|铝挤型|方管|方通|角鋼|角钢|框架|機架|机架", context)
        )
        reason = None
        if category_value == "SHEET_METAL" and not explicit_sheet_fabrication:
            reason = "没有折弯、冲压、钣金展开等薄板成形证据；板状毛坯不等于钣金件"
        elif category_value == "WELDMENT" and not explicit_weldment:
            reason = "没有焊接或焊缝证据，不能仅凭外形推断为焊接件"
        elif category_value == "FRAME_ASSEMBLY" and not explicit_frame:
            reason = "没有型材、方管、角钢或框架装配证据，不能推断为型材组装件"
        if reason is None:
            return result
        original = dict(result)
        result.update(
            {
                "part_category": "MACHINING",
                "category_name": "加工件",
                "confidence": max(float(result.get("confidence", 0) or 0), 0.9),
                "evidence": list(result.get("evidence") or [])
                + [
                    f"一致性校正：工艺规划为切削加工，{reason}。"
                ],
                "status": "CONSISTENCY_CORRECTED",
                "original_result": original,
            }
        )
        return result

    @staticmethod
    def audit_failed(review: dict[str, Any] | None) -> bool:
        if not isinstance(review, dict):
            return True
        issues = {str(item) for item in review.get("issues", [])}
        return (
            float(review.get("confidence", 0) or 0) <= 0
            and "价格审核未返回有效结果" in issues
        )

    @staticmethod
    def audit_requests_correction(review: dict[str, Any] | None) -> bool:
        return bool(
            isinstance(review, dict)
            and str(review.get("verdict", "")).upper() == "REVIEW"
            and review.get("actions")
            and float(review.get("confidence", 0) or 0) > 0
        )

    def retry_dependencies(
        self,
        drawing_number: str,
        texts: list[str],
        geometry: dict[str, Any],
        requested_actions: list[str] | None = None,
    ) -> dict[str, Any] | None:
        """Retry the prerequisite agents once after a transport/invalid audit failure."""
        reset = getattr(self._client, "begin_controlled_retry", None)
        if callable(reset) and reset() is False:
            return None
        retry_texts = list(texts)
        if requested_actions:
            retry_texts.append(
                "价格审核要求重新核对：" + "；".join(str(item) for item in requested_actions)
            )
        return self.analyze_before_pricing(drawing_number, retry_texts, geometry)

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
