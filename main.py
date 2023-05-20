import pandas as pd
import streamlit as st
from collections import Counter

from pathlib import Path

ROOT = Path(__file__).parent

st.set_page_config(
    page_title="Wordlike",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded",
)
_ = st.session_state.setdefault("random_word", None)
_ = st.session_state.setdefault("trials", [])
_ = st.session_state.setdefault("trial_points", {})


@st.cache_data
def load_vocabulary(path: str, word_length: int) -> pd.Series:
    df = pd.read_csv(path, index_col=0)
    return df[df["length"] == word_length]


def restart():
    st.session_state["random_word"] = None
    st.session_state["trials"] = []
    st.session_state["trial_points"] = {}
    st.experimental_rerun()


def is_legit(trial: str, vocabulary: list) -> bool:
    return trial in vocabulary["word"].values


def get_empty_trials_table(word_length: int, max_n_trials: int) -> pd.DataFrame:
    return pd.DataFrame(
        [[None] * word_length] * max_n_trials,
        index=[f"Trial {i + 1}" for i in range(max_n_trials)],
        columns=[f"{i + 1}" for i in range(word_length)],
    )


def main():
    # Game options
    with st.sidebar:
        lang = st.selectbox("🗣️ Language", ["english"], format_func=lambda t: t.title())
        word_length = st.slider(
            "Word length", min_value=4, max_value=10, value=5, step=1
        )
        max_n_trials = st.slider(
            "N° trials", min_value=3, max_value=10, value=6, step=1
        )
        if st.button("🧹 Restart") or (
            (st.session_state["random_word"] is not None)
            and (word_length != len(st.session_state["random_word"]))
        ):
            restart()
        cheat = st.checkbox("Cheat", False)

    path = ROOT.joinpath("vocabularies").joinpath("selected").joinpath(f"{lang}.csv")
    vocabulary = load_vocabulary(path, word_length)

    # Extract a new random word
    if st.session_state["random_word"] is None:
        st.session_state["random_word"] = vocabulary["word"].sample(1).item()

    # Attempts recap
    table = st.empty()

    # Trials submission
    trial = None
    if len(list(st.session_state["trials"])) <= max_n_trials:
        with st.form("trials_form", clear_on_submit=True):
            trial_parts = {}
            columns = st.columns(word_length)
            for i, col in enumerate(columns):
                with col:
                    trial_parts[i] = st.text_input(
                        f"{i}",
                        key=f"trial_{len(st.session_state['trials'])}_{i}",
                        max_chars=1,
                        placeholder="",
                        label_visibility="collapsed",
                    )

            # Submit a new trial
            submitted = st.form_submit_button("Enter")
            if submitted:
                trial = "".join(trial_parts.values()).lower()
    else:
        st.title("💀 GAME OVER 💀")
        st.write(
            f"The secret random word was: `{st.session_state['random_word'].upper()}`"
        )

    if trial is not None:
        if (
            is_legit(trial, vocabulary)
            and (trial not in list(st.session_state["trials"]))
            and not (trial == st.session_state["random_word"])
        ):
            st.session_state["trials"].append(trial)
            st.experimental_rerun()
        elif trial in list(st.session_state["trials"]):
            st.warning("🤦🏻‍♂️ You cannot submit the same word twice!")
        elif not is_legit(trial, vocabulary):
            st.error(f"❌ Unknown word: {trial}")
        elif trial == st.session_state["random_word"]:
            st.success("🎉 Congratulations!")
            st.balloons()

    # evaluate trial points
    for word in st.session_state["trials"]:
        guessed_any_order = len(
            set(st.session_state["random_word"]).intersection(set(word))
        )
        guessed_right_order = sum(
            [g == c for g, c in zip(word, st.session_state["random_word"])]
        )
        st.session_state["trial_points"][word] = guessed_any_order + guessed_right_order

    # Show trials recap
    if len(st.session_state["trials"]):
        columns = table.columns(word_length)
        for word in st.session_state["trials"]:
            for i, (col, char) in enumerate(zip(columns, word.upper())):
                if (
                    char
                    in set(st.session_state["random_word"].upper()).difference(
                        set(word[:i])
                    )
                ) and (st.session_state["random_word"].upper()[i] != char):
                    # char in word, but in the wrong position
                    color = "orange"
                elif (char in st.session_state["random_word"].upper()) and (
                    st.session_state["random_word"].upper()[i] == char
                ):
                    color = "green"
                else:
                    color = "red"

                with col:
                    st.title(f":{color}[{char}]")

    if cheat:
        st.sidebar.title(
            f"The secret random word is: `{st.session_state['random_word'].upper()}`"
        )

    with st.sidebar:
        n_words = len(vocabulary["word"])
        # Filter words containing guessed chars
        chars = "".join(st.session_state["trials"])
        all_guessed = set(st.session_state["random_word"]).intersection(set(chars))
        all_guessed_counts = {
            c: Counter(st.session_state["random_word"])[c] for c in all_guessed
        }
        if len(all_guessed) > 0:
            st.write(all_guessed_counts)
        right_lettering = vocabulary["word"].apply(
            lambda w: all(c in w for c in all_guessed)
            and all(
                Counter(w)[c] == all_guessed_counts.get(c, -1)
                for c in set(w).intersection(st.session_state["random_word"])
            )
        )

        eligible_words = vocabulary[right_lettering]
        if st.checkbox("Show hints"):
            st.write(eligible_words["word"])

        st.caption("Stats:")
        st.caption(f"- N° eligible words: {len(eligible_words)}")
        st.caption(
            f"- Chance: {(100 * (max_n_trials - len(st.session_state['trials'])) / len(eligible_words)):.2f} %"
        )


if __name__ == "__main__":
    main()
