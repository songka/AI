"""Test fixtures for rules unit tests.

Isolates unit tests from production Current Version Pointer:
- Uses test-specific YAML rules file
- Patches PublishedPricebookLoader to skip loading
- Regular unit tests never read data/current-version-pointer.json
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from quotation.infrastructure.rules.pricing_resolver import PricingResolver

TEST_RULES = Path(__file__).parent / "test_rules.yaml"


@pytest.fixture
def resolver():
    """PricingResolver with test YAML, NO published pricebook loading.

    Patches DEFAULT_POINTER_PATH to a non-existent file so the
    PublishedPricebookLoader never loads anything, ensuring
    unit tests are isolated from production data.
    """
    with patch(
        "quotation.infrastructure.rules.published_pricebook_loader.DEFAULT_POINTER_PATH",
        Path("/nonexistent/test-pointer.json"),
    ):
        yield PricingResolver(rules_path=TEST_RULES)
