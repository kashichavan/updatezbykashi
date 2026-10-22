"""
Multi-Source Job Aggregation Orchestrator.
Coordinates adapters, enforces failure isolation, manages deduplication,
and persists ingestion metrics and execution history.
"""

import time
import uuid
import logging
from typing import List, Dict, Any, Optional

from django.utils import timezone
from django.core.cache import cache

from requirements.models import JobPosting, JobGroup, JobIngestionRun
from .adapters import (
    JobdexoSourceAdapter,
    NaukriSourceAdapter,
    LinkedInSourceAdapter,
)
from .deduplicator import merge_or_create_job, purge_all_database_duplicates

logger = logging.getLogger(__name__)


class JobAggregationOrchestrator:
    """
    Master coordinator for India-wide job scraping and aggregation.
    Strictly prioritized across Jobdexo, Naukri, and LinkedIn for pure Indian jobs.
    """
    def __init__(self):
        # Exclusively prioritize Jobdexo, Naukri, and LinkedIn
        self.adapters = [
            JobdexoSourceAdapter(),
            NaukriSourceAdapter(),
            LinkedInSourceAdapter(),
        ]

    def get_registered_sources(self) -> List[Dict[str, Any]]:
        """Return metadata for all registered adapters."""
        return [
            {
                "name": a.source_name,
                "is_enabled": a.is_enabled,
                "rate_limit_delay": a.rate_limit_delay,
            }
            for a in self.adapters
        ]

    def run_aggregation(
        self,
        sources: Optional[List[str]] = None,
        limit_per_source: int = 10,
        last_hours: Optional[int] = None,
        keywords: Optional[str] = None,
        location: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute an ingestion cycle across specified or all active sources.
        """
        batch_id = f"batch_{int(time.time())}_{str(uuid.uuid4())[:8]}"
        overall_start = time.time()
        
        target_adapters = self.adapters
        if sources:
            source_names_lower = [s.lower() for s in sources]
            target_adapters = [a for a in self.adapters if a.source_name.lower() in source_names_lower]

        total_discovered = 0
        total_imported = 0
        total_duplicates = 0
        source_summaries = {}
        newly_created_instances = []

        for adapter in target_adapters:
            if not adapter.is_enabled:
                logger.info(f"Skipping disabled adapter: {adapter.source_name}")
                continue

            source_start = time.time()
            ingest_run = JobIngestionRun.objects.create(
                batch_id=f"{batch_id}_{adapter.source_name.lower()}",
                source_name=adapter.source_name,
                status='RUNNING'
            )

            try:
                raw_jobs = adapter.fetch_jobs(
                    limit=limit_per_source,
                    last_hours=last_hours,
                    keywords=keywords,
                    location=location
                )
                disc_count = len(raw_jobs)
                imp_count = 0
                dup_count = 0

                for job_data in raw_jobs:
                    try:
                        job_instance, created = merge_or_create_job(job_data, batch_id=batch_id)
                        if created:
                            imp_count += 1
                            newly_created_instances.append(job_instance)
                        else:
                            dup_count += 1
                    except Exception as e:
                        logger.warning(f"Error persisting job from {adapter.source_name}: {e}")

                duration = round(time.time() - source_start, 2)
                ingest_run.jobs_discovered = disc_count
                ingest_run.jobs_imported = imp_count
                ingest_run.duplicates_skipped = dup_count
                ingest_run.completed_at = timezone.now()
                ingest_run.duration_seconds = duration
                ingest_run.status = 'SUCCESS' if imp_count > 0 or disc_count == 0 else 'PARTIAL'
                ingest_run.save()

                total_discovered += disc_count
                total_imported += imp_count
                total_duplicates += dup_count

                source_summaries[adapter.source_name] = {
                    'status': ingest_run.status,
                    'discovered': disc_count,
                    'imported': imp_count,
                    'duplicates': dup_count,
                    'duration_s': duration,
                }

            except Exception as e:
                logger.exception(f"Failure running adapter {adapter.source_name}: {e}")
                ingest_run.status = 'FAILED'
                ingest_run.error_message = str(e)
                ingest_run.completed_at = timezone.now()
                ingest_run.duration_seconds = round(time.time() - source_start, 2)
                ingest_run.save()

                source_summaries[adapter.source_name] = {
                    'status': 'FAILED',
                    'error': str(e)
                }

        # Run cross-source database duplicate sweep and purge
        purge_stats = {}
        try:
            purge_stats = purge_all_database_duplicates(dry_run=False)
            logger.info(f"Ingestion auto-purge complete: {purge_stats.get('duplicates_deleted', 0)} duplicates removed.")
        except Exception as e:
            logger.warning(f"Notice running auto-deduplication purge: {e}")

        # If fresh jobs were imported, bundle them into a JobGroup for easy browsing
        # Filter newly_created_instances to only those that survived deduplication
        surviving_instances = [j for j in newly_created_instances if JobPosting.objects.filter(id=j.id).exists()]
        if surviving_instances:
            try:
                now_local = timezone.localtime(timezone.now())
                group_name = now_local.strftime("⚡ Fresh India Tech & Off-Campus Drives — %d %b %Y")
                base_slug = f"all-india-drives-{now_local.strftime('%Y%m%d%H%M')}"
                
                group = JobGroup.objects.create(
                    name=group_name,
                    slug=base_slug,
                    banner_tag="⚡ ALL-INDIA VERIFIED JOBS",
                    description=f"Curated feed of {len(surviving_instances)} fresh opportunities across tech, data, cloud, and core industries.",
                    posted_date=now_local.date(),
                    deadline=now_local + timezone.timedelta(days=7),
                    is_active=True
                )
                group.jobs.set(surviving_instances)
            except Exception as e:
                logger.warning(f"Notice creating JobGroup: {e}")

        # Clear cache so fresh listings appear immediately
        cache.clear()

        return {
            "success": True,
            "batch_id": batch_id,
            "total_discovered": total_discovered,
            "total_imported": total_imported,
            "total_duplicates": total_duplicates,
            "duplicates_purged": purge_stats.get("duplicates_deleted", 0),
            "duration_seconds": round(time.time() - overall_start, 2),
            "sources": source_summaries,
            "imported_jobs_count": len(surviving_instances),
        }


# Global singleton instance
orchestrator = JobAggregationOrchestrator()
