# AI Medical Monitor Service — Feature Deep Dive & Interview Script

> **Purpose of this document**: A comprehensive explanation of the AI Monitor feature — what it does, how it works, and how to present it in technical interviews.

---

## 1. What This Feature Does

The AI Medical Monitor is an **LLM-powered clinical trial data quality reviewer** integrated into the **Quality Service** (`quality-service/src/main.py`, port 8004). It:

1. **Fetches subject data** from the EDC Service — metadata, demographics, vitals, lab results, and existing queries.
2. **Assembles a rich clinical prompt** with all available data for the subject.
3. **Sends the prompt to an LLM** (OpenAI GPT-4o-mini or Anthropic Claude 3.5 Sonnet) for clinical review.
4. **Parses the LLM's free-text response** into structured findings with severity classification.
5. **Optionally posts findings as queries** back to the EDC for data managers to review.

### How the Monitor Makes Decisions

The decision engine is the **LLM itself**. The service constructs a structured prompt containing:

| Data Domain | EDC Endpoint | What It Provides |
|---|---|---|
| Subject metadata | `GET /subjects/{id}` | Site, status, treatment arm, enrollment date |
| Demographics | `GET /demographics/{id}` | Age, gender, BMI, smoking status, race |
| Vitals (all visits) | `GET /vitals/all` (filtered) | SBP, DBP, heart rate, temperature per visit |
| Lab results | `GET /labs/{id}` | Creatinine, ALT, AST, glucose, etc. |
| Existing queries | `GET /queries?subject_id=X` | Prior findings already raised |

The LLM uses its pre-trained medical knowledge to perform **cross-domain, multi-visit reasoning** — for example:
- *"72-year-old female with BMI 35.2, SBP trending from 130→162 across visits, creatinine rising from 0.9→1.9 — suggestive of renal hypertension"*
- *"ALT/AST doubling over 4 visits in a patient on statins — possible hepatotoxicity signal"*

This cross-field reasoning is what justifies using an LLM over simple rule-based checks — rules handle single-field range checks, but LLMs can connect patterns across demographics, vitals, and labs simultaneously.

### Severity Classification

Severity is determined by a **hybrid approach**:
1. The LLM naturally indicates severity in its output.
2. `parse_llm_response()` classifies via **keyword matching**:
   - `CRITICAL` / `SEVERE` → `"critical"`
   - `ERROR` / `INVALID` → `"error"`
   - `WARNING` / `CONCERN` → `"warning"`
   - `INFO` / `NOTE` → `"info"`

### Demo/Fallback Mode

When no API key is configured, the service returns **hardcoded mock findings** for demonstration purposes.

---

## 2. Architecture

```
┌──────────────┐     HTTP POST        ┌──────────────────────────┐
│   Frontend   │ ───────────────────→ │  Quality Service (8004)  │
│  AI Monitor  │                      │  /ai-monitor/review/*    │
│   Screen     │                      │                          │
└──────────────┘                      │  ┌──────────────────┐   │
                                      │  │ fetch_subject_    │   │
                                      │  │ context()         │   │
                                      │  │ → Demographics    │──→ EDC (8001)
                                      │  │ → Vitals          │   │
                                      │  │ → Labs            │   │
                                      │  │ → Existing Queries│   │
                                      │  └────────┬─────────┘   │
                                      │           ▼             │
                                      │  build_enriched_prompt()│
                                      │           ▼             │
                                      │  ┌─────────────────┐   │
                                      │  │ OpenAI / Claude  │   │
                                      │  │ (LLM API call)   │   │
                                      │  └────────┬────────┘   │
                                      │           ▼             │
                                      │  parse_llm_response()  │
                                      │           ▼             │
                                      │  (Optional) POST       │──→ EDC /queries
                                      │  findings as queries    │
                                      └──────────────────────────┘
```

### API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/ai-monitor/review/subject` | POST | Review single subject with full clinical context |
| `/ai-monitor/review/study` | POST | Review all subjects in a study (up to `max_subjects`) |
| `/ai-monitor/review/study/post-queries` | POST | Review + auto-post findings as queries to EDC |

### Key Design Decisions

| Decision | Rationale |
|---|---|
| **Merged into quality-service** | Shares the same Docker container and DB; avoids running a separate service |
| **LLM-based (not statistical)** | Cross-domain reasoning across vitals + labs + demographics is where LLMs outperform rules; rules would handle single-field range checks but not multi-field pattern detection |
| **Synchronous REST** | On-demand quality review tool, not a real-time stream processor — request-response is appropriate |
| **Best-effort data enrichment** | If any EDC endpoint is unavailable, the review still works with whatever data is available |
| **No new dependencies** | Uses `httpx` (already in requirements) for EDC calls and LLM API calls |

---

## 3. How I Developed This Feature

### Development Steps

1. **Started with a standalone microservice** (`ai-monitor-service/`) to prototype the LLM integration.
2. **Defined Pydantic models** (`SubjectReviewRequest`, `AIFinding`, `ReviewResponse`) for type-safe API contracts.
3. **Implemented `call_llm()`** supporting two LLM providers (OpenAI + Anthropic) with mock fallback.
4. **Built `parse_llm_response()`** — a keyword-matching parser that extracts severity from LLM output.
5. **Merged into quality-service** since both services deal with data quality — reduced operational overhead.
6. **Added `fetch_subject_context()`** — a best-effort helper that pulls demographics, vitals, labs, and existing queries from EDC in parallel, catching all errors gracefully.
7. **Created `build_enriched_prompt()`** — constructs a structured clinical review prompt from all available data, with a `brief` mode for batch reviews to stay within token limits.
8. **Connected to frontend** — React component (`AIMedicalMonitor.tsx`) lets users select a study, run the review, and see findings in a severity-colored table.

### Technologies Used

| Component | Technology | Why |
|---|---|---|
| Web framework | FastAPI | Async support, auto OpenAPI docs, Pydantic integration |
| HTTP client | httpx | Async HTTP for EDC + LLM API calls |
| Data validation | Pydantic v2 | Type-safe request/response models |
| LLM integration | Direct HTTP (no SDK) | Minimal dependency footprint |
| Frontend | React + TypeScript | Shared with the rest of the platform |

---

## 4. Interview Script

### The Pitch

> "I built an AI-powered medical monitor as part of a clinical trial data platform. In real trials, a medical monitor — typically a physician — reviews patient data for safety signals. My service automates the pre-screening step using LLMs.
>
> When triggered, it fetches a subject's full clinical profile from our EDC — demographics, vitals across visits, lab results, and any existing queries. It assembles this into a structured prompt and sends it to GPT-4o-mini or Claude. The LLM performs cross-domain clinical reasoning — for instance, correlating rising creatinine with increasing blood pressure to flag possible renal hypertension. Findings are parsed into structured objects with severity levels and posted back to the EDC as queries."

### "Why LLM instead of rules or Isolation Forests?"

> "For single-field range checks, rules would suffice — 'flag if SBP > 180.' But the value of this monitor is cross-domain reasoning: connecting a patient's age, BMI, smoking status, vital sign trends, and lab values to identify patterns that would require hundreds of combinatorial rules. An LLM handles that contextual reasoning naturally. If I were building for production, I'd use a hybrid — statistical baselines for numeric ranges plus an LLM for contextual interpretation."

### "What about latency?"

> "It runs synchronously — each subject review takes 1-3 seconds for the LLM call, plus sub-second for the EDC data fetches. For a study review of 10 subjects, that's 10-30 seconds total. This is fine for an on-demand quality review tool, but would be a bottleneck for real-time monitoring. If needed, I'd decouple it with a task queue."

### "How do you handle LLM hallucinations?"

> "The findings are advisory, not autonomous. They're posted as queries for human review. I also use low temperature (0.3) and structured prompts to constrain output. The best-effort data enrichment means the LLM always has real clinical data to reason about, reducing hallucination risk."

### "How would you improve it?"

> "Three things: (1) Use LLM structured output / function calling to get JSON findings directly instead of keyword-parsing. (2) Add statistical baselines as a first pass — flag obvious outliers with Z-scores, then send borderline cases to the LLM. (3) Use async processing with a task queue for study-level reviews."

---

## 5. Summary

| Aspect | Detail |
|---|---|
| **What it is** | LLM-powered clinical data quality reviewer |
| **Where it lives** | `quality-service/src/main.py` (lines 818+), port 8004 |
| **Data it reviews** | Demographics + vitals + labs + existing queries + subject metadata |
| **How it decides** | Delegates cross-domain reasoning to GPT-4o-mini or Claude 3.5 Sonnet |
| **Processing model** | Synchronous HTTP (on-demand, not streaming) |
| **Integration** | Reads from and writes to EDC Service via REST |
| **Error handling** | Best-effort data enrichment — graceful degradation if EDC data is unavailable |
| **Frontend** | `AIMedicalMonitor.tsx` — select study, run review, see findings table |
| **Fallback** | Mock findings when no API key is configured |
