from utils.packages import *
from utils.config import *
from app.ga4_schema_validator import *
from app.nl_parser import *
from app.ga4_client import *
from app.summarizer import *
from app.report_router import *

app = FastAPI()


class AnalyticsRequest(BaseModel):
    propertyId: str
    query: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/query")
def analytics_query(req: AnalyticsRequest):
    try:
        parsed = parse_query(req.query)
        metrics = parsed.get("metrics", [])
        dimensions = parsed.get("dimensions", [])

        if not metrics:
            raise ValueError("No valid GA4 metrics found")

        # 2. Determine report mode
        logger.info(f"Identified is_realtime is {parsed.get("is_realtime")}")
        mode = "realtime" if eval(parsed.get("is_realtime")) else "core"
        # 3. Validate + auto-repair schema
        metrics, dimensions = validate_with_auto_repair(
            client,  # LLM client is created inside repair function
            property_id=req.propertyId,
            metrics=metrics,
            dimensions=dimensions,
            mode=mode
        )
        parsed['metrics'] = metrics
        parsed['dimensions'] = dimensions
        logger.info('Validataion of metrics and dimensions is completed')
        # 4. Execute report (router decides core vs realtime)
        rows = execute_report(parsed, req.propertyId)

        # 5. Summarize results
        if eval(parsed.get("is_realtime")):
            summary = summarize(req.query, rows[0], metrics, dimensions, rows[1])
            return {
                "metadata": {
                    "propertyId": req.propertyId,
                    "mode": mode,
                    "metrics": metrics,
                    "dimensions": dimensions,
                    "duration": rows[1],
                    "page_path": parsed.get("page_path")
                },
                "data": rows,
                "summary": summary
            }
        else:
            summary = summarize(req.query, rows, metrics, dimensions, [parsed["start_date"],parsed['end_date']])

            return {
                "metadata": {
                    "propertyId": req.propertyId,
                    "mode": mode,
                    "metrics": metrics,
                    "dimensions": dimensions,
                    "duration": [parsed["start_date"],parsed['end_date']],
                    "page_path": parsed.get("page_path")
                },
                "data": rows,
                "summary": summary
            }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))