from __future__ import annotations

from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from quotation.domain.price_review import PriceReviewRecord, PriceReviewStatus


@pytest.fixture
def client():
    from quotation.api.main import app

    return TestClient(app)


def _review(status: PriceReviewStatus) -> PriceReviewRecord:
    return PriceReviewRecord(
        review_id="RV-TEST",
        price_record_id="PR-TEST",
        supplier_id="SUP-TEST-001",
        status=status,
        review_comment="已核对" if status == PriceReviewStatus.APPROVED else "资料不足",
        reviewed_by="USR-ADMIN",
        reviewed_by_name="管理员",
        reviewed_at="2026-08-05T00:00:00+00:00",
        source_sha256="a" * 64,
        previous_price_version_id="BASE-V1" if status == PriceReviewStatus.APPROVED else None,
        published_price_version_id="CP-NEW-V1" if status == PriceReviewStatus.APPROVED else None,
        published_company_price_id="CP-ROW" if status == PriceReviewStatus.APPROVED else None,
    )


def test_price_approval_api_uses_chinese_results(client, monkeypatch):
    import quotation.api.main as api

    calls = []

    class FakeApproval:
        def list_items(self, _actor, *, status=None, query=None):
            calls.append(("list", status, query))
            return [{"price_record_id": "PR-TEST", "review_status_display": "待审核"}]

        def current_version(self, _actor):
            return "BASE-V1"

        def approve(self, _actor, **kwargs):
            calls.append(("approve", kwargs))
            return _review(PriceReviewStatus.APPROVED)

        def reject(self, _actor, **kwargs):
            calls.append(("reject", kwargs))
            return _review(PriceReviewStatus.REJECTED)

    monkeypatch.setattr(
        api,
        "_price_approval_context",
        lambda _permission, _authorization: (FakeApproval(), SimpleNamespace()),
    )

    listed = client.get(
        "/api/v1/admin/price-approvals", params={"status": "PENDING_REVIEW", "query": "SUS"}
    )
    approved = client.post(
        "/api/v1/admin/price-approvals/SUP-TEST-001/PR-TEST/approve",
        json={"review_comment": "同意发布", "expected_current_version": "BASE-V1"},
    )
    rejected = client.post(
        "/api/v1/admin/price-approvals/SUP-TEST-001/PR-TEST/reject",
        json={"review_comment": "资料不足"},
    )

    assert listed.status_code == 200
    assert listed.json()["当前正式价格版本"] == "BASE-V1"
    assert approved.json()["结果"] == "已批准并发布新正式价格版本"
    assert approved.json()["审核记录"]["published_price_version_id"] == "CP-NEW-V1"
    assert rejected.json()["结果"] == "已驳回，正式价格表未修改"
    assert calls[0] == ("list", "PENDING_REVIEW", "SUS")


def test_price_approval_routes_are_in_openapi(client):
    paths = client.get("/openapi.json").json()["paths"]

    assert "/api/v1/admin/price-approvals" in paths
    assert "/api/v1/admin/price-approvals/{supplier_id}/{price_record_id}/approve" in paths
    assert "/api/v1/admin/price-approvals/{supplier_id}/{price_record_id}/reject" in paths

