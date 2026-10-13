import csv
import io
from pathlib import Path
from typing import BinaryIO

import pandas as pd

MAX_UPLOAD_BYTES = 20 * 1024 * 1024


class DatasetValidationError(ValueError):
    """Raised when uploaded content is empty, malformed, or incompatible."""


def _decode_csv_bytes(raw: bytes) -> str:
    if len(raw) > MAX_UPLOAD_BYTES:
        raise DatasetValidationError(f"Uploaded file exceeds the maximum size of {MAX_UPLOAD_BYTES // (1024 * 1024)} MB.")
    if not raw or not raw.strip():
        raise DatasetValidationError("The uploaded file is empty.")
    if b"\x00" in raw:
        raise DatasetValidationError("The file appears to be binary or malformed CSV content.")

    for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            text = raw.decode(encoding)
        except UnicodeDecodeError:
            continue
        if not text.strip():
            raise DatasetValidationError("The uploaded file is empty.")
        if "\x00" in text:
            raise DatasetValidationError("The file contains null bytes and is not a valid CSV file.")
        return text

    raise DatasetValidationError("The file could not be decoded as UTF-8 or a common CSV encoding.")


def _detect_delimiter(sample: str) -> str:
    try:
        dialect = csv.Sniffer().sniff(sample[:4096], delimiters=",	;|")
        return dialect.delimiter
    except csv.Error:
        return ","


def load_csv_from_bytes(raw_data: bytes | BinaryIO | str, *, max_bytes: int = MAX_UPLOAD_BYTES) -> pd.DataFrame:
    if hasattr(raw_data, "read"):
        raw_data = raw_data.read()

    if isinstance(raw_data, str):
        raw_data = raw_data.encode("utf-8")

    if not isinstance(raw_data, (bytes, bytearray)):
        raise DatasetValidationError("Unsupported file payload; expected CSV bytes or a file-like object.")

    payload = bytes(raw_data)
    if len(payload) > max_bytes:
        raise DatasetValidationError(f"The uploaded file exceeds the configured limit of {max_bytes // (1024 * 1024)} MB.")

    text = _decode_csv_bytes(payload)
    delimiter = _detect_delimiter(text)

    try:
        rows = list(csv.reader(io.StringIO(text), delimiter=delimiter))
    except Exception as exc:  # pragma: no cover
        raise DatasetValidationError(f"The CSV file could not be parsed: {exc}") from exc

    if not rows or not any(row for row in rows):
        raise DatasetValidationError("The CSV file is empty or has no usable rows.")

    header = rows[0]
    seen = set()
    duplicate_columns = []
    for column_name in header:
        if column_name in seen and column_name not in duplicate_columns:
            duplicate_columns.append(column_name)
        seen.add(column_name)
    if duplicate_columns:
        raise DatasetValidationError(f"duplicate column names detected: {', '.join(duplicate_columns)}.")

    try:
        df = pd.read_csv(
            io.StringIO(text),
            sep=delimiter,
            engine="python",
            on_bad_lines="error",
            dtype_backend="numpy_nullable",
        )
    except pd.errors.EmptyDataError as exc:
        raise DatasetValidationError("The CSV file is empty or has no usable rows.") from exc
    except Exception as exc:  # pragma: no cover - exercised by integration tests through real parser behavior
        raise DatasetValidationError(f"The CSV file could not be parsed: {exc}") from exc

    if df.empty:
        raise DatasetValidationError("The CSV file contains no rows after parsing.")

    if not list(df.columns):
        raise DatasetValidationError("The CSV file has no columns.")

    return df


def upload_csv_to_temp(file_bytes: bytes, destination_dir: str | Path) -> Path:
    destination = Path(destination_dir)
    destination.mkdir(parents=True, exist_ok=True)
    csv_path = destination / "uploaded_dataset.csv"
    csv_path.write_bytes(file_bytes)
    return csv_path
