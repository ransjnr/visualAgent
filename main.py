from __future__ import annotations

import argparse

from dotenv import load_dotenv

from visual_agent.agent import VisualAgent
from visual_agent.config import load_config


def main() -> None:
    load_dotenv()

    ap = argparse.ArgumentParser(description="Always-on visual assistant (MVP)")
    ap.add_argument("--config", default="config.yaml", help="Path to YAML config (default: config.yaml)")
    args = ap.parse_args()

    cfg = load_config(args.config)
    VisualAgent(cfg).start()


if __name__ == "__main__":
    main()

