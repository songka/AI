from __future__ import annotations

import json

from tools.bootstrap_supplier_data import bootstrap_supplier_master


def test_bootstrap_supplier_master_preserves_unknown_tax_and_never_overwrites(tmp_path):
    source = tmp_path / "source.json"
    source.write_text(
        json.dumps(
            {
                "supplier_master": [
                    {
                        "supplier_id": "SUP-ONE",
                        "supplier_name": "供应商一",
                        "default_tax_inclusion_status": "UNKNOWN",
                    }
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    root = tmp_path / "smb"

    first = bootstrap_supplier_master(source, root)
    second = bootstrap_supplier_master(source, root)
    payload = json.loads((root / "suppliers" / "suppliers.json").read_text(encoding="utf-8"))

    assert first["状态"] == "已建立"
    assert second["状态"] == "已跳过"
    assert payload["suppliers"][0]["default_tax_included"] is None
