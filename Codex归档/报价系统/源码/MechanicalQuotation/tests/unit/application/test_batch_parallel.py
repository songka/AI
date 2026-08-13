from __future__ import annotations

import threading
import time
from types import SimpleNamespace

from quotation.application.quotation_service import QuotationApplicationService


def test_batch_runs_independent_jobs_in_parallel_and_preserves_order(monkeypatch):
    service = QuotationApplicationService()
    bundles = [
        SimpleNamespace(
            drawing_number=f"P-{index}",
            geometry_source=SimpleNamespace(extension=".dxf"),
        )
        for index in range(4)
    ]
    lock = threading.Lock()
    active = 0
    max_active = 0
    completed_indices = []

    def process(bundle, _use_ai):
        nonlocal active, max_active
        index = int(bundle.drawing_number.split("-")[1])
        with lock:
            active += 1
            max_active = max(max_active, active)
        time.sleep(0.02 * (4 - index))
        with lock:
            active -= 1
        return SimpleNamespace(drawing_number=bundle.drawing_number, batch_index=None)

    monkeypatch.setattr(service, "_process_bundle", process)
    results = service.quote_batch(
        bundles,
        max_workers=4,
        progress_callback=lambda _done, _total, result: completed_indices.append(
            result.batch_index
        ),
    )

    assert max_active >= 2
    assert [result.drawing_number for result in results] == [f"P-{i}" for i in range(4)]
    assert sorted(completed_indices) == [0, 1, 2, 3]


def test_solidworks_batch_is_kept_serial(monkeypatch):
    service = QuotationApplicationService()
    bundles = [
        SimpleNamespace(
            drawing_number=f"SW-{index}",
            geometry_source=SimpleNamespace(extension=".sldprt"),
        )
        for index in range(2)
    ]
    thread_ids = []

    def process(bundle, _use_ai):
        thread_ids.append(threading.get_ident())
        return SimpleNamespace(drawing_number=bundle.drawing_number, batch_index=None)

    monkeypatch.setattr(service, "_process_bundle", process)
    service.quote_batch(bundles, max_workers=4)

    assert len(set(thread_ids)) == 1
