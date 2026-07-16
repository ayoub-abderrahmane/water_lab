from pathlib import Path

from src.preprocessing import (
    COLUMNS,
    load_and_clean_data,
    split_features_target,
)

DATA_PATH = Path("data/raw/water_potability.csv")


def test_expected_columns_are_present() -> None:
    dataframe = load_and_clean_data(DATA_PATH)

    assert list(dataframe.columns) == COLUMNS


def test_target_contains_only_binary_values() -> None:
    dataframe = load_and_clean_data(DATA_PATH)

    assert set(dataframe["Potability"].unique()).issubset({0, 1})


def test_features_and_target_are_separated() -> None:
    dataframe = load_and_clean_data(DATA_PATH)

    features, target = split_features_target(dataframe)

    assert "Potability" not in features.columns
    assert len(features) == len(target)