from quotation import launcher


def test_no_arguments_launches_ui(monkeypatch):
    calls = []
    monkeypatch.setattr("sys.argv", ["MechanicalQuotation.exe"])
    monkeypatch.setattr(launcher, "launch_ui", lambda: calls.append("ui"))

    launcher.main()

    assert calls == ["ui"]


def test_explicit_ui_still_launches_ui(monkeypatch):
    calls = []
    monkeypatch.setattr("sys.argv", ["MechanicalQuotation.exe", "--ui"])
    monkeypatch.setattr(launcher, "launch_ui", lambda: calls.append("ui"))

    launcher.main()

    assert calls == ["ui"]
