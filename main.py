import pandas as pd
import streamlit as st

from pathlib import Path

MIN_HINT_WORDS = 5
ROOT = Path(__file__).parent

st.set_page_config(
    page_title="Wordlike",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded",
)
_ = st.session_state.setdefault("random_word", None)
_ = st.session_state.setdefault("trials", [])


@st.cache_data
def load_vocabulary(path: str, word_length: int) -> pd.Series:
    df = pd.read_csv(path, index_col=0)
    return df[df["length"] == word_length]


def restart():
    st.session_state["random_word"] = None
    st.session_state["trials"] = []
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
        if st.button("🎲 New game") or (
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
    if (len(list(st.session_state["trials"])) <= max_n_trials) and (
        st.session_state["random_word"] not in st.session_state["trials"]
    ):
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
            submitted = st.form_submit_button("🚀 Enter")
            if submitted:
                trial = "".join(trial_parts.values()).lower()
    elif st.session_state["random_word"] in st.session_state["trials"]:
        st.title("🎯 You win!")
    else:
        st.title("💀 GAME OVER")
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
            st.warning("🤦🏻‍♂️ Don't try the same word again!")
        elif not is_legit(trial, vocabulary):
            st.error(f"❌ Unknown word: {trial}")
        elif trial == st.session_state["random_word"]:
            st.success("🎉 Awesome!")
            st.balloons()
            st.session_state["trials"].append(trial)

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

    # ---- HINTS --- #

    eligible_words = vocabulary["word"]
    # Make random word handy
    random_word = pd.Series(list(st.session_state["random_word"]))
    # Convert trials to table with letters
    trials_table = (
        pd.Series(st.session_state["trials"])
        .apply(lambda w: pd.Series(list(w)))
        .transpose()
    )
    # Summarize clues
    if len(trials_table):
        # 1. Guessed letters in right positions
        mask = []
        for i in trials_table.columns:
            mask.append(trials_table[i] == random_word)
        mask = pd.concat(mask, axis=1)
        right_position = (
            trials_table[mask].fillna("").apply(lambda x: "".join(set(x)), axis=1)
        )
        right_position[right_position == ""] = "*"
        right_position_words = vocabulary["word"].apply(
            lambda w: all(
                (c == w[i]) or (c == "*") for i, c in enumerate(right_position)
            )
        )
        # 2. Guessed letters (in wrong position or any)
        mask = trials_table.applymap(lambda c: c in st.session_state["random_word"])
        any_guessed = (
            pd.Series(trials_table[mask].values.ravel())
            .dropna()
            .drop_duplicates()
            .tolist()
        )
        any_guessed_words = vocabulary["word"].apply(
            lambda w: all(i in w for i in any_guessed)
        )
        # 3. Red letters (not in secret word)
        mask = trials_table.applymap(lambda c: c not in st.session_state["random_word"])
        red_letters = (
            pd.Series(trials_table[mask].values.ravel())
            .dropna()
            .drop_duplicates()
            .tolist()
        )
        red_letters_words = vocabulary["word"].apply(
            lambda w: all(i not in w for i in red_letters)
        )

        eligible_words = vocabulary.loc[
            right_position_words & any_guessed_words & red_letters_words,
            ["word"],
        ]

    # ---- STATS --- #

    with st.sidebar:
        if len(eligible_words) > 0:
            chance = min((max_n_trials - len(st.session_state["trials"])) / len(
                eligible_words
            ), 1)
            st.caption("Stats:")
            st.caption(f"- N° eligible words: {len(eligible_words)}")
            st.caption(f"- Chance: {(100 * chance):.4f} %")

            if (len(eligible_words) >= MIN_HINT_WORDS) and st.button("🕵🏻‍♂️ Show hints"):
                hints = eligible_words.sample(MIN_HINT_WORDS).values.ravel().tolist()
                for w in hints:
                    st.caption(f"- {w}")
            elif (len(eligible_words) < MIN_HINT_WORDS) and (st.session_state["random_word"] not in st.session_state["trials"]):
                st.caption("😏 You are almost there...")

            # Sanity check
            assert (
                st.session_state["random_word"].lower()
                in eligible_words.values.ravel().tolist()
            ), "🪲 Oh no! This is a bug."

    # ---- FOOTER --- #

    left, right = st.columns((1, 5))
    with left:
        st.markdown("</br>", unsafe_allow_html=True)
        st.markdown("</br>", unsafe_allow_html=True)
        cheat = st.button("🫣 Cheat")
    with right:
        if cheat:
            st.title(
                f"The secret random word is: `{st.session_state['random_word'].upper()}`"
            )


if __name__ == "__main__":
    main()
