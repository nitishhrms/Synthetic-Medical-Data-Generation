"""
Compliance/RBQM Watcher

Automated monitoring of regulatory sources for guidance updates.
Scans FDA, ICH, CDISC, and TransCelerate for changes that may
impact edit check rules and RBQM thresholds.
"""

import logging
import yaml
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
from urllib.parse import urlparse

from linkup_utils import get_linkup_client, extract_date_from_source

logger = logging.getLogger(__name__)


# ============================================================================
# Regulatory Source Configurations
# ============================================================================

REGULATORY_SOURCES = {
    "FDA": {
        "domains": ["fda.gov"],
        "keywords": [
            "clinical trial",
            "data quality",
            "RBQM",
            "ICH E6",
            "risk-based monitoring",
            "data integrity"
        ],
        "check_frequency_hours": 24
    },
    "ICH": {
        "domains": ["ich.org"],
        "keywords": [
            "E6(R3)",
            "E6(R2)",
            "guideline",
            "clinical trial",
            "quality management",
            "data integrity"
        ],
        "check_frequency_hours": 168  # Weekly
    },
    "CDISC": {
        "domains": ["cdisc.org"],
        "keywords": [
            "SDTM",
            "controlled terminology",
            "standard",
            "CDASH",
            "data collection"
        ],
        "check_frequency_hours": 168
    },
    "TransCelerate": {
        "domains": ["transcelerate.org"],
        "keywords": [
            "RBQM",
            "quality tolerance limits",
            "KRI",
            "risk-based quality management",
            "central monitoring"
        ],
        "check_frequency_hours": 168
    },
    "EMA": {
        "domains": ["ema.europa.eu"],
        "keywords": [
            "clinical trial",
            "data quality",
            "GCP inspection",
            "quality management"
        ],
        "check_frequency_hours": 168
    }
}


# ============================================================================
# Pydantic Models
# ============================================================================

class RegulatoryUpdate(BaseModel):
    """Model for a detected regulatory update"""
    update_id: str
    source_name: str
    title: str
    url: str
    publication_date: Optional[str] = None
    snippet: str
    impact_assessment: str  # HIGH, MEDIUM, LOW
    keywords_matched: List[str] = []
    detected_at: str


class ComplianceScanResponse(BaseModel):
    """Response model for compliance scan"""
    total_updates: int
    high_impact_count: int
    medium_impact_count: int
    low_impact_count: int
    sources_scanned: int
    updates: List[RegulatoryUpdate]
    scan_timestamp: str
    next_scan_scheduled: Optional[str] = None


class ImpactAssessment(BaseModel):
    """Impact assessment for a regulatory update"""
    update_id: str
    overall_impact: str
    affected_rules_count: int
    affected_rules: List[Dict[str, Any]]
    recommendations: List[str]
    requires_action: bool
    assessment_timestamp: str


# ============================================================================
# Core Scanning Functions
# ============================================================================

async def deep_search_regulatory_updates(
    source_name: str,
    config: Dict[str, Any],
    lookback_days: int = 30
) -> List[Dict[str, Any]]:
    """
    Deep search for new/updated regulatory guidance

    Args:
        source_name: Name of regulatory source (e.g., "FDA")
        config: Configuration dict with domains and keywords
        lookback_days: How many days back to search

    Returns:
        List of detected updates
    """
    updates = []

    try:
        # Build search query with time filter
        domains = config["domains"]
        keywords = config["keywords"]

        # Create query with site filter
        for domain in domains:
            for keyword in keywords[:3]:  # Limit to top 3 keywords per domain
                query = f"{keyword} site:{domain}"

                # Add time filter (note: this is query-level, Linkup handles it)
                after_date = (datetime.utcnow() - timedelta(days=lookback_days)).strftime('%Y-%m-%d')
                query += f" after:{after_date}"

                logger.info(f"Scanning {source_name}: {query}")

                # Perform deep search
                client = get_linkup_client()
                result = await client.search_web(
                    query=query,
                    depth="deep",  # Critical: deep mode for comprehensive coverage
                    output_type="structured",
                    max_results=5
                )

                # Process results
                for source in result.get("sources", []):
                    # Extract and validate publication date
                    pub_date = await extract_date_from_source(source)

                    # Only include recent updates
                    if pub_date and pub_date > datetime.utcnow() - timedelta(days=lookback_days):
                        update = {
                            "source_name": source_name,
                            "title": source.get("title", ""),
                            "url": source.get("url", ""),
                            "publication_date": pub_date.isoformat() if pub_date else None,
                            "snippet": source.get("snippet", ""),
                            "keywords_matched": [keyword],
                            "impact_assessment": await assess_impact(source),
                            "detected_at": datetime.utcnow().isoformat()
                        }
                        updates.append(update)

        # Deduplicate by URL
        seen_urls = set()
        unique_updates = []
        for update in updates:
            if update["url"] not in seen_urls:
                seen_urls.add(update["url"])
                unique_updates.append(update)

        logger.info(f"Found {len(unique_updates)} updates from {source_name}")
        return unique_updates

    except Exception as e:
        logger.error(f"Error scanning {source_name}: {str(e)}")
        return []


async def assess_impact(source: Dict[str, Any]) -> str:
    """
    Assess impact level of a regulatory update

    Args:
        source: Search result source dictionary

    Returns:
        Impact level: HIGH, MEDIUM, or LOW
    """
    text = (source.get("title", "") + " " + source.get("snippet", "")).lower()

    # High impact keywords
    high_impact_keywords = [
        "revised",
        "updated",
        "new requirement",
        "amendment",
        "change to",
        "effective date",
        "compliance deadline",
        "mandatory",
        "withdrawn",
        "supersedes"
    ]

    # Medium impact keywords
    medium_impact_keywords = [
        "guidance",
        "recommendation",
        "clarification",
        "addendum",
        "Q&A",
        "frequently asked",
        "implementation"
    ]

    # Check for high impact
    if any(kw in text for kw in high_impact_keywords):
        return "HIGH"

    # Check for medium impact
    elif any(kw in text for kw in medium_impact_keywords):
        return "MEDIUM"

    # Default to low impact
    else:
        return "LOW"


async def scan_all_regulatory_sources(
    lookback_days: int = 30
) -> ComplianceScanResponse:
    """
    Scan all configured regulatory sources for updates

    Args:
        lookback_days: How many days back to search

    Returns:
        Comprehensive scan results with all detected updates
    """
    all_updates = []

    logger.info(f"Starting compliance scan across {len(REGULATORY_SOURCES)} sources")

    # Scan each source
    for source_name, config in REGULATORY_SOURCES.items():
        updates = await deep_search_regulatory_updates(
            source_name,
            config,
            lookback_days
        )
        all_updates.extend(updates)

    # Count by impact level
    high_impact = [u for u in all_updates if u["impact_assessment"] == "HIGH"]
    medium_impact = [u for u in all_updates if u["impact_assessment"] == "MEDIUM"]
    low_impact = [u for u in all_updates if u["impact_assessment"] == "LOW"]

    # Create response
    response = ComplianceScanResponse(
        total_updates=len(all_updates),
        high_impact_count=len(high_impact),
        medium_impact_count=len(medium_impact),
        low_impact_count=len(low_impact),
        sources_scanned=len(REGULATORY_SOURCES),
        updates=[
            RegulatoryUpdate(
                update_id=f"UPD-{i+1:04d}",
                **update
            )
            for i, update in enumerate(all_updates)
        ],
        scan_timestamp=datetime.utcnow().isoformat(),
        next_scan_scheduled=(datetime.utcnow() + timedelta(hours=24)).isoformat()
    )

    # If high-impact updates found, trigger alert workflow
    if high_impact:
        await trigger_compliance_alert(high_impact)

    logger.info(
        f"Compliance scan completed: {len(all_updates)} total, "
        f"{len(high_impact)} high impact"
    )

    return response


# ============================================================================
# Database and Retrieval Functions
# ============================================================================

# In-memory storage for testing (replace with database in production)
_updates_storage: List[Dict[str, Any]] = []


async def get_recent_updates(
    days: int = 30,
    impact_level: Optional[str] = None,
    source: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Retrieve recent regulatory updates from storage

    Args:
        days: Lookback period in days
        impact_level: Filter by impact level
        source: Filter by source name

    Returns:
        Filtered list of updates
    """
    cutoff_date = datetime.utcnow() - timedelta(days=days)

    filtered = []
    for update in _updates_storage:
        # Parse detected_at timestamp
        try:
            detected = datetime.fromisoformat(update["detected_at"].replace("Z", "+00:00"))
            if detected < cutoff_date:
                continue
        except:
            continue

        # Apply filters
        if impact_level and update.get("impact_assessment") != impact_level:
            continue

        if source and update.get("source_name") != source:
            continue

        filtered.append(update)

    return filtered


async def store_scan_results(updates: List[Dict[str, Any]]) -> None:
    """
    Store scan results in database

    Args:
        updates: List of updates to store
    """
    # TODO: Implement database storage
    # For now, store in memory
    _updates_storage.extend(updates)
    logger.info(f"Stored {len(updates)} updates in cache")


# ============================================================================
# Impact Assessment and Rule Analysis
# ============================================================================

async def assess_rule_impact(
    update_id: str,
    current_rules: Optional[List[Dict[str, Any]]] = None
) -> ImpactAssessment:
    """
    Assess impact of a regulatory update on existing edit check rules

    Args:
        update_id: ID of the update to assess
        current_rules: Optional list of current rules to check

    Returns:
        Impact assessment with affected rules and recommendations
    """
    # Find the update
    update = next((u for u in _updates_storage if u.get("update_id") == update_id), None)

    if not update:
        raise ValueError(f"Update {update_id} not found")

    affected_rules = []
    recommendations = []

    # Analyze update text for specific impacts
    text = (update.get("title", "") + " " + update.get("snippet", "")).lower()

    # Check for RBQM/KRI updates
    if any(kw in text for kw in ["rbqm", "kri", "quality tolerance", "qtl"]):
        recommendations.append(
            "Review and update RBQM KRI thresholds based on new guidance"
        )

    # Check for data quality updates
    if any(kw in text for kw in ["data quality", "validation", "edit check"]):
        recommendations.append(
            "Review edit check rules for affected variables"
        )

    # Check for CDISC standard updates
    if "cdisc" in text or "sdtm" in text or "cdash" in text:
        recommendations.append(
            "Update SDTM mappings and controlled terminology"
        )

    # If current rules provided, check for specific impacts
    if current_rules:
        for rule in current_rules:
            rule_field = rule.get("field", "").lower()

            # Check if update mentions this variable
            if rule_field in text or rule.get("name", "").lower() in text:
                affected_rules.append({
                    "rule_id": rule.get("id"),
                    "rule_name": rule.get("name"),
                    "field": rule.get("field"),
                    "current_range": f"{rule.get('min')}-{rule.get('max')}",
                    "recommendation": "Review range based on updated guidance"
                })

    # Determine overall impact
    overall_impact = update.get("impact_assessment", "MEDIUM")

    # Requires action if high impact or if rules are affected
    requires_action = (
        overall_impact == "HIGH" or
        len(affected_rules) > 0
    )

    assessment = ImpactAssessment(
        update_id=update_id,
        overall_impact=overall_impact,
        affected_rules_count=len(affected_rules),
        affected_rules=affected_rules,
        recommendations=recommendations,
        requires_action=requires_action,
        assessment_timestamp=datetime.utcnow().isoformat()
    )

    return assessment


# ============================================================================
# Alert and Notification Functions
# ============================================================================

async def trigger_compliance_alert(high_impact_updates: List[Dict[str, Any]]) -> None:
    """
    Trigger alerts for high-impact regulatory updates

    Args:
        high_impact_updates: List of high-impact updates
    """
    logger.warning(
        f"HIGH IMPACT ALERT: {len(high_impact_updates)} regulatory updates require attention"
    )

    # TODO: Implement actual alerting (email, Slack, etc.)
    for update in high_impact_updates:
        logger.warning(
            f"  - {update['source_name']}: {update['title']}\n"
            f"    URL: {update['url']}"
        )


async def create_github_pr(
    updates: List[Dict[str, Any]],
    updated_rules: List[Dict[str, Any]]
) -> str:
    """
    Create GitHub PR with updated YAML rules

    Args:
        updates: List of regulatory updates
        updated_rules: List of updated rules

    Returns:
        PR URL

    Note: This is a placeholder. Real implementation would use GitHub API
    """
    branch_name = f"compliance-update-{datetime.utcnow().strftime('%Y%m%d')}"

    logger.info(f"Creating GitHub PR on branch: {branch_name}")

    # TODO: Implement GitHub API integration
    # For now, just log what would be in the PR

    pr_description = generate_pr_description(updates, updated_rules)
    logger.info(f"PR Description:\n{pr_description}")

    # Mock PR URL
    pr_url = f"https://github.com/yourorg/synthetictrial-rules/pull/123"

    return pr_url


def generate_pr_description(
    updates: List[Dict[str, Any]],
    rules: List[Dict[str, Any]]
) -> str:
    """
    Generate PR description with evidence

    Args:
        updates: List of regulatory updates
        rules: List of affected/updated rules

    Returns:
        Formatted PR description in Markdown
    """
    desc = "## Automated Compliance Update\n\n"
    desc += f"**Detected:** {len(updates)} regulatory changes\n"
    desc += f"**Affected Rules:** {len(rules)}\n"
    desc += f"**Generated:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}\n\n"

    desc += "### Regulatory Changes Detected:\n\n"
    for update in updates[:5]:  # Top 5
        desc += f"- **{update['source_name']}**: [{update['title']}]({update['url']})\n"
        if update.get('publication_date'):
            desc += f"  - Published: {update['publication_date']}\n"
        desc += f"  - Impact: {update['impact_assessment']}\n"
        desc += f"  - _{update['snippet'][:150]}..._\n\n"

    if rules:
        desc += "### Proposed Rule Updates:\n\n"
        for rule in rules[:5]:  # Top 5
            desc += f"```yaml\n{yaml.dump({'rules': [rule]}, default_flow_style=False)}\n```\n\n"

    desc += "---\n\n"
    desc += "**⚠️ REQUIRES REVIEW:** These changes were auto-generated. "
    desc += "Please review before merging.\n\n"
    desc += "_Generated by Linkup Integration Service - Compliance Watcher_\n"

    return desc


def generate_rule_from_guidance(update: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Generate or update a rule based on regulatory guidance

    Args:
        update: Regulatory update dictionary

    Returns:
        Updated rule or None

    Note: This is a simplified placeholder. Real implementation would
    use more sophisticated NLP to extract requirements from guidance.
    """
    # TODO: Implement rule generation from guidance text
    # This would involve parsing the guidance document and
    # extracting specific requirements/thresholds

    logger.info(f"Generating rule from guidance: {update.get('title')}")

    # Placeholder
    return None
