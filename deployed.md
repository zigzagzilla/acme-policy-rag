# Deployed Application

## Status

> **Stub — deployment pending.**  
> The application has not yet been pushed to a public hosting provider (Render, Railway, etc.).  
> Update this file with the live URL once deployment is complete.

---

## Running Locally / on Replit

The app runs on Replit's preview at the project URL while the **Start application** workflow is active.

To run locally:

```bash
# 1. Clone the repo
git clone https://github.com/zigzagzilla/acme-policy-rag.git
cd acme-policy-rag

# 2. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set environment variables (copy and fill in .env.example)
cp .env.example .env
# Edit .env — add your OpenRouter API key as OPENAI_API_KEY

# 5. Ingest policy documents into ChromaDB
python ingest.py

# 6. Start the app
python app.py
# Open http://localhost:5000
```

---

## Deployment Instructions (when ready)

### Render

1. Create a new **Web Service** on [render.com](https://render.com), connected to this repo.
2. Set **Build Command**: `pip install -r requirements.txt && python ingest.py`
3. Set **Start Command**: `python app.py`
4. Add environment variables (from `.env.example`) in the Render dashboard.
5. Update the URL below once live.

### Railway

1. Connect this repo to a new Railway project.
2. Set the start command: `python ingest.py && python app.py`
3. Add environment variables in the Railway dashboard.
4. Update the URL below once live.

---

## Live URL

```
# Replace this line with the public URL once deployed
# e.g. https://acme-policy-rag.onrender.com
```
