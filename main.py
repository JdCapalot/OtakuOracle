import streamlit as st
from recommender import MAL_GENRES, get_default_recs, recommend_anime

st.set_page_config(page_title="OtakuOracle", page_icon="🔮", layout="centered")
st.title("🔮 OtakuOracle")
st.write("Select genre(s), enter what you’re in the mood for, or pick one of the suggestions below:")

# Genre multiselect
genres = st.multiselect(
    "Pick anime genre(s)",
    options=list(MAL_GENRES.keys()),
    key="genre_select"
)

# Free-text input
if "user_input" not in st.session_state:
    st.session_state.user_input = ""
st.text_input(
    "Or type a custom query (e.g. 'under 20 episodes', 'hidden gem action')",  
    key="user_input"
)

# Suggestion buttons callback
def set_suggestion(sugg: str):
    st.session_state.user_input = sugg

# Clickable keyword suggestions
SUGGESTIONS = ["action hidden gem", "romance under 20", "comedy short", "dark thriller"]
cols = st.columns(len(SUGGESTIONS))
for col, suggestion in zip(cols, SUGGESTIONS):
    col.button(
        suggestion,
        key=f"sugg_{suggestion}",
        on_click=set_suggestion,
        kwargs={"sugg": suggestion}
    )

# Determine which recommendations to show
if genres:
    # User selected via dropdown
    st.subheader(f"Recommendations for genre(s): {', '.join(genres)}")
    query = " ".join(genres)
    results = recommend_anime(query)
elif st.session_state.user_input.strip():
    # User typed a free-form query
    user_input = st.session_state.user_input.strip()
    st.subheader(f"Recommendations for '{user_input}'")
    results = recommend_anime(user_input)
else:
    # Default trending picks
    st.subheader("🔥 Trending Picks to Get You Started")
    results = get_default_recs()

# Display results
for anime in results:
    st.markdown(f"**{anime['title']}** — [More Info]({anime['url']})")