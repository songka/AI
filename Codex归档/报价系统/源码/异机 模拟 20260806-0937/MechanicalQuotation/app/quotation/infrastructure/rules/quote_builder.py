"""Quote Builder - aggregates QuoteItems, dedups, computes confidence."""

from __future__ import annotations

from datetime import datetime, timezone

from quotation.domain.quote import PriceSource, Quote, QuoteConfidence, QuoteItem, QuoteStatus


class QuoteBuilder:
    """Build complete Quote from QuoteItems with dedup and confidence."""

    def build(
        self, quote_id: str, drawing_id: str,
        part_number: str | None, part_name: str | None, material: str | None,
        items: list[QuoteItem],
        feature_confidence: float | None = None,
        price_version: str | None = None, rule_version: str | None = None,
    ) -> Quote:
        now = datetime.now(timezone.utc).isoformat()
        items = self._dedup(items)
        has_unknown = any(i.source == PriceSource.U for i in items)
        status = QuoteStatus.INCOMPLETE if has_unknown else QuoteStatus.COMPLETE
        confidence, reason = self._compute_confidence(items, feature_confidence)
        cost_completion = self._calculate_cost_completion(items)
        return Quote(
            id=quote_id, drawing_id=drawing_id,
            part_number=part_number, part_name=part_name, material=material,
            items=items, quoted_at=now, quote_date=now[:10],
            price_version=price_version, rule_version=rule_version,
            quotation_status=status.value,
            overall_confidence=round(confidence, 2), confidence_reason=reason,
            cost_completion=cost_completion,
        )

    @staticmethod
    def _dedup(items: list[QuoteItem]) -> list[QuoteItem]:
        """Remove duplicate items, keeping higher-confidence / non-U version."""
        seen: dict[str, QuoteItem] = {}
        for item in items:
            key = f"{item.category}:{item.name.split(chr(32))[0]}"
            if key in seen:
                existing = seen[key]
                if item.amount > 0 and existing.amount == 0:
                    seen[key] = item
                elif item.source != PriceSource.U and existing.source == PriceSource.U:
                    seen[key] = item
            else:
                seen[key] = item
        return list(seen.values())

    def _compute_confidence(self, items: list[QuoteItem], feature_confidence: float | None = None) -> tuple[float, str | None]:
        if not items:
            return 1.0 if feature_confidence is None else feature_confidence, "No items"

        unknown_count = sum(1 for i in items if i.source == PriceSource.U)
        priced = [i for i in items if i.amount > 0]

        if not priced and unknown_count > 0:
            return 0.0, "All items unknown"
        if not priced:
            return 1.0, "All items zero amount"

        total = sum(i.amount for i in priced)
        SW = {PriceSource.C: 1.0, PriceSource.H: 0.8, PriceSource.E: 0.5, PriceSource.M: 0.7, PriceSource.U: 0.0}
        wsum = 0.0
        sc: dict[str, float] = {}
        for item in priced:
            w = SW.get(item.source, 0.3)
            wsum += item.amount * w
            sc[item.source.value] = sc.get(item.source.value, 0) + item.amount

        price_conf = round(wsum / total, 2)
        overall = round(0.4 * feature_confidence + 0.6 * price_conf, 2) if feature_confidence is not None else price_conf

        if unknown_count > 0:
            sc["U"] = unknown_count
            overall = max(overall - unknown_count * 0.2, 0.0)

        parts = [f"{k}={v:.0f}" for k, v in sc.items() if v > 0]
        reason = f"price={price_conf:.0%}"
        if feature_confidence is not None:
            reason += f" feat={feature_confidence:.0%}"
        reason += f" ({', '.join(parts)})"
        if overall >= 0.9: reason += " HIGH"
        elif overall >= 0.6: reason += " MEDIUM"
        elif overall >= 0.3: reason += " LOW"
        else: reason += " UNCERTAIN"
        return overall, reason

    @staticmethod
    def _calculate_cost_completion(items: list[QuoteItem]) -> float:
        """Calculate cost completion percentage.

        An item is considered "completed" when:
        - source is not U (unknown)
        - amount is not None

        amount=0 with a known source (C/H/E/AI/M) is a valid known price,
        e.g. a purchased part with confirmed zero markup.

        Returns:
            Percentage 0.0–100.0, rounded to 1 decimal place.
        """
        if not items:
            return 0.0

        completed = sum(
            1 for i in items
            if i.source != PriceSource.U and i.amount is not None
        )
        total = len(items)
        result = round(completed / total * 100, 1)
        return max(0.0, min(100.0, result))
