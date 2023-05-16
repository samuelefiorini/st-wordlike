import pandas as pd
import streamlit as st

from pathlib import Path

ROOT = Path(__file__).parent

st.set_page_config(
    page_title="Wordlike",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded",
)
_ = st.session_state.setdefault("random_word", None)


@st.cache_data
def load_vocabulary(path: str, word_length: int) -> pd.Series:
    df = pd.read_csv(path, index_col=0)
    return df[df["length"] == word_length]


def restart():
    st.session_state["random_word"] = None


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

    # Trials table
    trials = pd.DataFrame(
        [[""] * word_length] * max_n_trials,
        index=[f"Trial {i + 1}" for i in range(max_n_trials)],
        columns=[f"{i + 1}" for i in range(word_length)],
    )
    trials = st.experimental_data_editor(trials, use_container_width=True)

    if cheat:
        st.title(f"The secret random word is: `{st.session_state['random_word']}`")


if __name__ == "__main__":
    main()
