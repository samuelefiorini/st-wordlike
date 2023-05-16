"""Reduce the number of words from input vocabularies."""
from pathlib import Path

import json
import pandas as pd

ROOT = Path(__file__).parent


def read_json(path: str) -> dict:
    with open(str(path), "rt") as f:
        return json.load(f)


def load_vocabulary(path: str) -> list:
    return list(read_json(path).keys())


def main(
    min_word_length: int,
    max_word_length: int,
    min_num_characters: int,
):
    # Get metadata
    metadata = read_json(ROOT.parent.joinpath("vocabularies").joinpath("metadata.json"))

    # Init destination folder
    dst = ROOT.parent.joinpath("vocabularies").joinpath("selected")
    dst.mkdir(parents=True, exist_ok=True)

    # Transform all vocabularies
    words = {}
    for language, filename in metadata.items():
        path = ROOT.parent.joinpath("vocabularies").joinpath("raw").joinpath(filename)
        vocabulary = load_vocabulary(path)
        print(f"Language {language} has {len(vocabulary)} words")
        # Keep only words within contstraints
        selected = list(
            filter(
                lambda w: (len(w) >= min_word_length)
                and (len(w) <= max_word_length)
                and (len(set(w)) > min_num_characters),
                vocabulary,
            )
        )
        df = (
            pd.Series(selected).drop_duplicates().to_frame().rename(columns={0: "word"})
        )
        df["length"] = df["word"].apply(len)
        words[language] = df
        print(f"Only {len(words[language])} are kept")
        words[language].to_csv(dst.joinpath(f"{language}.csv"))


if __name__ == "__main__":
    min_word_length = 3
    max_word_length = 10
    min_num_characters = 3  # min number of different character per word
    main(
        min_word_length=min_word_length,
        max_word_length=max_word_length,
        min_num_characters=min_num_characters,
    )
