#!/usr/bin/env python3
"""OpenRouter price monitor - main program."""

import json
import sys
from pathlib import Path

import logger
from monitors.openrouter.fetcher import OpenRouterFetcher
from monitors.telegram_notifier import TelegramNotifier

log = logger.setup_logger("openrouter_monitor")

CONFIG_FILE = "/app/data/openrouter_config.json"


def load_config() -> dict:
    """Load OpenRouter monitor configuration."""
    config_path = Path(CONFIG_FILE)
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "enabled": True,
        "models": [],
        "schedule": "0 * * * *",
    }


def save_config(config: dict) -> None:
    """Save configuration to file."""
    config_path = Path(CONFIG_FILE)
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


def format_price_message(models_with_prices: dict[str, dict]) -> str:
    """Format price notification message.

    Args:
        models_with_prices: Dict of models with prices

    Returns:
        Formatted message string
    """
    lines = ["*OpenRouter 模型价格变动*"]
    lines.append("以下模型当前有价格:\n")

    for model_id, info in models_with_prices.items():
        name = info.get("name", model_id)
        prompt = info.get("prompt_price", "0")
        completion = info.get("completion_price", "0")
        lines.append(f"• `{model_id}`")
        lines.append(f"  Prompt: ${prompt}/1K tokens")
        lines.append(f"  Completion: ${completion}/1K tokens\n")

    return "\n".join(lines)


def check_prices() -> dict:
    """Check model prices and send notification if needed.

    Returns:
        Dict with results
    """
    config = load_config()

    if not config.get("enabled", True):
        log.info("OpenRouter monitor is disabled")
        return {"status": "disabled"}

    model_ids = config.get("models", [])
    if not model_ids:
        log.info("No models configured to monitor")
        return {"status": "no_models"}

    log.info(f"Checking prices for {len(model_ids)} models")

    fetcher = OpenRouterFetcher()
    models_with_prices = fetcher.check_models_with_price(model_ids)

    result = {
        "models_checked": len(model_ids),
        "models_with_prices": len(models_with_prices),
        "details": models_with_prices,
    }

    if models_with_prices:
        log.info(f"Found {len(models_with_prices)} models with prices")
        notifier = TelegramNotifier()
        message = format_price_message(models_with_prices)
        notifier.send_message(message)
    else:
        log.info("No models with prices found, no notification sent")

    return result


def main():
    """Main entry point."""
    logger.cleanup_old_logs()
    result = check_prices()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())