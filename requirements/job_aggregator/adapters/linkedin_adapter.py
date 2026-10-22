"""
LinkedIn Job Source Adapter (Explicitly Disabled by Default).
Complies with Section 3 requirements: LinkedIn automated collection is disabled
by default until approved API credentials or authorized access methods are configured.
"""

import os
import logging
from typing import List, Dict, Any, Optional
from ..base_adapter import BaseJobSourceAdapter

logger = logging.getLogger(__name__)


class LinkedInSourceAdapter(BaseJobSourceAdapter):
    source_name = "LinkedIn"
    
    # Disabled by default in compliance with site terms and anti-bot authorization policy
    is_enabled = os.getenv("LINKEDIN_SCRAPING_ENABLED", "false").lower() == "true"
    rate_limit_delay = 2.0

    def fetch_jobs(
        self,
        limit: int = 15,
        last_hours: Optional[int] = None,
        keywords: Optional[str] = None,
        location: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        LinkedIn automated scraping is disabled by default to avoid unauthorized sessions,
        CAPTCHA bypasses, or account bans.
        """
        if not self.is_enabled:
            logger.info(
                "[LinkedIn] Automated collection is disabled by default. "
                "To enable, configure an official LinkedIn API partner client via LINKEDIN_CLIENT_ID "
                "or set LINKEDIN_SCRAPING_ENABLED=true in environment."
            )
            return []

        # Authorized API ingestion logic when enabled
        logger.warning("[LinkedIn] Official API credentials not configured; skipping retrieval.")
        return []
