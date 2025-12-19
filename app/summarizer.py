from utils.packages import *
from utils.response_structure import *
from utils.config import *

def summarize(query, rows, metrics, dimensions, date_range):
    logger.info(f"LLM Parse Running")
    try:
        api_key = os.getenv("LITELLM_KEY")

        client = OpenAI(api_key=api_key,
                        base_url="http://3.110.18.218")

        logger.info(f"Client Initialized")
        prompt = f"""
        You are a senior data analyst specializing in Google Analytics 4 (GA4).

Your task is to analyze GA4 report results and produce a concise, business-ready natural language summary.

You will be given:
- The original user query (natural language) : {query}
- The GA4 report data (time-series and/or aggregate values): {rows}
- The metrics, dimensions, and date range used: {[metrics, dimensions, date_range]}

Your responsibilities:
1. Identify overall trends (increasing, decreasing, flat)
2. Highlight significant spikes, drops, or anomalies
3. Compare start vs end of period when time-series data exists
4. Call out notable patterns related to dimensions (e.g. page path, country, device)
5. Keep explanations factual and grounded strictly in the provided data
6. Do NOT speculate beyond the data

Constraints:
- Do NOT mention internal implementation details
- Do NOT restate raw numbers unless necessary
- Use clear, non-technical language suitable for business stakeholders
- If data is insufficient to infer trends, explicitly say so

Return STRICT JSON ONLY in the following format:

{
  {"summary": "High-level explanation of overall performance and trends",
  "trends": [
    {
      "metric": "<metric_name>",
      "direction": "up | down | flat | mixed",
      "description": "Short explanation of how this metric changed over time"
    }
  ],
  "anomalies": [
    {
      "metric": "<metric_name>",
      "date": "<YYYY-MM-DD or range>",
      "description": "What was unusual and why it stands out"
    }
  ],
  "dimension_insights": [
    {
      "dimension": "<dimension_name>",
      "value": "<dimension_value>",
      "description": "Notable observation tied to this dimension"
    }
  ]}
}

        """
        logger.info(f"prompt is :- {prompt}")
        response = client.chat.completions.create(
            model=summarizer_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        logger.info(f"Response:{response} and model used is {summarizer_model}")
        return safe_json_loads(response.choices[0].message.content)
    # return response

    except Exception as e:
        # Any failure → fallback to rules
        logger.error(f"Error {e}")
        return None