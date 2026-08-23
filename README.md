 🛒 EchoCart — Voice Command Shopping Assistant

A voice-powered shopping list manager with natural language understanding, smart recommendations, and multilingual support. Built as a technical assessment project demonstrating full-stack thinking: voice input, NLP command parsing, persistent storage, and a polished UI — all in a deliberately simple, explainable architecture.

**Live App:** https://voicecommander-kzxw5emzuqktq2nmyrqyrs.streamlit.app/
**Repository:** https://github.com/rishikamurugesh602/Voice_Commander

---

## Features

### Voice Input & NLP
- Voice command recognition via browser microphone
- Natural language understanding for varied phrasing ("Add milk" / "I need milk" / "I want to buy milk")
- Multilingual support (English, Hindi, Tamil) for core commands
- Rule-based intent detection + entity extraction (no black-box ML — fully explainable)

### Shopping List Management
- Add, remove, and update items by voice or text
- Automatic categorization (Dairy, Produce, Bakery, etc.)
- Voice-based quantity management ("Add 2 bottles of water")

### Voice-Activated Search
- Search by product name, brand, or price range
- Examples: "Find organic apples", "Find toothpaste under 200 rupees", "Find Colgate toothpaste"

### Smart Suggestions
- Frequency-based recommendations from purchase history ("You're running low on bread")
- Seasonal product suggestions
- Substitution suggestions (e.g., almond milk / soy milk for milk)

### UI/UX
- Custom-styled, minimalist dark interface (not default Streamlit styling)
- Real-time visual feedback, confirmation banners, loading states
- Empty and error states for every major interaction
- Recent commands panel with success/failure logging
- Mobile-responsive layout

---

## Tech Stack

**App Framework — Streamlit**
Fast to build, free hosting, keeps the entire stack in Python.

**Speech-to-Text — Google Web Speech API** (via `SpeechRecognition`)
Free, no API key required, supports Indian English/Hindi/Tamil locales.

**NLU — Custom rule-based engine** (regex + `rapidfuzz` fuzzy matching)
Deterministic and explainable, reliable for a bounded command vocabulary — no training data needed.

**Database — SQLite**
Zero-config, file-based, sufficient for single-user local persistence.

**Styling — Custom CSS** injected into Streamlit
Avoids the default Streamlit look.

**Hosting — Streamlit Community Cloud**
Free, git-push-to-deploy.

## Architecture

Voice Input (browser mic)
↓
streamlit-mic-recorder (capture audio)
↓
voice_service.py (Google Speech-to-Text → transcript)
↓
nlu_engine.py (transcript → intent + entities)
↓
command_handler.py (orchestrates action)
↓
db_service.py (SQLite read/write)
↓
UI feedback (Streamlit re-render)


Each layer has a single responsibility and can be tested independently:
- `nlu_engine.py` was built and unit-tested with plain text *before* voice was wired in, isolating language-understanding bugs from speech-recognition bugs.
- `command_handler.py` is the only file that connects NLU output to database actions.
- `db_service.py` is the only file that writes raw SQL.

---

## Project Structure

## Project Structure

```
voice-shopping-assistant/
├── app.py                        # Streamlit entrypoint
├── requirements.txt
├── packages.txt                  # System-level deps (ffmpeg) for deployment
├── README.md
├── .gitignore
│
├── services/
│   ├── voice_service.py          # Mic audio -> text (Speech-to-Text)
│   ├── nlu_engine.py             # Text -> intent + entities
│   ├── command_handler.py        # Orchestrates NLU -> DB actions
│   ├── recommendation_engine.py  # Frequency + seasonal suggestions
│   └── db_service.py             # All SQLite operations
│
├── database/
│   └── schema.sql                # Table definitions
│
├── data/
│   ├── products.json             # Seed product catalog
│   ├── substitutions.json        # Substitution map
│   └── seasonal.json             # Month -> seasonal items
│
├── components/
│   └── ui_helpers.py             # Reusable render functions
│
└── assets/
    └── style.css                 # Custom styling
```

## Database Schema

- **`products`** — Product catalog: name, brand, category, price, unit
- **`shopping_list`** — Current cart: item, category, quantity
- **`purchase_history`** — Simulated past purchases (seeded), powers recommendations
- **`command_history`** — Every executed command, logged for debugging and the "Recent Commands" panel


## NLU Design

Commands are parsed through a five-stage pipeline: normalize → detect intent → extract quantity → extract price/brand filters → extract item (exact match, then fuzzy match via `rapidfuzz` against the product catalog).

**Why rule-based instead of an ML model:** the command vocabulary is small and bounded (~10 command patterns). A rule-based approach gives near-100% accuracy on this scope, is fully explainable/debuggable, has zero inference latency, and requires no training data — all of which matter more than raw NLP sophistication in this context. `command_history` doubles as a live debugging tool, showing exactly what was parsed from every input.

---

## Setup Instructions (Local)

```bash
git clone https://github.com/rishikamurugesh602/Voice_Commander.git
cd Voice_Commander

python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux

pip install -r requirements.txt

streamlit run app.py
```

The app opens at `http://localhost:8501`. The SQLite database and seed data are created automatically on first run.

**Note:** Voice input requires `ffmpeg` installed and on your system PATH (used by `pydub` for audio format conversion). See [ffmpeg.org/download.html](https://ffmpeg.org/download.html).

---

## Testing

Try these example commands (via voice or the text input fallback):

- "Add milk"
- "I need 2 bottles of water"
- "I want to buy five apples"
- "Remove milk"
- "Change apples to 10"
- "Find organic apples"
- "Find toothpaste under 200 rupees"
- "Find Colgate toothpaste"
- "Show alternatives for milk"

For Hindi/Tamil, select the language from the dropdown before recording (core commands supported: add/remove/search for a subset of common items).

---

## Known Limitations

- **Multilingual coverage is partial** — Hindi/Tamil support covers core commands and common products, not the full catalog. This was a deliberate scope decision for the assessment's time budget; a production version would use a translation API or a complete localization table.
- **Persistence resets on redeploy** — Streamlit Community Cloud's filesystem is ephemeral, so the SQLite database resets when the app restarts after inactivity. Production would use a hosted database (e.g. Postgres).
- **Speech recognition accuracy** depends on network connectivity (Google's API requires internet) and varies with accent/background noise.
- **No user authentication** — single shared list, appropriate for a demo but not multi-user.

---

## Future Improvements

- Full multilingual catalog coverage or translation-API-based approach
- Persistent cloud database for production deployment
- Optional LLM-based NLU layer for handling more varied/ambiguous phrasing, alongside the existing rule-based system as a fast-path
- User accounts and multiple shopping lists
- Real product images and a live pricing API

---

## Author

Built by Rishika Murugesh
