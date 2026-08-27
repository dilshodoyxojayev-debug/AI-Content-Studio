#!/usr/bin/env python3
"""
generate_content.py

CLI script for automated AI video generation using Nullpk AI Content Studio.
Supports Python tutorials, Cinematic Nature/Animal Facts, Documentaries, and Shorts/Reels/TikToks.
"""

import argparse
import logging
import threading
import sys
import os

from config import load_config
from pipeline import Pipeline, PIPELINE_STEPS

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)]
    )

def main():
    parser = argparse.ArgumentParser(description="Automated Content Video Generation CLI")
    parser.add_argument("--topic", type=str, default="5 Mind-Blowing Facts About Nature and the Animal Kingdom!", help="Video topic")
    parser.add_argument("--aspect-ratio", type=str, choices=["16:9", "9:16"], default="9:16", help="Aspect ratio: 16:9 for YouTube Long-form, 9:16 for Shorts/Reels/TikTok")
    parser.add_argument("--style", type=str, default="Documentary", help="Content style profile (e.g., 'Documentary', 'Viral Video', 'Tech Tutorial & Code Tricks')")
    parser.add_argument("--language", type=str, default="English", help="Target language")

    args = parser.parse_args()
    setup_logging()

    config = load_config()
    config["CONTENT_STYLE"] = args.style
    config["PODCAST_LANGUAGE"] = args.language
    config["LANGUAGE_ENABLED"] = True
    config["VIDEO_ASPECT_RATIO"] = "16:9 (Horizontal)" if args.aspect_ratio == "16:9" else "9:16 (Vertical)"

    logging.info(f"🚀 Starting content generation for topic: '{args.topic}'")
    logging.info(f"Aspect Ratio: {config['VIDEO_ASPECT_RATIO']} | Style: {config['CONTENT_STYLE']} | Language: {config['PODCAST_LANGUAGE']}")

    stop_event = threading.Event()

    def status_callback(step_idx, status_symbol, progress):
        step_name = PIPELINE_STEPS[step_idx] if step_idx < len(PIPELINE_STEPS) else f"Step {step_idx}"
        logging.info(f"Pipeline [{step_idx+1}/{len(PIPELINE_STEPS)}] {step_name}: {status_symbol}")

    def seo_callback(metadata):
        logging.info("SEO Metadata Generated:")
        logging.info(f"Title: {metadata.get('title')}")
        logging.info(f"Description: {metadata.get('description')[:150]}...")
        logging.info(f"Tags: {metadata.get('tags')}")

    def timestamps_callback(timestamps):
        logging.info(f"Timestamps:\n{timestamps}")

    def on_finish(success):
        if success:
            logging.info("✅ Video generation completed successfully!")
        else:
            logging.error("❌ Video generation pipeline encountered an error.")

    pipeline_inst = Pipeline(
        config=config,
        stop_event=stop_event,
        status_callback=status_callback,
        seo_callback=seo_callback,
        on_finish_callback=on_finish,
        timestamps_callback=timestamps_callback
    )

    pipeline_inst.run(args.topic, "Deep Research")

if __name__ == "__main__":
    main()
