import time
import os

from parser import MinecraftWikiParser
from chunking import chunk_page

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))


def collect_and_parse():
    with open("minecraft_urls.txt", "r", encoding="utf-8") as f:
        urls = [line.strip() for line in f.readlines()]

    for url in urls:
        parser = MinecraftWikiParser(url)
        parser.save_to_file(os.path.join(ROOT_DIR, "json"))
        time.sleep(0.1)  # Be polite with a small delay


def load_and_chunk():
    source_folder = os.path.join(ROOT_DIR, "json")
    dest_folder = os.path.join(ROOT_DIR, "chunks")
    for filename in os.listdir(source_folder):
        if not filename.endswith(".json"):
            continue
        file_path = os.path.join(source_folder, filename)
        parser = MinecraftWikiParser.load_from_file(file_path)
        chunks = chunk_page(parser.title, parser.url, parser.content)

        # Save chunks to a file or process further
        with open(os.path.join(dest_folder, f"{filename}"), "w", encoding="utf-8") as f:
            import json

            json.dump(chunks, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    load_and_chunk()
