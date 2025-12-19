from app.ga4_client import *

def execute_report(parsed_query, property_id):
    if eval(parsed_query.get("is_realtime")):
        return run_realtime_report(
            property_id=property_id,
            metrics=parsed_query["metrics"],
            dimensions=parsed_query["dimensions"],
            minute_ranges=parsed_query.get("minute_ranges", ['30'])
        )
    else:
        return run_report(
            property_id=property_id,
            metrics=parsed_query["metrics"],
            dimensions=parsed_query["dimensions"],
            start_date=parsed_query["start_date"],
            end_date=parsed_query["end_date"],
            page_path=parsed_query.get("page_path")
        )
