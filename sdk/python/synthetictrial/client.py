"""
SyntheticTrial Python SDK - Main Client

Stripe-style API client for synthetic clinical trial data generation.
"""

import os
from typing import Optional
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .resources.trials import TrialsResource
from .resources.analytics import AnalyticsResource
from .resources.benchmarks import BenchmarksResource


class SyntheticTrial:
    """
    Main client for the SyntheticTrial API

    Usage:
        >>> from synthetictrial import SyntheticTrial
        >>> client = SyntheticTrial(api_key="your_key")
        >>> trial = client.trials.generate(indication="Hypertension", n_per_arm=50)
        >>> print(trial.realism_score)
    """

    DEFAULT_BASE_URL = "http://localhost:8000"
    DEFAULT_TIMEOUT = 120  # 2 minutes for LLM generation

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: int = DEFAULT_TIMEOUT,
        max_retries: int = 3
    ):
        """
        Initialize the SyntheticTrial client

        Args:
            api_key: API key for authentication (optional for local dev)
            base_url: Base URL for the API (default: http://localhost:8000)
            timeout: Request timeout in seconds (default: 120)
            max_retries: Number of retries for failed requests (default: 3)
        """
        self.api_key = api_key or os.getenv("SYNTHETICTRIAL_API_KEY")
        self.base_url = base_url or os.getenv("SYNTHETICTRIAL_BASE_URL", self.DEFAULT_BASE_URL)
        self.timeout = timeout

        # Configure session with retries
        self.session = requests.Session()
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        # Initialize resources
        self.trials = TrialsResource(self)
        self.analytics = AnalyticsResource(self)
        self.benchmarks = BenchmarksResource(self)

    def _get_headers(self) -> dict:
        """Get request headers with authentication"""
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "synthetictrial-python/1.0.0"
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def request(
        self,
        method: str,
        endpoint: str,
        data: Optional[dict] = None,
        params: Optional[dict] = None
    ) -> dict:
        """
        Make an HTTP request to the API

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            data: Request body data
            params: URL query parameters

        Returns:
            Response data as dictionary

        Raises:
            requests.exceptions.RequestException: If request fails
        """
        url = f"{self.base_url}{endpoint}"

        try:
            response = self.session.request(
                method=method,
                url=url,
                json=data,
                params=params,
                headers=self._get_headers(),
                timeout=self.timeout
            )
            response.raise_for_status()

            # Handle empty responses
            if response.status_code == 204 or not response.content:
                return {}

            return response.json()

        except requests.exceptions.HTTPError as e:
            # Enhance error message with response body if available
            try:
                error_data = e.response.json()
                error_msg = error_data.get("detail", str(e))
            except:
                error_msg = str(e)

            raise requests.exceptions.HTTPError(
                f"API request failed: {error_msg}",
                response=e.response
            )

    def __repr__(self):
        return f"SyntheticTrial(base_url='{self.base_url}')"
