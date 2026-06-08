import pandas as pd

from src.tools._utils import generate_next_id


def test_generate_next_id_increments_max():
    df = pd.DataFrame({"id": ["00000000", "00000004", "00000002"]})
    assert generate_next_id(df, "id") == "00000005"


def test_generate_next_id_empty_dataframe_returns_first_id():
    df = pd.DataFrame({"id": pd.Series([], dtype=str)})
    assert generate_next_id(df, "id") == "00000000"
