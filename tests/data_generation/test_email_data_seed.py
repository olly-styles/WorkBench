from pathlib import Path

import pytest

from scripts.data_generation.sandbox_databases import generate_email_data


def test_generate_email_data_raises_actionable_error_when_seed_missing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(generate_email_data, "CONTENT_PAIRS_PATH", str(tmp_path / "missing.csv"))
    with pytest.raises(FileNotFoundError, match="generate_email_content_pairs"):
        generate_email_data.generate_data()
