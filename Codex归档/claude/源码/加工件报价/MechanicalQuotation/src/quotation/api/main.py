"""FastAPI application — REST API for the quotation system."""

from __future__ import annotations

import os
import sys
import traceback
import uuid
from pathlib import Path
from typing import Any

# Ensure project root on path
_PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from quotation.application.file_scanner import FileScanner
from quotation.application.quotation_service import QuotationApplicationService
from quotation.infrastructure.ai.deepseek_client import DeepSeekClient
from quotation.infrastructure.secrets.secret_locator import SecretLocator


# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = FastAPI(
    title="機械加工件智能報價系統 API",
    description="Mechanical Quotation System — REST API for quotation processing",
    version="1.0-demo",
    docs_url="/docs",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Service initialization
# ---------------------------------------------------------------------------

_ai_client: DeepSeekClient | None = None
_service: QuotationApplicationService | None = None


def _get_ai_client() -> DeepSeekClient | None:
    global _ai_client
    if _ai_client is None:
        key = SecretLocator.get_deepseek_key()
        if key:
            _ai_client = DeepSeekClient(api_key=key)
    return _ai_client


def _get_service() -> QuotationApplicationService:
    global _service
    if _service is None:
        _service = QuotationApplicationService(ai_client=_get_ai_client())
    return _service


# In-memory job store (demo only)
_jobs: dict[str, Any] = {}


# ---------------------------------------------------------------------------
# Safe filename
# ---------------------------------------------------------------------------

def _safe_filename(original: str) -> str:
    """Sanitize upload filename to prevent path traversal."""
    name = Path(original).name  # Strip any directory components
    # Remove dangerous characters
    safe = "".join(c for c in name if c.isalnum() or c in "._- ")
    return safe or "uploaded_file"


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/api/v1/health")
async def health():
    return {"status": "ok", "service": "mechanical-quotation"}


@app.get("/api/v1/ai/health")
async def ai_health():
    client = _get_ai_client()
    if client is None:
        return {"configured": False, "reachable": False, "model": None, "latency_ms": None, "error": "AI not configured"}
    return client.health_check()


@app.post("/api/v1/quotes/upload")
async def quote_upload(file: UploadFile = File(...)):
    """Upload a single drawing file for quotation."""
    if file.filename is None:
        raise HTTPException(400, "No filename provided")

    safe_name = _safe_filename(file.filename)
    upload_dir = Path("runtime/uploads")
    upload_dir.mkdir(parents=True, exist_ok=True)
    file_path = upload_dir / f"{uuid.uuid4().hex[:8]}_{safe_name}"

    try:
        content = await file.read()
        file_path.write_bytes(content)
    except Exception as e:
        raise HTTPException(500, f"Failed to save file: {e}")

    service = _get_service()
    try:
        result = service.quote_single_file(file_path)
        job_id = result.job_id
        _jobs[job_id] = result
        return result.to_dict()
    except Exception as e:
        raise HTTPException(500, f"Quotation failed: {e}")


@app.post("/api/v1/quotes/batch-upload")
async def batch_upload(files: list[UploadFile] = File(...)):
    """Upload multiple drawing files for batch quotation."""
    upload_dir = Path("runtime/uploads")
    upload_dir.mkdir(parents=True, exist_ok=True)

    saved_paths: list[Path] = []
    for file in files:
        if file.filename is None:
            continue
        safe_name = _safe_filename(file.filename)
        file_path = upload_dir / f"{uuid.uuid4().hex[:8]}_{safe_name}"
        content = await file.read()
        file_path.write_bytes(content)
        saved_paths.append(file_path)

    if not saved_paths:
        raise HTTPException(400, "No valid files uploaded")

    # Scan and batch
    scanner = FileScanner()
    bundles = scanner.scan_directory(upload_dir, recursive=False)

    service = _get_service()
    results = service.quote_batch(bundles)

    batch_id = f"BATCH-{uuid.uuid4().hex[:8]}"
    _jobs[batch_id] = {
        "batch_id": batch_id,
        "results": results,
        "total": len(results),
    }

    return {
        "batch_id": batch_id,
        "total": len(results),
        "complete": sum(1 for r in results if r.is_complete),
        "failed": sum(1 for r in results if r.status in ("PARSE_FAILED", "QUOTE_FAILED")),
    }


@app.get("/api/v1/jobs/{job_id}")
async def get_job(job_id: str):
    """Get job/batch status and results."""
    job = _jobs.get(job_id)
    if job is None:
        raise HTTPException(404, "Job not found")

    if isinstance(job, dict) and "batch_id" in job:
        return {
            "batch_id": job["batch_id"],
            "total": job["total"],
            "results": [r.to_dict() for r in job["results"]],
        }
    return job.to_dict()


@app.get("/api/v1/jobs/{job_id}/excel")
async def get_job_excel(job_id: str):
    """Download batch quotation as Excel."""
    from quotation.application.batch_excel import export_batch_excel

    job = _jobs.get(job_id)
    if job is None:
        raise HTTPException(404, "Job not found")

    if isinstance(job, dict) and "batch_id" in job:
        results = job["results"]
    else:
        results = [job]

    output = Path(f"runtime/exports/quote_{job_id}.xlsx")
    output.parent.mkdir(parents=True, exist_ok=True)

    try:
        export_batch_excel(results, output)
        return FileResponse(str(output), filename=output.name,
                          media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    except Exception as e:
        raise HTTPException(500, f"Excel export failed: {e}")
