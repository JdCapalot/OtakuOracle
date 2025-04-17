# OtakuOracle

OtakuOracle is a Streamlit app that recommends anime based on your preferences—genres, themes, episode count, or even those "hidden gems" you’ve been meaning to watch. It pulls data from:

- **MyAnimeList (via Jikan v4)** for genre-based lookups, top charts, and keyword search
- **AniList GraphQL API** as a fallback when MAL data is sparse
- **spaCy** to parse and understand multi-word phrases and key descriptors
- Local JSON files in the `data/` folder to cache API responses and speed up repeat queries

## Prerequisites

- Python 3.8 or higher
- Git (to clone the repo)

## Installation

1. **Clone this repository**
   ```bash
   git clone https://github.com/<your-username>/OtakuOracle.git
   cd OtakuOracle
   ```

2. **Set up a virtual environment**

   - **Windows (Command Prompt)**
     ```bash
     py -3 -m venv .venv
     .\.venv\Scripts\activate.bat
     ```

   - **macOS/Linux**
     ```bash
     python3 -m venv .venv
     source .venv/bin/activate
     ```

3. **Install the required packages**
   ```bash
   pip install -r requirements.txt
   python -m spacy download en_core_web_sm
   ```

4. **Prepare the cache folder** (optional—app will create it automatically on first run)
   ```bash
   mkdir data
   ```

## Running the App

Launch OtakuOracle with Streamlit:

```bash
streamlit run main.py
```

Your browser will open at http://localhost:8501, or you can navigate to that URL manually.

## NLP Strategies

Under the hood, we use **spaCy** to turn your text into actionable filters:

- **Part‑of‑Speech Filtering**: Extracts nouns and adjectives (`adventure`, `funny`, `dark`).
- **Noun Chunks**: Captures phrases like **"slice of life"** or **"post apocalyptic"** in one go.
- **Pattern Matching**: Detects `under 20 episodes` or `hidden gem` to apply episode or rating constraints.

These parsed keywords drive our data fetch and filtering logic, resulting in personalized anime recommendations.

## Project Structure

```
OtakuOracle/
├── data/                  # Cached API responses (JSON files)
├── main.py                # Streamlit interface
├── recommender.py         # NLP parsing, API calls, caching, recommendation logic
├── requirements.txt       # Dependencies list
├── README.md              # This guide
└── LICENSE                # Project license (MIT)
```

## Contributing

If you find a bug, have a feature idea, or want to help improve the app, please open an issue or submit a pull request. Your feedback is welcome!

## License

This project is released under the MIT License. See [LICENSE](LICENSE) for details.

