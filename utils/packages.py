from datetime import date, timedelta
import re
import json
import re
import os
from loguru import logger
from dotenv import load_dotenv

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from openai import OpenAI

from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    RunRealtimeReportRequest,
    MinuteRange
)
from google.analytics.data_v1beta.types import DateRange, Dimension, Metric, RunReportRequest, FilterExpression, Filter
from google.oauth2 import service_account
from functools import lru_cache
from typing import List, Set