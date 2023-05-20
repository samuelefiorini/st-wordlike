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
    is_right_mask = {}
    if len(st.session_state["trials"]):
        columns = table.columns(word_length)
        for word in st.session_state["trials"]:
            # 'NOK' -> char not in word
            # 'Q' -> char in word but wrong place
            # 'OK' -> char in word in right place
            is_right_mask[word] = []
            for i, (col, char) in enumerate(zip(columns, word.upper())):
                if (
                    char.lower()
                    in set(st.session_state["random_word"].lower()).difference(
                        set(word[:i])
                    )
                ) and (st.session_state["random_word"].upper()[i] != char):
                    # char in word, but in the wrong position
                    color = "orange"
                    is_right_mask[word].append({char: "Q"})
                elif (char in st.session_state["random_word"].upper()) and (
                    st.session_state["random_word"].upper()[i] == char
                ):
                    color = "green"
                    is_right_mask[word].append({char: "OK"})
                else:
                    color = "red"
                    is_right_mask[word].append({char: "NOK"})

                with col:
                    st.title(f":{color}[{char}]")

    eligible_words = vocabulary["word"]
    # with st.sidebar:
    #     # Get guessed letters and their number
    #     chars = "".join(st.session_state["trials"])
    #     all_guessed = set(st.session_state["random_word"]).intersection(set(chars))
    #     all_guessed_counts = {
    #         c: Counter(st.session_state["random_word"])[c] for c in all_guessed
    #     }
    #     # Filter words containing the guessed letters with the right count
    #     right_lettering = vocabulary["word"].apply(
    #         lambda w: all(c in w for c in all_guessed)
    #         and all(
    #             Counter(w)[c] == all_guessed_counts.get(c, -1)
    #             for c in set(w).intersection(st.session_state["random_word"])
    #         )
    #     )
    #     eligible_words = vocabulary.loc[right_lettering, "word"]
    #     # Get best guess
    #     if len(st.session_state["trial_points"]) > 0:
    #         best_guess = pd.Series(st.session_state["trial_points"]).idxmax()
    #         if any(
    #             i == "OK"
    #             for i in [list(d.values())[0] for d in is_right_mask[best_guess]]
    #         ):
    #             # Check matches with positions
    #             eligible_words_table = vocabulary["word"].apply(
    #                 lambda x: pd.Series(list(x))
    #             )
    #             right_positions = []
    #             for i, d in enumerate(is_right_mask[best_guess]):
    #                 char, status = list(d.items())[0]
    #                 if status == "OK":
    #                     right_positions.append(eligible_words_table[i] == char.lower())
    #             right_positions.append(
    #                 pd.Series([True] * len(eligible_words_table))
    #             )  # just in case it's empty
    #             right_positions = pd.concat(right_positions, axis="columns").apply(
    #                 all, axis=1
    #             )
    #             eligible_words = vocabulary[right_lettering & right_positions]

    #     if st.checkbox("Show hints"):
    #         st.write(eligible_words["word"].sort_values())

    with st.sidebar:
        st.caption("Stats:")
        st.caption(f"- N° eligible words: {len(eligible_words)}")
        st.caption(
            f"- Chance: {(100 * (max_n_trials - len(st.session_state['trials'])) / len(eligible_words)):.4f} %"
        )

    left, right = st.columns((1, 5))
    with left:
        st.markdown("</br>", unsafe_allow_html=True)
        st.markdown("</br>", unsafe_allow_html=True)
        cheat = st.button("😏 Cheat")
    with right:
        if cheat:
            st.title(
                f"The secret random word is: `{st.session_state['random_word'].upper()}`"
            )

    # assert (
    #     st.session_state["random_word"].lower()
    #     in eligible_words["word"].values.tolist()
    # ), "Wrong hints criteria!"


if __name__ == "__main__":
    main()
