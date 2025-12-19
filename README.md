# GA4 Analytics Agent

A **production-ready Analytics Agent** that converts natural-language questions into **live Google Analytics 4 (GA4) reports** using the GA4 Data API and Realtime Reporting API.

The system combines **LLM-based reasoning**, **rule-based fallbacks**, and **strict GA4 schema validation** to safely generate accurate analytics insights with zero manual intervention.

---

## Key Capabilities

### Core Analytics (Historical Data)
- Natural-language → GA4 query conversion
- Automatic inference of:
  - Metrics
  - Dimensions
  - Date ranges
  - Page paths & filters
- Time-series and aggregate reporting
- Server-side validation using GA4 Metadata API
- LLM-based auto-repair for invalid metric/dimension combinations
- Clear, human-readable summaries

### Realtime Analytics
- Live data from the **last 30–60 minutes**
- Automatic detection of `realtime` intent
- Uses `runRealtimeReport`
- Realtime-specific validation rules
- Supports multiple minute ranges

### Production-Grade Design
- Binds **only to port 8080**
- Fully automated startup via `deploy.sh`
- No manual steps during evaluation
- Credentials loaded at runtime
- Clean separation of concerns
- Extendable to multiple agents (SEO Agent, etc.)

---
### Sequential Data Flow Diagram
<img width="9420" height="5150" alt="SequenceFlow Diagram" src="https://github.com/user-attachments/assets/1ee02a09-5590-4add-991f-34a971048edb" />

## Architecture Overview
<img width="3322" height="4525" alt="GA4 Intent-Driven Report-2025-12-19-060625" src="https://github.com/user-attachments/assets/33d07c99-e769-465c-af8d-554fe2256e52" />

**Request Flow**
1. Natural language query received via API
2. LLM-based parsing with rule fallback
3. GA4 schema validation (Metadata API)
4. Auto-repair (if needed)
5. Core or Realtime GA4 execution
6. Optional LLM-based summarization
7. Structured JSON response

---

## 📁 Repository Structure

.
├── app
│   ├── main.py
│   ├── nl_parser.py
│   ├── ga4_client.py
│   ├── ga4_schema_validator.py
│   ├── summarizer.py
│   └── validator.py
├── credentials.json
├── requirements.txt
├── deploy.sh
└── README.md



---

## Credentials

- The application expects a valid **GA4 service account credentials file**
- File must be named **`credentials.json`**
- Must exist at the **repository root**
- Used at runtime for GA4 authentication
- Evaluators will replace this file automatically

---

## Deployment (One Command)

```bash
bash deploy.sh

