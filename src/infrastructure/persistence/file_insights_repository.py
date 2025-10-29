"""File-based implementation of InsightsRepository."""

import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from src.domain.performance.entities.performance_insight import PerformanceInsight
from src.domain.performance.repositories.insights_repository import InsightsRepository
from src.domain.performance.value_objects.severity import Severity

logger = logging.getLogger(__name__)


class FileInsightsRepository(InsightsRepository):
    """File-based repository for performance insights.

    Reads insights from validation_*.txt files in the reports directory.
    This is the adapter that implements the port interface.
    """

    def __init__(self, reports_dir: Path):
        """
        Initialize repository with reports directory.

        Args:
            reports_dir: Directory containing validation report files
        """
        self.reports_dir = Path(reports_dir)
        self._cache: Optional[List[PerformanceInsight]] = None
        self._cache_time: Optional[datetime] = None
        self._cache_ttl_seconds = 30  # Cache for 30 seconds

    def _parse_validation_file(self, file_path: Path) -> List[PerformanceInsight]:
        """
        Parse a validation file and extract insights.

        Args:
            file_path: Path to validation file

        Returns:
            List of PerformanceInsight entities
        """
        insights = []

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Look for the insights section
            if "💡 INSIGHTS GENERATED:" not in content:
                logger.debug(f"No insights section found in {file_path}")
                return []

            lines = content.split("\n")
            in_insights_section = False
            current_data = {}

            for line in lines:
                if "💡 INSIGHTS GENERATED:" in line:
                    in_insights_section = True
                    continue

                if not in_insights_section:
                    continue

                # Stop at section separator
                if line.startswith("=") and len(line) > 50:
                    if current_data:
                        insight = self._create_insight_from_data(current_data)
                        if insight:
                            insights.append(insight)
                    break

                # Start of new insight
                if line.startswith("  [") and "] " in line:
                    # Save previous insight
                    if current_data:
                        insight = self._create_insight_from_data(current_data)
                        if insight:
                            insights.append(insight)

                    # Start new insight
                    current_data = {}
                    title_part = line.split("] ", 1)[1] if "] " in line else ""
                    current_data["title"] = title_part.strip()

                elif "Component:" in line:
                    current_data["component"] = line.split("Component:", 1)[1].strip()

                elif "Severity:" in line:
                    severity_str = line.split("Severity:", 1)[1].strip().upper()
                    current_data["severity"] = severity_str

                elif "Methodology:" in line:
                    current_data["methodology"] = line.split("Methodology:", 1)[1].strip()

                elif "Evidence:" in line:
                    evidence_str = line.split("Evidence:", 1)[1].strip()
                    # Parse key=value pairs
                    evidence = []
                    for pair in evidence_str.split(", "):
                        if "=" in pair:
                            evidence.append(pair)
                    current_data["evidence"] = evidence

                elif line.strip() and not line.startswith("="):
                    # Additional description
                    if "description" not in current_data:
                        current_data["description"] = line.strip()
                    else:
                        current_data["description"] += " " + line.strip()

            # Add last insight if exists
            if current_data:
                insight = self._create_insight_from_data(current_data)
                if insight:
                    insights.append(insight)

        except Exception as e:
            logger.error(f"Error parsing validation file {file_path}: {e}")
            return []

        logger.debug(f"Parsed {len(insights)} insights from {file_path}")
        return insights

    def _create_insight_from_data(self, data: dict) -> Optional[PerformanceInsight]:
        """
        Create a PerformanceInsight entity from parsed data.

        Args:
            data: Dictionary with parsed insight data

        Returns:
            PerformanceInsight entity or None if data is incomplete
        """
        try:
            # Required fields
            title = data.get("title", "").strip()
            if not title:
                return None

            # Parse severity
            severity_str = data.get("severity", "MEDIUM").upper()
            try:
                severity = Severity[severity_str]
            except KeyError:
                logger.warning(f"Unknown severity '{severity_str}', defaulting to MEDIUM")
                severity = Severity.MEDIUM

            # Build description
            description = data.get("description", title)
            methodology = data.get("methodology", "")
            if methodology:
                description = f"{description} (Methodology: {methodology})"

            # Build recommendations from evidence
            recommendations = []
            evidence_list = data.get("evidence", [])
            if evidence_list:
                recommendations.append(f"Evidence: {', '.join(evidence_list)}")

            # Create entity
            insight = PerformanceInsight(
                title=title,
                description=description,
                component=data.get("component", "System"),
                severity=severity,
                timestamp=datetime.now(),
                recommendations=recommendations,
                metrics=evidence_list,
                root_cause=data.get("methodology"),
            )

            return insight

        except Exception as e:
            logger.error(f"Error creating insight from data: {e}")
            return None

    def _load_all_insights(self) -> List[PerformanceInsight]:
        """
        Load all insights from validation files.

        Returns:
            List of all insights from the most recent file
        """
        # Find the most recent validation file
        validation_files = sorted(
            self.reports_dir.glob("validation_*.txt"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )

        if not validation_files:
            logger.warning(f"No validation files found in {self.reports_dir}")
            return []

        latest_file = validation_files[0]
        logger.info(f"Loading insights from {latest_file.name}")

        insights = self._parse_validation_file(latest_file)
        return insights

    def _get_cached_insights(self) -> List[PerformanceInsight]:
        """
        Get insights from cache or load from file.

        Returns:
            List of cached or freshly loaded insights
        """
        now = datetime.now()

        # Check cache validity
        if (
            self._cache is not None
            and self._cache_time is not None
            and (now - self._cache_time).total_seconds() < self._cache_ttl_seconds
        ):
            logger.debug("Returning cached insights")
            return self._cache

        # Load fresh data
        logger.debug("Cache expired or empty, loading from file")
        self._cache = self._load_all_insights()
        self._cache_time = now

        return self._cache

    # Implement abstract methods

    async def get_all(self, limit: Optional[int] = None) -> List[PerformanceInsight]:
        """Get all insights, optionally limited."""
        insights = self._get_cached_insights()

        # Sort by timestamp (newest first)
        insights.sort(key=lambda x: x.timestamp, reverse=True)

        if limit:
            return insights[:limit]
        return insights

    async def get_by_severity(
        self, severity: Severity, limit: Optional[int] = None
    ) -> List[PerformanceInsight]:
        """Get insights filtered by severity."""
        all_insights = await self.get_all()
        filtered = [i for i in all_insights if i.severity == severity]

        if limit:
            return filtered[:limit]
        return filtered

    async def get_by_component(
        self, component: str, limit: Optional[int] = None
    ) -> List[PerformanceInsight]:
        """Get insights for a specific component."""
        all_insights = await self.get_all()
        # Case-insensitive comparison
        component_lower = component.lower()
        filtered = [i for i in all_insights if component_lower in i.component.lower()]

        if limit:
            return filtered[:limit]
        return filtered

    async def get_critical_insights(self) -> List[PerformanceInsight]:
        """Get only critical insights."""
        return await self.get_by_severity(Severity.CRITICAL)

    async def get_by_time_range(
        self, start_time: datetime, end_time: datetime
    ) -> List[PerformanceInsight]:
        """Get insights within a time range."""
        all_insights = await self.get_all()
        filtered = [
            i
            for i in all_insights
            if start_time <= i.timestamp <= end_time
        ]
        return filtered

    async def count_by_severity(self) -> dict[Severity, int]:
        """Count insights grouped by severity."""
        all_insights = await self.get_all()
        counts = {severity: 0 for severity in Severity}

        for insight in all_insights:
            counts[insight.severity] += 1

        return counts

    async def save(self, insight: PerformanceInsight) -> None:
        """Save a performance insight (not implemented for file-based)."""
        raise NotImplementedError(
            "FileInsightsRepository is read-only. Use a different implementation for writes."
        )

    async def save_many(self, insights: List[PerformanceInsight]) -> None:
        """Save multiple insights (not implemented for file-based)."""
        raise NotImplementedError(
            "FileInsightsRepository is read-only. Use a different implementation for writes."
        )
