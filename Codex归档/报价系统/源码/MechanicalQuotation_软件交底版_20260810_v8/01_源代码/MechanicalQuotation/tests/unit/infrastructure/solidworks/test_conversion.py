from quotation.infrastructure.dwg.converter import ConversionStatus
from quotation.infrastructure.solidworks.converter import SolidWorksConversionService


def test_missing_solidworks_returns_actionable_error(tmp_path, monkeypatch):
    source = tmp_path / "零件.SLDPRT"
    source.write_bytes(b"native-solidworks")
    monkeypatch.setattr(SolidWorksConversionService, "is_available", staticmethod(lambda: False))

    result = SolidWorksConversionService(tmp_path / "cache").convert(source)

    assert result.status == ConversionStatus.NOT_CONFIGURED
    assert "安装" in (result.error or "")
    assert "SOLIDWORKS" in (result.error or "")
