"""
Base Adapter Specification for India-Wide Multi-Source Job Ingestion.
Enforces modular contracts, rate-limiting, failure isolation, and timeout bounds.
"""

import time
import random
import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

import requests

logger = logging.getLogger(__name__)


class BaseJobSourceAdapter(ABC):
    """
    Abstract base class for all job source adapters.
    Each adapter isolates one data source (e.g. Jobdexo, Greenhouse, Ashby, PublicFeeds).
    """
    source_name: str = "BaseAdapter"
    is_enabled: bool = True
    rate_limit_delay: float = 0.5  # seconds between requests
    timeout: int = 8  # seconds
    max_retries: int = 2

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "KashiiUpdatez-Aggregator/2.0 (India Tech & Off-Campus Aggregator)",
            "Accept": "application/json, text/html, application/xml, */*",
            "Accept-Language": "en-US,en;q=0.9",
        })

    def safe_get(self, url: str, params: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None) -> Optional[requests.Response]:
        """
        Execute an HTTP GET request with timeout, rate limiting, and exponential backoff.
        """
        req_headers = {}
        if headers:
            req_headers.update(headers)

        for attempt in range(self.max_retries + 1):
            try:
                time.sleep(self.rate_limit_delay + random.uniform(0.05, 0.15))
                res = self.session.get(url, params=params, headers=req_headers, timeout=self.timeout)
                
                if res.status_code == 200:
                    return res
                elif res.status_code == 429:
                    sleep_s = (attempt + 1) * 2.0 + random.uniform(0.5, 1.5)
                    logger.warning(f"[{self.source_name}] Rate limited (HTTP 429). Backing off for {sleep_s:.1f}s.")
                    time.sleep(sleep_s)
                    continue
                elif res.status_code in [500, 502, 503, 504]:
                    time.sleep((attempt + 1) * 1.5)
                    continue
                else:
                    logger.info(f"[{self.source_name}] Request returned status {res.status_code} for {url}")
                    return res
            except Exception as e:
                if attempt == self.max_retries:
                    logger.warning(f"[{self.source_name}] Failed request to {url}: {e}")
                    return None
                time.sleep((attempt + 1) * 1.0)
        return None

    @abstractmethod
    def fetch_jobs(
        self,
        limit: int = 20,
        last_hours: Optional[int] = None,
        keywords: Optional[str] = None,
        location: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch normalized job postings matching the criteria.
        Returns a list of standardized job dictionary records.
        """
        pass
