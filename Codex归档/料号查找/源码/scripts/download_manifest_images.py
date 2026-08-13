from __future__ import annotations

import argparse
import mimetypes
import re
import ssl
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

import certifi

from pipeline_common import DATA_DIR, REPORTS_DIR, ROOT, ensure_dirs, read_jsonl


URL_RE = re.compile(r"^https?://", re.IGNORECASE)


def safe_name(value: str) -> str:
    value = re.sub(r"[^A-Za-z0-9._-]+", "_", value.strip())
    return value.strip("._") or "image"


def extension_from_response(url: str, content_type: str | None) -> str:
    parsed_suffix = Path(urlparse(url).path).suffix.lower()
    if parsed_suffix in {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp"}:
        return parsed_suffix
    if content_type:
        guessed = mimetypes.guess_extension(content_type.split(";", 1)[0].strip())
        if guessed in {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp"}:
            return guessed
    return ".img"


def download(url: str, output_dir: Path, stem: str, timeout: int, context: ssl.SSLContext) -> tuple[bool, str, int, str]:
    existing = sorted(output_dir.glob(f"{safe_name(stem)}.*")) if output_dir.exists() else []
    for path in existing:
        if path.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp"} and path.stat().st_size >= 128:
            return True, str(path.relative_to(ROOT)), path.stat().st_size, "already_exists_local"

    request = Request(url, headers={"User-Agent": "Mozilla/5.0 Codex external-part-pipeline"})
    try:
        with urlopen(request, timeout=timeout, context=context) as response:
            status = getattr(response, "status", 200)
            content_type = response.headers.get("Content-Type", "")
            if status >= 400:
                return False, "", 0, f"http_status={status}"
            if content_type and not content_type.lower().startswith("image/"):
                return False, "", 0, f"content_type={content_type}"
            data = response.read()
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        return False, "", 0, str(exc)

    if len(data) < 128:
        return False, "", len(data), "too_small"

    output_dir.mkdir(parents=True, exist_ok=True)
    suffix = extension_from_response(url, content_type)
    path = output_dir / f"{safe_name(stem)}{suffix}"
    if path.exists() and path.read_bytes() == data:
        return True, str(path.relative_to(ROOT)), len(data), "already_exists"
    path.write_bytes(data)
    return True, str(path.relative_to(ROOT)), len(data), "downloaded"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default=str(DATA_DIR / "image_manifest.jsonl"))
    parser.add_argument("--timeout", type=int, default=20)
    args = parser.parse_args()

    ensure_dirs()
    rows = read_jsonl(Path(args.manifest))
    context = ssl.create_default_context(cafile=certifi.where())
    attempted = 0
    successes: list[dict[str, str]] = []
    failures: list[dict[str, str]] = []

    for row in rows:
        image_url = row.get("image_url", "").strip()
        part_no = row.get("part_no", "").strip()
        if not part_no or not URL_RE.match(image_url):
            continue
        attempted += 1
        stem = row.get("normalized_model") or row.get("original_model") or part_no
        ok, local_path, size, note = download(image_url, ROOT / "assets" / part_no, stem, args.timeout, context)
        record = {
            "part_no": part_no,
            "image_url": image_url,
            "local_path": local_path,
            "bytes": str(size),
            "note": note,
        }
        if ok:
            successes.append(record)
        else:
            failures.append(record)

    report_path = REPORTS_DIR / "image_download_manifest.md"
    lines = [
        "# Image Download Report",
        "",
        f"- attempted: {attempted}",
        f"- downloaded_or_existing: {len(successes)}",
        f"- failed: {len(failures)}",
        "",
        "## Successes",
    ]
    lines.extend(f"- {row['part_no']}: {row['local_path']} ({row['note']}, {row['bytes']} bytes)" for row in successes)
    lines.append("")
    lines.append("## Failures")
    lines.extend(f"- {row['part_no']}: {row['image_url']} ({row['note']})" for row in failures)
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"attempted={attempted} successes={len(successes)} failures={len(failures)} report={report_path}")
    if failures:
        sys.exit(1)


if __name__ == "__main__":
    main()
