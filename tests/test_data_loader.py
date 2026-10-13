import io

import pandas as pd
import pytest

from utils.data_loader import DatasetValidationError, load_csv_from_bytes


@pytest.mark.parametrize(
    "content, expected_error",
    [
        (b"", DatasetValidationError),
        (b"a,b\n1,2\n3,4\n", None),
    ],
)
def test_csv_loading_and_validation(content, expected_error):
    if expected_error:
        with pytest.raises(expected_error):
            load_csv_from_bytes(content)
    else:
        df = load_csv_from_bytes(content)
        assert isinstance(df, pd.DataFrame)
        assert not df.empty


def test_duplicate_columns_are_rejected():
    payload = b"col1,col1\n1,2\n3,4\n"
    with pytest.raises(DatasetValidationError, match="duplicate"):
        load_csv_from_bytes(payload)


def test_non_utf8_payload_is_rejected_for_malformed_data():
    payload = b"\xff\xfe\x00\x00"
    with pytest.raises(DatasetValidationError):
        load_csv_from_bytes(payload)
