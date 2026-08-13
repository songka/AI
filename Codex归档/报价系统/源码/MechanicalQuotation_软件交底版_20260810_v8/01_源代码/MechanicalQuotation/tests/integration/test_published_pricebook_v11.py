from quotation.infrastructure.rules.pricing_resolver import PricingResolver
from quotation.infrastructure.rules.published_pricebook_loader import PublishedPricebookLoader
from quotation.domain.quote import PriceSource
from quotation.infrastructure.rules.calculators import calc_machining, calc_surface


def test_v11_snapshot_is_active_and_ral9003_is_formal_company_price():
    loader = PublishedPricebookLoader()

    result = loader.lookup_surface("COATING_RAL9003", "m2")

    assert loader.loaded is True
    assert loader.price_version == "R01-COMPANY-PRICE-V1.1"
    assert result is not None
    assert result.unit_price == 25.0
    assert result.unit == "m2"
    assert result.price_basis == "EXCLUDING_TAX"
    assert result.resolution_source == "PUBLISHED_COMPANY_PRICEBOOK"


def test_ral9003_description_resolves_to_published_area_price():
    resolver = PricingResolver()

    result = resolver.lookup("surface", "表面噴塗,顏色:皺紋白,RAL9003")

    assert result is not None
    assert result.unit_price == 25.0
    assert result.unit == "m2"
    assert result.price_version_id == "R01-COMPANY-PRICE-V1.1"
    assert result.resolution_source == "PUBLISHED_COMPANY_PRICEBOOK"


def test_tap_remains_a_review_warning_instead_of_company_price():
    resolver = PricingResolver()

    result = resolver.lookup("process", "TAP")

    assert result is not None
    assert result.company_price_id is None
    assert result.resolution_source == "LEGACY_YAML_DRAFT"
    assert result.fallback_warning is True
    assert result.fallback_approval_status == "DRAFT_REQUIRES_CORRECTION"

    item = calc_machining("TAP", 1.0, resolver.lookup)
    assert item.source == PriceSource.U
    assert item.quote_price_source == "U"
    assert item.fallback_warning is True


def test_ral9003_uses_drawing_area_instead_of_weight():
    resolver = PricingResolver()

    item = calc_surface(
        "表面噴塗,RAL9003",
        weight_kg=99,
        lookup=resolver.lookup,
        surface_area_mm2=2_000_000,
    )

    assert item is not None
    assert item.quantity == 2.0
    assert item.unit == "m2"
    assert item.unit_price == 25.0
    assert item.amount == 50.0
    assert item.resolution_source == "PUBLISHED_COMPANY_PRICEBOOK"
