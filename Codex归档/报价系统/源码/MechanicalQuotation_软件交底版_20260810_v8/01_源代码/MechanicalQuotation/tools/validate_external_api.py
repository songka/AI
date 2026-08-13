"""Exercise the live FastAPI multipart workflow used by Swagger UI."""

from __future__ import annotations

import argparse
import json
from contextlib import ExitStack
from pathlib import Path

import httpx


def _multipart(paths: list[Path], stack: ExitStack):
    return [
        ("files", (path.name, stack.enter_context(path.open("rb")), "application/octet-stream"))
        for path in paths
    ]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8766")
    parser.add_argument("--samples", type=Path, default=Path("samples/drawings"))
    args = parser.parse_args()

    names = [
        "UC1000005854-J003.DWG",
        "UC1000005854-J003.PDF",
        "UC1000005855-J005.DWG",
        "UC1000005855-J005.PDF",
    ]
    client = httpx.Client(base_url=args.base_url, timeout=180)
    openapi = client.get("/openapi.json").raise_for_status().json()
    upload_schema = openapi["paths"]["/api/v1/quotes/batch-upload"]["post"]["requestBody"]
    assert "multipart/form-data" in upload_schema["content"]

    with ExitStack() as stack:
        response = client.post(
            "/api/v1/quotes/batch-upload",
            files=_multipart([args.samples / name for name in names], stack),
            data={"use_ai": "false"},
        )
    response.raise_for_status()
    batch = response.json()
    details = client.get(f"/api/v1/jobs/{batch['batch_id']}").raise_for_status().json()
    excel = client.get(f"/api/v1/jobs/{batch['batch_id']}/excel").raise_for_status()
    excel_path = Path("runtime/validation/m2/swagger-batch.xlsx")
    excel_path.parent.mkdir(parents=True, exist_ok=True)
    excel_path.write_bytes(excel.content)

    with ExitStack() as stack:
        unsupported_response = client.post(
            "/api/v1/quotes/batch-upload",
            files=_multipart([args.samples / "UC1004001894-F022.SLDPRT.PDF"], stack),
        )
    unsupported_response.raise_for_status()
    unsupported_batch = unsupported_response.json()
    unsupported = client.get(
        f"/api/v1/jobs/{unsupported_batch['batch_id']}"
    ).raise_for_status().json()["results"][0]

    summary = {
        "swagger_multipart_schema": True,
        "batch_response": batch,
        "drawing_numbers": [item["drawing_number"] for item in details["results"]],
        "paired_source_files": [item["source_files"] for item in details["results"]],
        "statuses": [item["status"] for item in details["results"]],
        "pdf_text_counts": [
            item["supplementary_analysis"][0]["text_count"] for item in details["results"]
        ],
        "excel": {"path": str(excel_path), "bytes": len(excel.content)},
        "chinese_error": unsupported["errors"][0],
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
