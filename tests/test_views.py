import json
import os
import pytest
import pandas as pd
from datetime import datetime
from unittest.mock import patch, Mock, MagicMock
import sys

from src.views import (
    filter_data_by_date,
    get_card_summary,
    get_top_transactions,
    get_stock_prices,
    create_summary_json,
    USER_SETTINGS,
    logger
    )



def test_time_response():
    pass
