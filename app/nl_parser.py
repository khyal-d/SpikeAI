from utils.packages import *
from utils.config import *
from utils.response_structure import *

# ---------------- Rule-based fallback ----------------
METRIC_MAP = {
    "page views": "screenPageViews",
    "pageviews": "screenPageViews",
    "users": "totalUsers",
    "sessions": "sessions"
}

DIMENSIONS = ["date"]

# Enabled only if OPENAI_API_KEY is present
def llm_parse(query: str):
    logger.info(f"LLM Parse Running")
    try:
        logger.info(f"Client Initialized")
        prompt = f"""
        You are a Google Analytics 4 (GA4) query parsing agent.

Your task is to convert a natural-language analytics question into a
STRUCTURED, GA4-EXECUTABLE QUERY.

You MUST follow GA4 Data API semantics.

----------------------------------
INPUT
----------------------------------
Natural language query:
{query}

----------------------------------
WHAT TO EXTRACT
----------------------------------

1. METRICS:- Metrics provide quantitative measurements of user behavior and performance, including users, sessions, engagement, conversions, revenue, and e-commerce.
- Return ONLY GA4 Data API metric names (camelCase)
- Examples:
  screenPageViews, totalUsers, activeUsers, sessions,
  engagementRate, eventCount, purchaseRevenue
- If multiple metrics are requested, include ALL of them
- DO NOT invent metrics

2. DIMENSIONS:- Dimensions represent attributes of your data, categorized into areas like user/event information, audience, campaigns, devices, Country and various advertising platform data.
- Return ONLY GA4 Data API dimension names
- Examples:
  date, pagePath, pageTitle, eventName, country, browser, deviceCategory
- Include time dimensions (date, week, month) when time-series is implied
- DO NOT invent dimensions

3. DATE RANGE
- Infer date range from the query
- Return as number of days (integer)
- If no range is specified, default to last 7 days

4. FILTERS (optional)
- Extract page path if mentioned (e.g. /pricing, /home)
- ONLY include exact page paths
- Do NOT infer query strings

5. IS_REALTIME
- Extract this flag as True/False based on context relating to realtime info
- Some example realtime indicating keywords:-right now,last 30 minutes,live users,realtime,currently active

----------------------------------
RULES (STRICT)
----------------------------------
- Output MUST be valid JSON
- DO NOT include markdown
- DO NOT include explanations
- DO NOT include extra fields
- DO NOT guess unsupported GA4 fields
- Preserve user intent as much as possible

----------------------------------
OUTPUT FORMAT (STRICT)
----------------------------------
{{
  "metrics": ["screenPageViews", "totalUsers"],
  "dimensions": ["date"],
  "days": 14,
  "page_path": "/pricing",
  "is_realtime":"False",
  "minute_ranges:["20"]
}}
If you are unsure about a metric or dimension, OMIT it rather than guessing.
        """
        logger.info(f"prompt is :- {prompt}")
        response = client.chat.completions.create(
            model=parser_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        logger.info(f"Response:{response} and model used is {parser_model}")
        return safe_json_loads(response.choices[0].message.content)
    # return response

    except Exception as e:
        # Any failure → fallback to rules
        logger.error(f"Error {e}")
        return None


# ---------------- Unified parser ----------------
def parse_query(query: str):
    # 1️⃣ Try LLM-based parsing
    llm_result = llm_parse(query)

    if llm_result:
        logger.info(f"Got query response from LLM")
        days = llm_result.get("days", 7)
        end_date = date.today()
        start_date = end_date - timedelta(days=days)

        return {
            "metrics": llm_result.get("metrics", []),
            "dimensions": llm_result.get("dimensions", []),
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "page_path": llm_result.get("page_path"),
            "dateRange": f"last {days} days",
            "minute_ranges": llm_result.get("minute_ranges", ['29']),
            "is_realtime": llm_result.get("is_realtime", "False")
        }

    # 2️⃣ Deterministic rule-based fallback
    logger.info(f"Did not receive response from LLM, running Rules Fallback")
    q = query.lower()

    metrics = [v for k, v in METRIC_MAP.items() if k in q]
    if not metrics:
        raise ValueError("No valid GA4 metrics found in query")

    days_match = re.search(r"last (\d+) days", q)
    days = int(days_match.group(1)) if days_match else 7

    end_date = date.today()
    start_date = end_date - timedelta(days=days)

    page_match = re.search(r"/(\w+)", q)
    page_path = f"/{page_match.group(1)}" if page_match else None

    return {
        "metrics": metrics,
        "dimensions": DIMENSIONS,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "page_path": page_path,
        "dateRange": f"last {days} days",
        "minute_ranges": llm_result.get("minute_ranges", ['29']),
        "is_realtime": "False"
    }



