import pytest

from src.cli import generate_data


def test_generate_data_refuses_without_force(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]):
    monkeypatch.setattr("sys.argv", ["workbench-generate-data"])
    with pytest.raises(SystemExit) as exc_info:
        generate_data()
    assert exc_info.value.code == 2
    assert "--force" in capsys.readouterr().err


def test_generate_data_help_exits_cleanly(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]):
    monkeypatch.setattr("sys.argv", ["workbench-generate-data", "--help"])
    with pytest.raises(SystemExit) as exc_info:
        generate_data()
    assert exc_info.value.code == 0
    assert "overwriting the committed" in capsys.readouterr().out
