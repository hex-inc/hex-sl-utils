"""Copied calc result-test helpers."""

from __future__ import annotations

import polars as pl


def floatify(df: pl.DataFrame) -> pl.DataFrame:
    """
    Convert all Decimal columns to Float64
    """
    for col in df.columns:
        if df[col].dtype == pl.Decimal:
            df = df.with_columns(pl.col(col).cast(pl.Float64))
    return df
