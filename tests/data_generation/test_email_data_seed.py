import hashlib
from pathlib import Path

import pytest

from scripts.data_generation.sandbox_databases import generate_email_data

FROZEN_SEED_CHECKSUMS = {
    "data/raw/email_content_pairs.csv": "4e5f3ca71a0495571936fa36f076ab2868d546d2ad96780e5c9ebb661a8c5d5d",
    "data/raw/email_addresses.csv": "d9227ee1a072e528c3735afea166a56e5d2e88f4c98dc7a0beba035ff0efcc2a",
    "data/raw/events.csv": "0abb179439488eeb1c45a1760ddf3628c37af04fd9bc714026c2e09dd836a0fd",
}


def test_generate_email_data_raises_actionable_error_when_seed_missing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(generate_email_data, "CONTENT_PAIRS_PATH", str(tmp_path / "missing.csv"))
    with pytest.raises(FileNotFoundError, match="git checkout"):
        generate_email_data.generate_data()


@pytest.mark.parametrize("path", sorted(FROZEN_SEED_CHECKSUMS))
def test_frozen_seeds_are_unchanged(path: str):
    digest = hashlib.sha256(Path(path).read_bytes()).hexdigest()
    assert digest == FROZEN_SEED_CHECKSUMS[path], (
        f"{path} is a frozen seed: the committed sandbox databases, tasks, outcomes, and inference results "
        f"were all derived from it. It must not be regenerated or edited; restore it with `git checkout -- {path}`."
    )
