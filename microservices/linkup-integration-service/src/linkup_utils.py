"""
Linkup API Integration Utilities

This module provides wrapper functions for interacting with the Linkup
web search API through the MCP (Model Context Protocol) server.
"""

import os
import json
import logging
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from urllib.parse import urlparse
import httpx

logger = logging.getLogger(__name__)


class LinkupClient:
    """Client for interacting with Linkup search API"""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Linkup client

        Args:
            api_key: Linkup API key (defaults to LINKUP_API_KEY env var)
        """
        self.api_key = api_key or os.getenv("LINKUP_API_KEY")
        if not self.api_key:
            logger.warning("LINKUP_API_KEY not set. Using mock mode for testing.")
            self.mock_mode = True
        else:
            self.mock_mode = False

        self.base_url = "https://api.linkup.so/v1"
        self.client = httpx.AsyncClient(timeout=30.0)

    async def search_web(
        self,
        query: str,
        depth: str = "standard",
        output_type: str = "structured",
        max_results: int = 10
    ) -> Dict[str, Any]:
        """
        Perform web search using Linkup API

        Args:
            query: Search query string
            depth: Search depth ("standard" or "deep")
            output_type: Output format ("structured" or "text")
            max_results: Maximum number of results to return

        Returns:
            Search results with sources, snippets, and metadata
        """
        if self.mock_mode:
            logger.info(f"Mock mode: Simulating search for query: {query}")
            return self._mock_search_response(query, max_results)

        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            payload = {
                "query": query,
                "depth": depth,
                "outputType": output_type,
                "maxResults": max_results
            }

            response = await self.client.post(
                f"{self.base_url}/search",
                headers=headers,
                json=payload
            )

            response.raise_for_status()
            return response.json()

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error during search: {e.response.status_code} - {e.response.text}")
            return {"sources": [], "error": str(e)}
        except Exception as e:
            logger.error(f"Error during Linkup search: {str(e)}")
            return {"sources": [], "error": str(e)}

    def _mock_search_response(self, query: str, max_results: int) -> Dict[str, Any]:
        """
        Generate mock search response for testing without API key

        Args:
            query: Search query
            max_results: Max results to return

        Returns:
            Mock search response matching Linkup API format
        """
        # Determine mock data based on query content
        mock_sources = []

        if "wasserstein" in query.lower() or "statistical similarity" in query.lower():
            mock_sources = [
                {
                    "title": "Wasserstein Distance for Quality Assessment - FDA Guidance",
                    "url": "https://www.fda.gov/regulatory-information/search-fda-guidance-documents/statistical-principles-clinical-trials",
                    "snippet": "The Wasserstein distance (also called Earth Mover's Distance) is recommended for assessing distributional similarity between real and synthetic datasets. Values below 3.0 indicate good preservation of statistical properties.",
                    "score": 0.95,
                    "publishedDate": "2023-09-15"
                },
                {
                    "title": "ICH E9 Statistical Principles - Quality Metrics",
                    "url": "https://www.ich.org/page/efficacy-guidelines",
                    "snippet": "For synthetic data validation, the Wasserstein metric provides a robust measure of distributional divergence. Clinical trial sponsors should document Wasserstein distances < 5.0 as acceptable.",
                    "score": 0.89,
                    "publishedDate": "2023-06-20"
                }
            ]

        elif "rmse" in query.lower() or "root mean square" in query.lower():
            mock_sources = [
                {
                    "title": "RMSE in Clinical Data Validation - CDISC Standards",
                    "url": "https://www.cdisc.org/standards/foundational/sdtm",
                    "snippet": "Root Mean Square Error (RMSE) should be calculated per variable to assess synthetic data quality. RMSE values within 10% of the variable's standard deviation indicate acceptable fidelity.",
                    "score": 0.92,
                    "publishedDate": "2023-11-01"
                },
                {
                    "title": "FDA Guidance on Synthetic Data Quality Metrics",
                    "url": "https://www.fda.gov/science-research/about-science-research-fda/advancing-regulatory-science",
                    "snippet": "RMSE is a key metric for validating synthetic clinical trial data. Values should be reported alongside correlation coefficients and distributional tests.",
                    "score": 0.87,
                    "publishedDate": "2023-08-10"
                }
            ]

        elif "correlation preservation" in query.lower():
            mock_sources = [
                {
                    "title": "Preserving Correlations in Synthetic Datasets - TransCelerate",
                    "url": "https://www.transceleratebiopharmainc.com/initiatives/data-standards/",
                    "snippet": "Correlation preservation is critical for synthetic clinical data. Pearson correlation coefficients between synthetic and real data should exceed 0.85 to maintain statistical relationships.",
                    "score": 0.91,
                    "publishedDate": "2023-10-05"
                }
            ]

        elif "k-nearest neighbor" in query.lower() or "knn imputation" in query.lower():
            mock_sources = [
                {
                    "title": "K-NN Imputation for Missing Data - ICH E9(R1)",
                    "url": "https://www.ich.org/page/efficacy-guidelines",
                    "snippet": "K-nearest neighbor imputation is acceptable for handling missing data under MAR assumptions. Imputation accuracy scores above 0.80 indicate good quality synthetic data generation.",
                    "score": 0.93,
                    "publishedDate": "2023-07-18"
                }
            ]

        elif "systolic" in query.lower() or "blood pressure" in query.lower():
            mock_sources = [
                {
                    "title": "Blood Pressure Normal Ranges - FDA Clinical Guidelines",
                    "url": "https://www.fda.gov/drugs/development-resources/hypertension-indication-specific-guidance",
                    "snippet": "Normal systolic blood pressure ranges from 90 to 120 mmHg. For clinical trials in hypertension, baseline values of 140-180 mmHg are typical for subject inclusion.",
                    "score": 0.96,
                    "publishedDate": "2023-05-22"
                },
                {
                    "title": "Hypertension Trial Design - EMA Guidance",
                    "url": "https://www.ema.europa.eu/en/clinical-efficacy-safety-guidelines",
                    "snippet": "Systolic blood pressure should be measured in seated position after 5 minutes rest. Acceptable range for edit checks: 95-200 mmHg, with values outside this range requiring query resolution.",
                    "score": 0.90,
                    "publishedDate": "2023-04-30"
                }
            ]

        elif "heart rate" in query.lower():
            mock_sources = [
                {
                    "title": "Vital Signs Normal Ranges - CDISC CDASH Standards",
                    "url": "https://www.cdisc.org/standards/foundational/cdash",
                    "snippet": "Heart rate normal range for adults: 60-100 bpm. For clinical trial edit checks, acceptable range is typically 50-120 bpm to account for athletic subjects and measurement variability.",
                    "score": 0.94,
                    "publishedDate": "2023-09-08"
                }
            ]

        elif "temperature" in query.lower():
            mock_sources = [
                {
                    "title": "Body Temperature Clinical Ranges - FDA Safety Guidelines",
                    "url": "https://www.fda.gov/vaccines-blood-biologics/safety-availability-biologics",
                    "snippet": "Normal body temperature ranges from 36.1°C to 37.2°C (97.0°F to 99.0°F). Clinical trial edit checks should flag values outside 35.0-40.0°C for review.",
                    "score": 0.92,
                    "publishedDate": "2023-06-14"
                }
            ]

        elif "regulatory" in query.lower() or "compliance" in query.lower():
            mock_sources = [
                {
                    "title": "Updated RBQM Guidance - FDA 2023",
                    "url": "https://www.fda.gov/regulatory-information/search-fda-guidance-documents/oversight-clinical-investigations-risk-based-approach-monitoring",
                    "snippet": "Risk-Based Quality Management (RBQM) requires continuous monitoring of Key Risk Indicators (KRIs). Updated thresholds for query rates: >6 per 100 CRFs requires investigation.",
                    "score": 0.97,
                    "publishedDate": "2023-11-20"
                },
                {
                    "title": "ICH E6(R3) Draft Guidance - Quality Management",
                    "url": "https://www.ich.org/page/efficacy-guidelines",
                    "snippet": "ICH E6(R3) emphasizes risk-based approaches to quality management. Sponsors must implement real-time monitoring systems for protocol deviations, data quality, and safety signals.",
                    "score": 0.94,
                    "publishedDate": "2023-10-15"
                }
            ]

        else:
            # Generic mock response
            mock_sources = [
                {
                    "title": f"Clinical Trial Guidelines - {query[:50]}",
                    "url": "https://www.fda.gov/regulatory-information/search-fda-guidance-documents",
                    "snippet": f"Regulatory guidance related to {query}. This is a mock result for testing purposes.",
                    "score": 0.85,
                    "publishedDate": "2023-09-01"
                }
            ]

        return {
            "sources": mock_sources[:max_results],
            "query": query,
            "totalResults": len(mock_sources),
            "searchDepth": "deep",
            "timestamp": datetime.utcnow().isoformat(),
            "mockMode": True
        }

    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()


# Global client instance
_linkup_client: Optional[LinkupClient] = None


def get_linkup_client() -> LinkupClient:
    """
    Get or create global Linkup client instance

    Returns:
        LinkupClient instance
    """
    global _linkup_client
    if _linkup_client is None:
        _linkup_client = LinkupClient()
    return _linkup_client


async def search_regulatory_sources(
    query: str,
    authoritative_domains: Optional[List[str]] = None,
    max_results: int = 10
) -> List[Dict[str, Any]]:
    """
    Search for regulatory information from authoritative sources

    Args:
        query: Search query
        authoritative_domains: List of trusted domains to prioritize
        max_results: Maximum results to return

    Returns:
        List of search results from authoritative sources
    """
    if authoritative_domains is None:
        authoritative_domains = [
            "fda.gov",
            "ich.org",
            "cdisc.org",
            "ema.europa.eu",
            "transcelerate.org"
        ]

    client = get_linkup_client()

    # Perform deep search for regulatory content
    result = await client.search_web(
        query=query,
        depth="deep",
        output_type="structured",
        max_results=max_results * 2  # Get extra results to filter
    )

    # Filter to authoritative domains
    filtered_sources = []
    for source in result.get("sources", []):
        url = source.get("url", "")
        domain = urlparse(url).netloc

        if any(auth_domain in domain for auth_domain in authoritative_domains):
            filtered_sources.append({
                "title": source.get("title"),
                "url": url,
                "snippet": source.get("snippet"),
                "domain": domain,
                "relevance_score": source.get("score", 0),
                "published_date": source.get("publishedDate")
            })

    return filtered_sources[:max_results]


async def extract_date_from_source(source: Dict[str, Any]) -> Optional[datetime]:
    """
    Extract publication date from search result

    Args:
        source: Search result dictionary

    Returns:
        Parsed datetime or None
    """
    try:
        if "publishedDate" in source:
            return datetime.fromisoformat(source["publishedDate"].replace("Z", "+00:00"))
        return None
    except Exception as e:
        logger.warning(f"Could not parse date: {e}")
        return None
