import requests
import gzip
import logging
import time
from urllib.robotparser import RobotFileParser
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET

# Configure logging to write to file
logging.basicConfig(
    filename="output.txt",
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
    filemode="w",  # 'w' to overwrite, 'a' to append
)

SITEMAP_URL = "https://minecraft.wiki/images/sitemaps/index.xml"

HEADERS = {"User-Agent": "FriendlyResearchBot/1.0 (contact: limjiantao@gmail.com)"}

CRAWL_DELAY = 1  # seconds


def fetch_sitemap_index(url) -> list[ET.Element]:
    """Fetch and parse the sitemap index XML."""
    logging.info(f"Fetching sitemap index from {url}")
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "xml")
    return soup.find_all("loc")


def fetch_sitemap(url) -> ET.Element:
    """Fetch and decompress a gzipped sitemap file."""
    logging.info(f"Fetching sitemap: {url}")
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    data = gzip.decompress(response.content)
    return ET.fromstring(data)


def extract_urls_from_sitemap(root, robot_parser) -> list[str]:
    """Extract URLs from a sitemap XML root, filtering by robots.txt rules."""
    urls = []
    for url in root.findall("{http://www.sitemaps.org/schemas/sitemap/0.9}url"):
        loc = url.find("{http://www.sitemaps.org/schemas/sitemap/0.9}loc").text

        # Check if URL is allowed by robots.txt
        if robot_parser.can_fetch("*", loc):
            urls.append(loc)
        else:
            logging.warning(f"Skipped (disallowed by robots.txt): {loc}")

    return urls


def save_urls_to_file(urls, filename) -> None:
    """Save a list of URLs to a text file."""
    with open(filename, "w", encoding="utf-8") as f:
        for url in urls:
            f.write(url + "\n")
    logging.info(f"Saved {len(urls)} URLs to {filename}")


def collect_all_urls() -> list[str]:
    """Collect all URLs from Minecraft Wiki sitemaps (run once per month)."""
    # Parse robots.txt
    rp = RobotFileParser()
    rp.set_url("https://minecraft.wiki/robots.txt")
    rp.read()

    logging.info("Starting URL collection from sitemaps...")

    # Fetch the sitemap index
    sitemap_locations = fetch_sitemap_index(SITEMAP_URL)

    all_urls = []

    # Process all sitemaps
    for sitemap_loc in sitemap_locations:
        root = fetch_sitemap(sitemap_loc.string)
        urls = extract_urls_from_sitemap(root, rp)
        all_urls.extend(urls)

        # Small delay between sitemap files to be polite
        time.sleep(0.1)

    return all_urls


def filter_urls(urls: list[str], blacklist: list[str]) -> list[str]:
    """Filter out URLs that contains any of the specified keywords."""
    filtered = []
    for url in urls:
        if any(keyword in url for keyword in blacklist):
            logging.info(f"Filtered out URL: {url}")
        else:
            filtered.append(url)
    logging.info(f"Filtered URLs count: {len(filtered)}")
    return filtered


def fetch_page(url) -> str:
    r = requests.get(url, headers=HEADERS, timeout=10)
    r.raise_for_status()
    return r.text


if __name__ == "__main__":
    urls = collect_all_urls()
    blacklist = [
        "Bedrock_Edition",
        "Bedrock_Editor",
        "Calculators",
        "Character_Creator",
        "Education_Edition",
        "LEGO_Minecraft",
        "Launcher",
        "Console",
        "MinecraftEdu",
        "Minecraft_",
        "Nintendo",
        "PlayStation",
        "Pocket_Edition",
        "Technical_blocks",
        "Wii",
        "Xbox",
        "Talk:",
        "Minecraft_Wiki:",
        "MediaWiki:",
        "Template:",
        "Category",
        "Module:",
        "Dungeons:",
        "Earth:",
        "Story_Mode:",
        "Legends:",
        "Forum:",
        "Tutorial:",
        "Movie",
        "talk:",
    ]
    filtered_urls = filter_urls(urls, blacklist)
    save_urls_to_file(filtered_urls, "minecraft_urls.txt")
