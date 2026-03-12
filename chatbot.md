# Chatbot Implementation Plan

## Goal

Build a conversational chatbot that understands the Ocean Freight Optimizer's data (scraped rates, processed Excel files, configuration) and answers natural-language questions like:

- *"What's the cheapest route to Valence, France for a 40HC container?"*
- *"Compare ONE vs HAPAG rates to Muenster, Germany."*
- *"Which POD gives the lowest inland rate to Tampere?"*
- *"What transport modes are available to Oegstgeest?"*

---

## Architecture Options (Ranked by Efficiency)

### Option A — RAG over Structured Data (Recommended)

```
┌──────────────┐     ┌────────────────────┐     ┌──────────────────┐
│  Excel Files │────►│  Data Extraction   │────►│  Vector Store /  │
│  .md files   │     │  (Python scripts)  │     │  Context Builder │
│  JSON config │     └────────────────────┘     └────────┬─────────┘
└──────────────┘                                         │
                                                         ▼
              ┌──────────────┐     ┌──────────────────────────────┐
              │   User Chat  │────►│  LLM API (GPT / Gemini)     │
              │   Interface  │◄────│  + System Prompt + Context   │
              └──────────────┘     └──────────────────────────────┘
```

**How it works:**
1. On startup (or on data refresh), read Excel files and convert rows to structured text/JSON chunks.
2. When a user asks a question, determine which data is relevant (destination filter, carrier filter, etc.).
3. Build a context window: system prompt (explains the domain) + relevant data rows + user question.
4. Send to OpenAI/Gemini API → return answer.

**Why this is the best approach for this project:**
- The dataset is **small** (hundreds of rows, not millions) — no vector database needed.
- Data is **structured** (tabular Excel) — direct lookup is faster and more accurate than semantic search.
- Avoids hallucination by injecting real numbers into the prompt.

### Option B — Naive "Send Everything" Approach

Send all `.md` files + all Excel data as a giant prompt to the LLM every time.

| Pros | Cons |
|------|------|
| Simplest to implement | Token cost grows with data |
| No preprocessing needed | Hits context limits with large datasets |
| | Slower responses |
| | LLM may hallucinate on large noisy context |

**Verdict:** Works for a prototype with small data. Not scalable.

### Option C — Full RAG with Vector DB (Chroma / Pinecone)

Embed all data chunks into a vector store, do semantic retrieval on each query.

| Pros | Cons |
|------|------|
| Scales to massive datasets | Overkill for ~300 rows of rate data |
| Standard RAG pattern | Adds infra complexity (embedding model, vector DB) |
| | Structured numeric data doesn't embed well semantically |

**Verdict:** Unnecessary for this dataset size. Consider only if data grows 100x+.

---

## Recommended Architecture — Option A Details

### Why Not Just Send .md Files?

Your instinct (store data + md files → send to LLM) is reasonable for a prototype but has limits:

| Concern | Impact |
|---------|--------|
| Token cost | Sending 50KB+ of markdown on every query wastes money |
| Accuracy | LLM may misread table formatting in markdown |
| Staleness | .md files are static — Excel data changes with each scrape |
| Precision | For "cheapest route to X," a database query beats an LLM every time |

**The hybrid approach is better:** Use Python to do the precise data lookups, then send only the relevant slice to the LLM for natural-language formatting and reasoning.

---

## Implementation Plan

### Phase 1 — Backend Chat API

#### 1.1 Data Layer (`chatbot/data_loader.py`)

```python
"""
Load and cache all data sources into queryable DataFrames.
Reuses the same loading logic from api_server.py.
"""
import pandas as pd
import json, glob, os

class FreightDataLoader:
    def __init__(self):
        self.one_data: pd.DataFrame = None      # Processed ONE rates
        self.hapag_data: pd.DataFrame = None     # HAPAG surcharges
        self.ocean_freight: pd.DataFrame = None  # Ocean freight base rates
        self.destinations: dict = {}             # destination_configs.json
        self.load_all()

    def load_all(self):
        # Load ONE processed data
        # Load HAPAG surcharges
        # Load ocean_freight.xlsx
        # Load destination_configs.json

    def get_routes(self, destination, container_type=None) -> pd.DataFrame:
        """Filter ONE data by destination and optional container type."""

    def get_hapag_charges(self, destination) -> pd.DataFrame:
        """Filter HAPAG data by destination."""

    def get_cheapest_route(self, destination, container_type) -> dict:
        """Return rank-1 route for given destination + container."""

    def compare_carriers(self, destination, container_type) -> dict:
        """Side-by-side ONE vs HAPAG comparison."""

    def summarize_data(self) -> str:
        """Return a text summary of available data for system prompt."""
```

#### 1.2 Context Builder (`chatbot/context_builder.py`)

```python
"""
Analyze the user's question, pull relevant data, and build
the context that gets sent to the LLM.
"""

class ContextBuilder:
    def __init__(self, data_loader: FreightDataLoader):
        self.data = data_loader
        self.system_prompt = self._build_system_prompt()

    def _build_system_prompt(self) -> str:
        """
        System prompt explaining:
        - What this system does (freight rate comparison)
        - Available carriers (ONE Line, HAPAG-Lloyd)
        - Data fields (POD, inland rate, ocean rate, total rate, etc.)
        - Full list of available destination names (for LLM fallback matching)
        - Container types
        - Rules: answer from data only, match misspelled destinations,
          respond in user's language (Korean, English, etc.)
        """

    def _match_destination(self, msg_lower: str, destinations: list) -> str | None:
        """
        Two-step fuzzy matching:
        1. Exact substring scan (longest city name first, + squashed variants)
        2. difflib.get_close_matches() on message tokens (cutoff=0.65)
        Returns the canonical destination name or None.
        """

    def build_context(self, user_message: str, history: list = None) -> list[dict]:
        """
        1. Parse intent (destination via fuzzy match, carrier, comparison, general?)
        2. Query DataFrames for relevant rows (with contains-fallback)
        3. Format as compact text/JSON
        4. Return [system_prompt, ...history, data_context + user_message]
        """
```

Intent detection uses keyword matching for query type + **fuzzy matching** for destinations:

| Keywords detected | Data pulled |
|-------------------|-------------|
| Destination name found (fuzzy) | Filter to that destination |
| "cheapest", "lowest", "best" | Sort by total rate, show top N |
| "compare", "vs", "versus" | Pull both ONE and HAPAG data |
| "hapag" | Filter to HAPAG data only |
| "one", "one line" | Filter to ONE data only |
| "all", "list", "show" | Return full route table |
| No match | Send data summary + destination list → LLM interprets |

##### Fuzzy Destination Matching (`_match_destination()`)

Users rarely type exact destination names like `"ARQUES-LA-BATAILLE, FRANCE"`. They may type `"arques la bataille"`, `"arqueslabataille"`, or even `"dormund"` (typo for Dortmund). The `_match_destination()` method handles this with a two-step strategy:

**Step 1 — Exact substring scan (catches partial/reformatted names):**

1. Build a lookup of `{city_name: full_canonical_destination}` from the database:
   - `"arques-la-bataille"` → `"ARQUES-LA-BATAILLE, FRANCE"`
   - `"dortmund"` → `"DORTMUND, NW, GERMANY"`
2. Also store "squashed" variants with spaces and hyphens removed:
   - `"arqueslabataille"` → `"ARQUES-LA-BATAILLE, FRANCE"`
3. Scan the user message for these substrings, **longest first** (to avoid false positives where a short city name appears inside a longer word).

This handles: `"le havre"` (if it's a destination), `"arques-la-bataille"`, `"arques la bataille"` (via squashed match), case-insensitive input.

**Step 2 — Fuzzy match with `difflib.get_close_matches()` (catches typos):**

1. Tokenize the message, filtering out a comprehensive stop word list:
   - Common English words: `the`, `and`, `show`, `routes`, `rates`, `how`, `much`, ...
   - Country names: `france`, `germany`, `belgium`, `poland`, ... (prevents `"france"` fuzzy-matching `"valence"`)
   - Freight terms: `freight`, `container`, `truck`, `inland`, `ocean`, ...
2. Build match candidates from remaining tokens:
   - Individual tokens: `["dormund"]`
   - Consecutive pairs with space: `["arques bataille"]`
   - Consecutive pairs squashed: `["arquesbataille"]`
3. Run `difflib.get_close_matches(candidate, city_names, cutoff=0.65)` — this uses SequenceMatcher (longest common subsequence ratio) to find the closest city name.
   - `"dormund"` → matches `"dortmund"` (ratio ~0.86)
   - `"munster"` → matches `"muenster"` (ratio ~0.86)
   - Cutoff of 0.65 catches reasonable typos while avoiding false positives.

**Fallback — LLM-assisted matching:**

If neither step finds a match, the system prompt contains the **full list of available destination names**. The LLM can then:
- Suggest the closest destination to what the user typed
- Ask the user to clarify
- Tell the user what destinations are available

This three-layer approach (exact substring → fuzzy match → LLM fallback) handles virtually all user input variations without requiring a separate NLP model.

##### Data Lookup: Contains-Fallback Matching

`get_routes()` and `get_hapag_charges()` in the data loader also use a two-step strategy:
1. Try exact match first: `df['Destination'].str.upper() == dest_upper`
2. If no rows matched, fall back to contains: `df['Destination'].str.upper().str.contains(dest_upper)`

This handles the case where fuzzy matching returns `"ARQUES-LA-BATAILLE"` (from HAPAG data) but ONE data stores it as `"ARQUES-LA-BATAILLE, FRANCE"` — the contains fallback catches it.

##### Multilingual Support

The system prompt includes: *"You can respond in the same language the user writes in (e.g., Korean, English)."* This allows users to ask questions in Korean (or other languages) and receive answers in the same language. The destination matching works language-independently since city names are always Latin characters in the database.

#### 1.3 LLM Client (`chatbot/llm_client.py`)

```python
"""
Thin wrapper around OpenAI / Gemini API.
Switchable via config or environment variable.
"""
import os

class LLMClient:
    def __init__(self, provider: str = None):
        self.provider = provider or os.getenv("LLM_PROVIDER", "openai")
        # "openai" → uses openai SDK
        # "gemini" → uses google-generativeai SDK

    def chat(self, messages: list[dict]) -> str:
        """Send messages to the chosen LLM and return the response."""
        if self.provider == "openai":
            return self._call_openai(messages)
        elif self.provider == "gemini":
            return self._call_gemini(messages)

    def _call_openai(self, messages):
        from openai import OpenAI
        client = OpenAI()  # uses OPENAI_API_KEY env var
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # cost-effective, fast
            messages=messages,
            temperature=0.3       # low temp for factual answers
        )
        return response.choices[0].message.content

    def _call_gemini(self, messages):
        import google.generativeai as genai
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        model = genai.GenerativeModel("gemini-1.5-flash")
        # Convert messages format for Gemini
        ...
```

#### 1.4 Chat Endpoint (`api_server.py` addition)

```python
@app.route('/api/chat', methods=['POST'])
def chat():
    """
    POST /api/chat
    Body: { "message": "What's the cheapest route to Valence?" }
    Response: { "reply": "The cheapest route to Valence for a 40HC..." }
    """
    user_message = request.json.get('message', '')
    context = context_builder.build_context(user_message)
    reply = llm_client.chat(context)
    return jsonify({"reply": reply})
```

### Phase 2 — Frontend Chat UI

#### 2.1 Chat Component (`freight-ui/src/components/ChatPanel.tsx`)

A collapsible chat panel in the bottom-right corner of the dashboard.

```
┌─────────────────────────────────────────────┐
│ 🔽 Freight Assistant                        │
├─────────────────────────────────────────────┤
│                                             │
│  [Bot] Hi! Ask me about freight rates,      │
│        routes, or carrier comparisons.      │
│                                             │
│  [You] What's the cheapest 40HC route       │
│        to Valence?                          │
│                                             │
│  [Bot] The cheapest 40HC route to           │
│        VALENCE, DROME, FRANCE is via        │
│        LE HAVRE by Truck at €2,480          │
│        (Ocean: €1,509 + Inland: €971).      │
│        There are 5 total routes available.  │
│                                             │
├─────────────────────────────────────────────┤
│  [Type your question...]          [Send]    │
└─────────────────────────────────────────────┘
```

#### 2.2 Chat State Management

```typescript
interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

// Simple useState-based state — no Redux needed
const [messages, setMessages] = useState<ChatMessage[]>([]);
const [input, setInput] = useState('');
const [loading, setLoading] = useState(false);
```

### Phase 3 — Conversation Memory (Optional)

For multi-turn context (so the LLM remembers earlier questions in the same session):

- Keep last N messages in the frontend state.
- Send the full conversation history to the API on each request.
- The API includes it in the LLM prompt.

No database needed — session memory lives in the browser.

---

## File Structure

```
chatbot/
  __init__.py
  data_loader.py        # Excel/JSON → DataFrames
  context_builder.py    # Intent detection + prompt assembly
  llm_client.py         # OpenAI/Gemini API wrapper

freight-ui/src/
  components/
    ChatPanel.tsx        # Chat UI component
    ChatPanel.css        # Chat styles

api_server.py            # Add POST /api/chat endpoint
.env                     # Add LLM_PROVIDER, OPENAI_API_KEY, GEMINI_API_KEY
```

---

## Environment Variables

```bash
# Add to .env
LLM_PROVIDER=openai          # or "gemini"
OPENAI_API_KEY=sk-...         # if using OpenAI
GEMINI_API_KEY=AI...          # if using Gemini
```

---

## Dependencies

```bash
# Python
pip install openai google-generativeai

# No new frontend dependencies needed — just fetch API calls
```

---

## Token & Cost Estimation

| Scenario | Est. Tokens (in+out) | GPT-4o-mini Cost | Gemini Flash Cost |
|----------|---------------------|-------------------|-------------------|
| Simple route query (1 destination) | ~1,500 | ~$0.0003 | Free tier / ~$0.00004 |
| Carrier comparison | ~3,000 | ~$0.0006 | ~$0.00008 |
| Full data summary | ~8,000 | ~$0.0016 | ~$0.0002 |

With the hybrid approach (Python lookups + LLM formatting), each query stays well under 4K tokens.

---

## Example Prompt Flow

**User asks:** *"Compare ONE and HAPAG for 40HC to Muenster"*

**Step 1 — Intent detected:** comparison, destination=MUENSTER, container=40HC

**Step 2 — Data pulled:**
```
ONE Data:
  MUENSTER, NW, GERMANY | 40 FT High Cube Dry | ROTTERDAM | Truck | Inland: €485 | Ocean: €1,509 | Total: €1,994 (Rank 1)
  MUENSTER, NW, GERMANY | 40 FT High Cube Dry | ANTWERP   | Truck | Inland: €520 | Ocean: €1,620 | Total: €2,140 (Rank 2)

HAPAG Data:
  BUSAN → MUENSTER via ROTTERDAM
  Ocean Freight: $1,800 (40HC)
  Destination Landfreight: €650 (Combined Rail)
  THC: €280, ISPS: $10
```

**Step 3 — Sent to LLM:**
```
System: You are a freight rate assistant. Answer based only on the provided data...
Data: [above data]
User: Compare ONE and HAPAG for 40HC to Muenster
```

**Step 4 — LLM responds** with a formatted comparison.

---

## Implementation Order

| Step | Task | Effort |
|------|------|--------|
| 1 | Create `chatbot/data_loader.py` — reuse loading logic from `api_server.py` | Small |
| 2 | Create `chatbot/context_builder.py` — system prompt + intent detection | Medium |
| 3 | Create `chatbot/llm_client.py` — OpenAI + Gemini dual support | Small |
| 4 | Add `POST /api/chat` endpoint to `api_server.py` | Small |
| 5 | Create `ChatPanel.tsx` frontend component | Medium |
| 6 | Wire ChatPanel into `App.tsx` | Small |
| 7 | Test end-to-end with real data | Small |
| 8 | (Optional) Add conversation memory | Small |

---

## Summary

| Question | Answer |
|----------|--------|
| Can the chatbot answer questions from our data? | **Yes** — the data is small, structured, and well-documented. An LLM with the right context will answer accurately. |
| Is "store data + md files → send to LLM" the best approach? | **Not quite.** It works for a prototype, but the hybrid approach (Python does precise lookups → LLM formats the answer) is cheaper, faster, and more accurate. |
| Do we need a vector database? | **No.** With ~300 rows of rate data, in-memory Pandas filtering is sufficient. |
| Which LLM to use? | **GPT-4o-mini** (cheapest OpenAI option with strong reasoning) or **Gemini 1.5 Flash** (generous free tier). Both work well for this use case. |
