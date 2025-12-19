from utils.packages import *
from utils.config import *
from utils.response_structure import *

"""
GA4 Validator with Metadata API + Rule-based checks + LLM Auto-repair
NO caching (no lru_cache)
"""


# -----------------------------
# Constants
# -----------------------------

SCOPES = ["https://www.googleapis.com/auth/analytics.readonly"]

TIME_DIMENSIONS = {
    "date", "dateHour", "dateHourMinute", "week", "month", "year"
}

EVENT_DIMENSIONS = {
    "eventName", "eventCategory", "eventLabel"
}

ITEM_DIMENSIONS = {
    "itemName", "itemBrand", "itemCategory","browser","city","cohort"
}

SESSION_METRICS = {
    "sessions",
    "averageSessionDuration",
    "engagementRate",
    "sessionsPerUser"
}

USER_METRICS = {
    "totalUsers",
    "activeUsers",
    "newUsers"
}

ADS_METRICS = {
    "advertiserAdClicks",
    "advertiserAdCost",
    "advertiserAdImpressions"
}

METRIC_ALIASES = {
    # ecommerce
    "purchases": "ecommercePurchases",
    "purchase": "ecommercePurchases",

    # events
    "conversions": "keyEvents",
    "conversion": "keyEvents",

    # pages
    "pageviews": "screenPageViews",
    "page views": "screenPageViews",
    "page_views": "screenPageViews",

    # sessions
    "events per session": "eventsPerSession",
    "eventcountpersession": "eventsPerSession",

    # revenue
    "revenue": "totalRevenue"
}

DIMENSION_ALIASES = {
    # pages
    "page": "pagePath",
    "page path": "pagePath",
    "page url": "pagePathPlusQueryString",

    # geo
    "country name": "country",
    "location": "country",
    "city name": "city",

    # device
    "device": "deviceCategory",
    "os": "operatingSystem",
    "operating system": "operatingSystem",

    # traffic
    "source": "source",
    "source / medium": "sourceMedium",
    "traffic source": "sourceMedium",
    "campaign": "campaignName",

    # time
    "day": "date",
    "daily": "date",
    "week": "week",
    "month": "month"
}

REALTIME_ALLOWED_METRICS = {
    "eventCount",
    "activeUsers",
    "screenPageViews",
    "keyEvents"
}

REALTIME_ALLOWED_DIMENSIONS = {
    "eventName",
    "deviceCategory",
    "platform",
    "appVersion",
    "audienceId",
    "audienceName",
    "audienceResourceName",
    "city",
    "cityId",
    "country",
    "countryId",
    "deviceCategory",
    "minutesAgo",
    "streamId",
    "streamName",
    "unifiedScreenName"
}

def normalize_metrics(metrics: list[str]) -> list[str]:
    normalized = []

    for m in metrics:
        key = m.lower().replace(" ", "")
        canonical = METRIC_ALIASES.get(key) or METRIC_ALIASES.get(m.lower())
        normalized.append(canonical if canonical else m)
        
    return normalized

def normalize_dimensions(dimensions: list[str]) -> list[str]:
    normalized = []
    for d in dimensions:
        key = d.lower().strip()
        normalized.append(DIMENSION_ALIASES.get(key, d))
    return normalized

# -----------------------------
# Errors
# -----------------------------

class GA4BaseValidationError(Exception):
    def __init__(self,reason, metrics=None, dimensions=None, extra=None):
        super().__init__(reason)
        self.reason = reason
        self.metrics = metrics or []
        self.dimensions = dimensions or []
        self.extra = extra or {}

class GA4ValidationError(GA4BaseValidationError):
    pass

class GA4RealtimeValidationError(GA4BaseValidationError):
    pass


# -----------------------------
# Metadata Loader (NO CACHE)
# -----------------------------

def load_metadata(property_id: str):
    credentials = service_account.Credentials.from_service_account_file(
        "credentials.json",
        scopes=["https://www.googleapis.com/auth/analytics.readonly"]
    )

    client = BetaAnalyticsDataClient(credentials=credentials)

    metadata = client.get_metadata(
        name=f"properties/{property_id}/metadata"
    )

    metric_types = {
        m.api_name: m.type_
        for m in metadata.metrics
    }

    dimension_set = {d.api_name for d in metadata.dimensions}

    return metric_types, dimension_set

# -----------------------------
# Core Validation
# -----------------------------

def validate_ga4_query(property_id, metrics, dimensions):
    metric_types, dimension_set = load_metadata(property_id)

    # --- existence ---
    for m in metrics:
        if m not in metric_types:
            raise GA4ValidationError(f"Invalid GA4 metric: {m}", metrics, dimensions)

    for d in dimensions:
        if d not in dimension_set:
            raise GA4ValidationError(f"Invalid GA4 dimension: {d}", metrics, dimensions)

    # --- scope rules ---
    for m in metrics:
        metric_type = metric_types[m]

        if metric_type == "SESSION" and EVENT_DIMENSIONS & set(dimensions):
            raise GA4ValidationError(
                "Session metrics cannot be broken down by event dimensions",
                metrics,
                dimensions
            )

        if metric_type == "USER" and ITEM_DIMENSIONS & set(dimensions):
            raise GA4ValidationError(
                "User metrics cannot be broken down by item dimensions",
                metrics,
                dimensions
            )

    return True


def validate_realtime_query(metrics, dimensions):
    for m in metrics:
        if m not in REALTIME_ALLOWED_METRICS:
            raise GA4RealtimeValidationError(
                f"Metric '{m}' is not supported in GA4 Realtime reports",
                metrics, dimensions
            )

    for d in dimensions:
        if d not in REALTIME_ALLOWED_DIMENSIONS:
            raise GA4RealtimeValidationError(
                f"Dimension '{d}' is not supported in GA4 Realtime reports",
                metrics, dimensions
            )
    return True

# -----------------------------
# LLM Auto-repair
# -----------------------------

def build_repair_prompt(error, metric_map, dimension_set,mode="Core"):
    logger.info(f"The Repair Prompt is building")
    return f"""
You are a Google Analytics 4 query repair agent repairing {mode.upper()} query.

The GA4 query below is INVALID.

Reason:
{error.reason}

Metrics:
{error.metrics}

Dimensions:
{error.dimensions}

VALID METRICS:
{list(metric_map)}

VALID DIMENSIONS:
{list(dimension_set)}

Invalid error:
{str(error)}

Rules:
- ONLY return fields supported by GA4 {mode.upper()} reports
- Use ONLY valid metrics and dimensions
- Ensure compatibility
- Preserve original intent
- Prefer removing invalid dimensions over changing metrics
IMPORTANT:
GA4 metric names MUST match the GA4 Data API exactly.

Examples:
- Use "ecommercePurchases" NOT "purchases"
- Use "eventsPerSession" NOT "eventCountPerSession"
- Use "screenPageViews" NOT "pageViews"
- Use "keyEvents" NOT "conversions"

If unsure, choose the closest valid GA4 metric.
Return STRICT JSON ONLY.

Format:
{{
  "metrics": [...],
  "dimensions": [...]
}}
"""

def llm_repair_query(
    client,
    property_id: str,
    error: GA4BaseValidationError,
    mode:"Core"
):
    if mode.lower()=="core":
        metric_type, dimension_set = load_metadata(property_id)
        metric_map = metric_type.keys()
    else:
        metric_map, dimension_set = REALTIME_ALLOWED_METRICS,REALTIME_ALLOWED_DIMENSIONS

    prompt = build_repair_prompt(error, metric_map, dimension_set,mode)
    logger.info(f"The Repair prompt is generated, {prompt}")
    response = client.chat.completions.create(
        model=parser_model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )

    logger.info(f"Model used is {parser_model} with response is {response}")
    return safe_json_loads(response.choices[0].message.content)


# -----------------------------
# Validation + Repair Loop
# -----------------------------

def validate_with_auto_repair(
    client,
    property_id: str,
    metrics: list[str],
    dimensions: list[str],
    mode: str = "core",
    retries: int = 1
):
    try:
        if mode == "realtime":
            logger.info(f"Identified Mode is {mode}")
            validate_realtime_query(metrics, dimensions)
        else:
            metrics = normalize_metrics(metrics)
            dimensions = normalize_dimensions(dimensions)
            validate_ga4_query(property_id, metrics, dimensions)

        return metrics, dimensions

    except GA4BaseValidationError as e:
        logger.info(f"GA4BaseValidationError is raised")
        if retries <= 0:
            raise

        repaired = llm_repair_query(
            client=client,
            property_id=property_id,
            error=e,
            mode=mode
        )

        return validate_with_auto_repair(
            client,
            property_id,
            repaired["metrics"],
            repaired["dimensions"],
            mode=mode,
            retries=retries - 1
        )



