"""OpenRouter API fetcher module."""

import logging
from typing import Any, Optional

import requests

log = logging.getLogger("monitor")

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/models"


class OpenRouterFetcher:
    """OpenRouter model price fetcher."""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'Accept': 'application/json',
        })

    def fetch_models(self) -> Optional[dict[str, Any]]:
        """Fetch all models from OpenRouter API.

        Returns:
            API response as dict, or None on failure.
        """
        try:
            response = self.session.get(OPENROUTER_API_URL, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            log.error(f"Failed to fetch OpenRouter models: {e}")
            return None

    def get_model_prices(self, model_ids: list[str]) -> dict[str, dict]:
        """Get prices for specified models.

        Args:
            model_ids: List of model IDs to fetch prices for (e.g., ["openai/gpt-4"])

        Returns:
            Dict mapping model_id to price info:
            {
                "openai/gpt-4": {
                    "prompt_price": "0.03",
                    "completion_price": "0.06",
                    "has_price": True
                }
            }
        """
        data = self.fetch_models()
        if not data or "data" not in data:
            return {}

        prices = {}
        for model in data["data"]:
            model_id = model.get("id", "")
            if model_id in model_ids:
                pricing = model.get("pricing", {})
                prompt_price = pricing.get("prompt", "0")
                completion_price = pricing.get("completion", "0")

                has_price = (
                    float(prompt_price) > 0 if prompt_price else False
                ) or (
                    float(completion_price) > 0 if completion_price else False
                )

                prices[model_id] = {
                    "prompt_price": prompt_price,
                    "completion_price": completion_price,
                    "has_price": has_price,
                    "name": model.get("name", model_id),
                }

        return prices

    def check_models_with_price(self, model_ids: list[str]) -> dict[str, dict]:
        """Check which models have non-zero prices.

        Args:
            model_ids: List of model IDs to check

        Returns:
            Dict of models that have prices (price > 0)
        """
        all_prices = self.get_model_prices(model_ids)
        return {
            model_id: info
            for model_id, info in all_prices.items()
            if info["has_price"]
        }