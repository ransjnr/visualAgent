from __future__ import annotations

import argparse

from dotenv import load_dotenv

from visual_agent.agent import VisualAgent
from visual_agent.config import load_config


def main() -> None:
    # Load environment variables from .env.local first, then .env
    # .env.local takes precedence and should not be committed to git
    load_dotenv(".env.local")  # Try .env.local first
    load_dotenv()  # Fallback to .env if .env.local doesn't exist

    ap = argparse.ArgumentParser(description="Always-on visual assistant (MVP)")
    ap.add_argument("--config", default="config.yaml", help="Path to YAML config (default: config.yaml)")
    args = ap.parse_args()

    cfg = load_config(args.config)
    VisualAgent(cfg).start()


if __name__ == "__main__":
    main()

