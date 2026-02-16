"""Record a screencast of the resumake web UI using Playwright.

Usage:
    python scripts/record_web_demo.py          # outputs demo-web.webm + demo-web.gif
    python scripts/record_web_demo.py --no-gif # skip GIF conversion

Requirements:
    pip install playwright
    playwright install chromium
    brew install ffmpeg   # for GIF conversion
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
import textwrap
import time
from pathlib import Path

# ---------------------------------------------------------------------------
# Sample data
# ---------------------------------------------------------------------------

SAMPLE_CV = textwrap.dedent("""\
    name: "Sarah Chen"
    title: "Full-Stack Engineer & Tech Lead"
    photo: "profile.jpeg"

    contact:
      address: "San Francisco, CA"
      phone: "+1 415 555 0198"
      email: "sarah.chen@example.com"
      nationality: "US Citizen"

    links:
      - label: "LinkedIn"
        url: "https://linkedin.com/in/sarahchen"
      - label: "GitHub"
        url: "https://github.com/sarahchen"
      - label: "Portfolio"
        url: "https://sarahchen.dev"

    skills:
      leadership:
        - "Engineering Management"
        - "Agile / Scrum"
        - "System Design"
        - "Cross-Team Collaboration"
      technical:
        - "Python"
        - "TypeScript"
        - "React"
        - "Node.js"
        - "PostgreSQL"
        - "Redis"
        - "Docker"
        - "Kubernetes"
        - "AWS"
        - "GraphQL"
      languages:
        - name: "English"
          level: "native"
        - name: "Mandarin"
          level: "fluent"
        - name: "Spanish"
          level: "professional"

    profile: >
      Full-Stack Engineer and Tech Lead with 7+ years of experience building
      high-performance web applications at scale. Led teams of 4-10 engineers
      delivering products used by millions. Passionate about developer experience,
      observability, and shipping fast without breaking things.

    experience:
      - title: "Tech Lead"
        org: "Acme Cloud Inc."
        start: "January 2022"
        end: "Present"
        description: "Leading the Platform team building internal developer tools and infrastructure."
        bullets:
          - "Designed and shipped a feature-flag platform adopted by 12 product teams, reducing release risk by 45%"
          - "Led migration from monolith to microservices architecture, improving deploy frequency from weekly to daily"
          - "Mentored 4 junior engineers, 2 of whom were promoted within 18 months"
          - "Reduced P95 API latency from 800ms to 120ms through caching and query optimization"
        tech_stack: ["Python", "FastAPI", "React", "PostgreSQL", "Redis", "Kubernetes"]

      - title: "Senior Software Engineer"
        org: "Streamline Analytics"
        start: "March 2019"
        end: "December 2021"
        description: "Built real-time analytics dashboards and data pipelines for enterprise clients."
        bullets:
          - "Architected a real-time streaming pipeline processing 2M+ events/minute using Kafka and Flink"
          - "Built a drag-and-drop dashboard builder used by 500+ enterprise customers"
          - "Implemented end-to-end testing infrastructure, reducing production incidents by 60%"
        tech_stack: ["TypeScript", "React", "Node.js", "Kafka", "ClickHouse", "AWS"]

      - title: "Software Engineer"
        org: "DataBridge"
        start: "July 2017"
        end: "February 2019"
        description: "Backend development for a B2B data integration platform."
        bullets:
          - "Built REST and GraphQL APIs serving 3M+ daily requests with 99.95% uptime"
          - "Designed an ETL framework that reduced client onboarding time from 2 weeks to 2 days"
        tech_stack: ["Python", "Django", "PostgreSQL", "Docker"]

    education:
      - degree: "M.S. Computer Science"
        institution: "Stanford University"
        start: "2015"
        end: "2017"
        description: "Focus on distributed systems and machine learning."
        details: "Thesis: 'Low-Latency Stream Processing for Real-Time Analytics'"

      - degree: "B.S. Computer Science"
        institution: "UC Berkeley"
        start: "2011"
        end: "2015"

    certifications:
      - name: "AWS Solutions Architect Professional"
        org: "Amazon Web Services"
        start: "2023"
        end: "2026"

      - name: "Certified Kubernetes Administrator"
        org: "CNCF"
        start: "2022"
        end: "2025"

    publications:
      - title: "Low-Latency Stream Processing at Scale"
        year: 2024
        venue: "QCon San Francisco"

    volunteering:
      - title: "Workshop Instructor"
        org: "Women Who Code SF"
        start: "2020"
        end: "Present"
        description: "Monthly workshops on system design and career growth in tech."

    references: "Available upon request."
""")


def generate_profile_photo(dest: Path) -> None:
    """Generate a simple avatar photo with initials."""
    from PIL import Image, ImageDraw, ImageFont

    size = 400
    img = Image.new("RGB", (size, size), "#2563eb")
    draw = ImageDraw.Draw(img)

    # Draw a lighter circle
    margin = 20
    draw.ellipse([margin, margin, size - margin, size - margin], fill="#3b82f6")

    # Draw initials
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 140)
    except (OSError, IOError):
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 140)
        except (OSError, IOError):
            font = ImageFont.load_default()

    text = "SC"
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = (size - tw) / 2
    y = (size - th) / 2 - bbox[1]
    draw.text((x, y), text, fill="white", font=font)

    img.save(dest, "JPEG", quality=90)


def setup_demo_project(project_dir: Path) -> None:
    """Create a temp project with sample CV and photo."""
    project_dir.mkdir(parents=True, exist_ok=True)
    assets_dir = project_dir / "assets"
    assets_dir.mkdir(exist_ok=True)

    (project_dir / "cv.yaml").write_text(SAMPLE_CV)
    generate_profile_photo(assets_dir / "profile.jpeg")


# ---------------------------------------------------------------------------
# Playwright screencast
# ---------------------------------------------------------------------------

PAUSE = 1.2  # seconds between actions (for readability)


def record(project_dir: Path, output_video: Path) -> None:
    from playwright.sync_api import sync_playwright

    repo_root = Path(__file__).resolve().parent.parent

    # Start the server in a subprocess
    server = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "web.server:app", "--host", "127.0.0.1", "--port", "3199"],
        cwd=project_dir,
        env={
            **__import__("os").environ,
            "PYTHONPATH": str(repo_root),
        },
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    # Wait for server to start
    import urllib.request

    for _ in range(30):
        try:
            urllib.request.urlopen("http://127.0.0.1:3199/api/status")
            break
        except Exception:
            time.sleep(0.3)
    else:
        server.terminate()
        raise RuntimeError("Server did not start in time")

    video_dir = output_video.parent / "_recordings"
    video_dir.mkdir(exist_ok=True)

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                viewport={"width": 1440, "height": 900},
                record_video_dir=str(video_dir),
                record_video_size={"width": 1440, "height": 900},
            )
            page = context.new_page()
            page.goto("http://127.0.0.1:3199")
            page.wait_for_load_state("networkidle")
            time.sleep(PAUSE)

            # --- 1. Editor page (default) ---
            # Scroll down to show some content
            page.evaluate("window.scrollTo(0, 200)")
            time.sleep(PAUSE)
            page.evaluate("window.scrollTo(0, 0)")
            time.sleep(0.5)

            # --- 2. Preview ---
            page.click('[data-page="preview"]')
            time.sleep(PAUSE + 1)  # preview needs to render

            # --- 3. Themes ---
            page.click('[data-page="themes"]')
            time.sleep(PAUSE)

            # --- 4. Build ---
            page.click('[data-page="build"]')
            time.sleep(PAUSE)
            page.click("#btn-build")
            time.sleep(PAUSE + 1)  # wait for build

            # --- 5. Export ---
            page.click('[data-page="export"]')
            time.sleep(PAUSE)

            # --- 6. AI Tools ---
            page.click('[data-page="ai"]')
            time.sleep(PAUSE)

            # --- 7. Settings ---
            page.click('[data-page="settings"]')
            time.sleep(PAUSE)

            # --- 8. Back to editor ---
            page.click('[data-page="editor"]')
            time.sleep(PAUSE)

            context.close()
            browser.close()

        # Find the recorded video
        videos = list(video_dir.glob("*.webm"))
        if not videos:
            raise RuntimeError("No video recorded")
        recorded = max(videos, key=lambda f: f.stat().st_mtime)
        shutil.move(str(recorded), str(output_video))
        print(f"Video saved: {output_video}")

    finally:
        server.terminate()
        server.wait()
        # Cleanup temp video dir
        shutil.rmtree(video_dir, ignore_errors=True)


def convert_to_gif(video_path: Path, gif_path: Path, fps: int = 12, width: int = 800) -> None:
    """Convert video to optimized GIF using ffmpeg."""
    palette = video_path.parent / "_palette.png"
    try:
        # Generate palette
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-i",
                str(video_path),
                "-vf",
                f"fps={fps},scale={width}:-1:flags=lanczos,palettegen=stats_mode=diff",
                str(palette),
            ],
            check=True,
            capture_output=True,
        )
        # Convert with palette
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-i",
                str(video_path),
                "-i",
                str(palette),
                "-lavfi",
                f"fps={fps},scale={width}:-1:flags=lanczos[x];[x][1:v]paletteuse=dither=bayer:bayer_scale=3",
                str(gif_path),
            ],
            check=True,
            capture_output=True,
        )
        print(f"GIF saved: {gif_path} ({gif_path.stat().st_size / 1_048_576:.1f} MB)")
    finally:
        palette.unlink(missing_ok=True)


# ---------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(description="Record resumake web UI screencast")
    parser.add_argument("--no-gif", action="store_true", help="Skip GIF conversion")
    parser.add_argument("--output", default="demo-web", help="Output filename (without extension)")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    docs_dir = repo_root / "docs"
    docs_dir.mkdir(exist_ok=True)
    output_video = docs_dir / f"{args.output}.webm"
    output_gif = docs_dir / f"{args.output}.gif"

    with tempfile.TemporaryDirectory(prefix="resumake-demo-") as tmpdir:
        project_dir = Path(tmpdir)
        print("Setting up demo project...")
        setup_demo_project(project_dir)
        # Copy icons from repo assets
        assets_src = repo_root / "resumake" / "assets"
        assets_dst = project_dir / "assets"
        for icon in assets_src.glob("icon_*.png"):
            shutil.copy2(icon, assets_dst / icon.name)

        print("Recording screencast...")
        record(project_dir, output_video)

    if not args.no_gif and shutil.which("ffmpeg"):
        print("Converting to GIF...")
        convert_to_gif(output_video, output_gif)
    elif not args.no_gif:
        print("ffmpeg not found — skipping GIF conversion")
        print(f"Convert manually: ffmpeg -i {output_video} {output_gif}")


if __name__ == "__main__":
    main()
