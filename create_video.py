import os
import sys
import argparse
import logging
import threading
from config import load_config
from pipeline import Pipeline

# Set up logging to console
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

def parse_args():
    parser = argparse.ArgumentParser(
        description="Nullpk AI Content Studio - CLI Video Creator",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    # Required positional argument
    parser.add_argument("topic", type=str, help="The topic for your AI generated video.")

    # Optional pipeline starting point
    parser.add_argument(
        "--start-step",
        type=str,
        default="Deep Research",
        choices=[
            "Deep Research", "Fact Check Research", "Revise Research", "Podcast Script",
            "Generate Thumbnail", "Analyze Tone", "Audio (TTS)", "Generate Timed Images",
            "Video Generation", "Add Background Music", "Create Final Video",
            "Generate SEO Metadata", "Generate Timestamps", "Generate Snippets"
        ],
        help="The pipeline step to start execution from."
    )

    # Configuration overrides
    parser.add_argument("--gemini-key", type=str, help="Override GEMINI_API_KEY")
    parser.add_argument("--wavespeed-key", type=str, help="Override WAVESPEED_AI_KEY")
    parser.add_argument("--news-key", type=str, help="Override NEWS_API_KEY")

    parser.add_argument(
        "--bg-mode",
        type=str,
        default="AI Video",
        choices=["AI Video", "Image Slideshow", "Disabled"],
        help="Background visual mode."
    )

    parser.add_argument(
        "--content-style",
        type=str,
        default="Podcast",
        choices=["Podcast", "ASMR Video", "Documentary", "Product Ad", "Story", "Kids Story", "Horror Story", "Viral Video"],
        help="Style of content to generate."
    )

    parser.add_argument(
        "--aspect-ratio",
        type=str,
        default="16:9 (Horizontal)",
        choices=["16:9 (Horizontal)", "9:16 (Vertical)", "1:1 (Square)"],
        help="Video aspect ratio."
    )

    parser.add_argument("--image-count", type=int, default=8, help="Number of images for Slideshow mode.")
    parser.add_argument("--video-count", type=int, default=1, help="Number of video clips for AI Video mode.")

    parser.add_argument("--fact-check", action="store_true", help="Enable Fact-Checking.")
    parser.add_argument("--metadata", action="store_true", help="Generate SEO Metadata.")
    parser.add_argument("--timestamps", action="store_true", help="Generate Timestamps.")
    parser.add_argument("--captions", action="store_true", help="Enable Auto-Captioning.")
    parser.add_argument("--music", action="store_true", help="Add Background Music.")
    parser.add_argument("--snippets", action="store_true", help="Generate Social Media Snippets.")
    parser.add_argument("--thumbnail", action="store_true", help="Generate Thumbnail.")

    return parser.parse_args()

def status_callback(step_index, status, progress):
    # Map step index to step name
    from pipeline import PIPELINE_STEPS
    step_name = PIPELINE_STEPS[step_index] if step_index < len(PIPELINE_STEPS) else f"Step {step_index}"
    logging.info(f"[PROGRESS] {step_name}: {status} ({progress*100:.0f}%)")

def seo_callback(metadata):
    logging.info(f"[SEO METADATA] Title: {metadata.get('title', '')}")
    logging.info(f"[SEO METADATA] Tags: {metadata.get('tags', '')}")
    logging.info(f"[SEO METADATA] Description:\n{metadata.get('description', '')}")

def timestamps_callback(timestamps_text):
    logging.info(f"[TIMESTAMPS]:\n{timestamps_text}")

def script_review_callback(script_content, file_path, resume_event):
    logging.info("=" * 60)
    logging.info(" SCRIPT REVIEW REQUIRED ")
    logging.info("=" * 60)
    logging.info(f"\n{script_content}\n")
    logging.info("=" * 60)
    logging.info(f"The script above has been saved to: {file_path}")
    logging.info("You can open and edit that file now if you wish.")
    input("Press ENTER in this console to approve the script and continue...")
    resume_event.set()

def run_pipeline():
    args = parse_args()

    # Load configuration
    config = load_config()

    # Apply CLI overrides to configuration
    if args.gemini_key:
        config["GEMINI_API_KEY"] = args.gemini_key
    if args.wavespeed_key:
        config["WAVESPEED_AI_KEY"] = args.wavespeed_key
    if args.news_key:
        config["NEWS_API_KEY"] = args.news_key

    config["BG_MODE"] = args.bg_mode
    config["GENERATE_TIMED_IMAGES"] = (args.bg_mode == "Image Slideshow")
    config["TIMED_IMAGES_AS_SLIDESHOW"] = (args.bg_mode == "Image Slideshow")
    config["CONTENT_STYLE"] = args.content_style
    config["VIDEO_ASPECT_RATIO"] = args.aspect_ratio
    config["IMAGE_COUNT"] = args.image_count
    config["VIDEO_CLIP_COUNT"] = args.video_count

    config["FACT_CHECK_ENABLED"] = args.fact_check
    config["GENERATE_METADATA"] = args.metadata
    config["GENERATE_TIMESTAMPS"] = args.timestamps
    config["CAPTION_ENABLED"] = args.captions
    config["ADD_MUSIC"] = args.music
    config["GENERATE_SNIPPETS"] = args.snippets
    config["GENERATE_THUMBNAIL"] = args.thumbnail

    # Check for Gemini API key
    if not config.get("GEMINI_API_KEY"):
        logging.error("GEMINI_API_KEY is missing. Please provide it via --gemini-key or in config.json")
        sys.exit(1)

    stop_event = threading.Event()

    def on_finish_callback(success):
        if success:
            logging.info("✅ Pipeline completed successfully!")
        else:
            logging.error("❌ Pipeline execution failed.")
            sys.exit(1)

    pipeline_instance = Pipeline(
        config=config,
        stop_event=stop_event,
        status_callback=status_callback,
        seo_callback=seo_callback,
        on_finish_callback=on_finish_callback,
        timestamps_callback=timestamps_callback,
        on_script_generated=script_review_callback
    )

    try:
        pipeline_instance.run(args.topic, args.start_step)
    except KeyboardInterrupt:
        logging.info("Aborting pipeline on user request...")
        stop_event.set()
        sys.exit(1)

if __name__ == "__main__":
    run_pipeline()
