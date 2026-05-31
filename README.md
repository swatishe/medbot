# 🏥 MedBot - AI-Powered Clinical Policy Assistant

> Hospital staff spend 2+ hours/week hunting through policy PDFs. MedBot answers clinical questions in under 10 seconds, with cited sources from your own documents.

**Stack:** FastAPI · ChromaDB · Claude claude-sonnet-4-20250514 · OpenAI Embeddings · React  
**Deploy:** Railway (backend) + Vercel (frontend) · Free tiers · ~30 minutes

![MedBot Demo](https://img.shields.io/badge/Status-Live-brightgreen) 

---

## How It Works

```
Your PDFs → Chunk → Embed (OpenAI) → ChromaDB
                                          ↓
User Question → Embed → Retrieve Top-5 → Claude → Cited Answer
```

---

##  Full Setup Guide

### Prerequisites
- Python 3.11+
- Node.js 18+
- Git
- Groq API Keys

---

### Step 1 - Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/medbot.git
cd medbot
```

---

### Step 2 - Set Up the Backend

```bash
cd backend

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
```

Open `.env` and fill in your keys:
```
GROQ_API_KEY=sk-...
```

---

### Step 3 - Add Medical Documents

**Option A: Download free sample PDFs (fastest for demo)**
```bash
python ingest.py --download-samples
```

**Option B: Use your own PDFs**
```bash
mkdir -p data
# Copy your PDF files into the data/ folder
cp /path/to/your/policy.pdf data/
```

Then ingest:
```bash
python ingest.py
# Expected output:
# Found 2 PDF(s) in ./data
# Processing: cdc_niosh_guidelines.pdf
#   Extracted 45 pages
# Ingestion complete! 847 chunks indexed.
```

---

### Step 4 - Run the Backend Locally

```bash
uvicorn main:app --reload
# → http://localhost:8000
# → http://localhost:8000/docs  (Swagger UI)
```

Test it:
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the hand hygiene protocol?"}'
```

---

### Step 5 - Run the Frontend Locally

```bash
cd ../frontend

# Install dependencies
npm install

# Set the API URL
cp .env.example .env
# .env already points to http://localhost:8000

npm start
# → http://localhost:3000
```

Your app is now running locally! 

---

### Step 6 - Deploy Backend to Render

1. **Push to GitHub first:**
   ```bash
   cd ..   # back to project root
   git init
   git add .
   git commit -m "Initial MedBot commit"
   git remote add origin https://github.com/YOUR_USERNAME/medbot.git
   git push -u origin main
   ```

2. **Deploy on Render:**
  

---

### Step 7 - Deploy Frontend to Vercel


---


## Project Structure

```
medbot/
├── backend/
│   ├── main.py          # FastAPI app + query endpoint
│   ├── ingest.py        # PDF → ChromaDB pipeline
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── App.js       # Chat UI + source cards
│   │   └── App.css
│   ├── public/
│   ├── package.json
│   ├── vercel.json
│   └── .env.example
└── README.md
```

---

## Extending MedBot

| Feature | How |
|---|---|
| Upload PDFs via UI | Add `POST /ingest` endpoint accepting file uploads |
| Conversation memory | Pass chat history array to Groq messages |
| Auth / multi-tenant | Add JWT middleware + per-org ChromaDB collections |
| Better chunking | Try semantic chunking via `langchain_experimental` |
| Streaming responses | Use `anthropic.messages.stream()` + SSE |
| HIPAA compliance | Self-host embeddings (e.g. onnx) |

---

## Cost Estimate

| Component | Cost |
|---|---|
| Ingest 100-page PDF | ~$0 (Groq embeddings) |
| Hosting | Free (Render + Vercel free tiers) |

---

## License

MIT
