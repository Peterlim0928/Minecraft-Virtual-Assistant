from parser import ContentItem
from typing import TypedDict


class ChunkType(TypedDict):
    text: str
    metadata: dict[str, str]


def chunk_page(title: str, url: str, content: list[ContentItem], max_length: int = 512) -> list[ChunkType]:
    """
    Chunk a parsed page into smaller sections for embedding.
    Each chunk contains metadata: title, url, section, and text.
    """
    chunks = []

    for block in content:
        # For paragraphs and lists, chunk directly
        if block["type"] == "paragraph":
            chunks.append(
                {
                    "text": f"[{title} | {block['section']}]\n{block['text']}",
                    "metadata": {
                        "title": title,
                        "url": url,
                        "section": block["section"],
                        "content_type": "paragraph",
                    },
                }
            )
        elif block["type"] == "list":
            # Combine list items into one chunk (or split if too long)
            list_text = "\n".join(block["items"])
            chunks.append(
                {
                    "text": f"[{title} | {block['section']}]\n{list_text}",
                    "metadata": {
                        "title": title,
                        "url": url,
                        "section": block["section"],
                        "content_type": "list",
                    },
                }
            )
        elif block["type"] == "table":
            # Flatten table rows for embedding
            table_text = "\n".join([" | ".join(row) for row in block["data"]])
            chunks.append(
                {
                    "text": f"[{title} | {block['section']}]\n{table_text}",
                    "metadata": {
                        "title": title,
                        "url": url,
                        "section": block["section"],
                        "content_type": "table",
                    },
                }
            )
        elif block["type"] == "infobox":
            # Flatten infobox key-value pairs
            infobox_text = "\n".join([f"{k}: {v}" for k, v in block["data"].items()])
            chunks.append(
                {
                    "text": f"[{title} | {block['section']}]\n{infobox_text}",
                    "metadata": {
                        "title": title,
                        "url": url,
                        "section": block["section"],
                        "content_type": "infobox",
                    },
                }
            )
        elif block["type"] == "droptable":
            # Flatten droptable key-value pairs
            droptable_text = "\n\n".join("\n".join(" | ".join(row) for row in table) for table in block["data"])
            chunks.append(
                {
                    "text": f"[{title} | {block['section']}]\n{droptable_text.strip()}",
                    "metadata": {
                        "title": title,
                        "url": url,
                        "section": block["section"],
                        "content_type": "droptable",
                    },
                }
            )
        elif block["type"] == "calculator_table":
            # Flatten calculator table key-value pairs
            calculator_table_text = "\n".join([" | ".join(row) for row in block["data"]])

            lines = []
            for name, p in block["parameters"].items():
                if p["type"] == "slider":
                    lines.append(f"{name} (slider): {p['min']}–{p['max']} options: {', '.join(p['options'])}")
                elif p["type"] == "radio":
                    lines.append(f"{name} (radio): {', '.join(p['options'])}")
            params_text = "\n".join(lines)

            chunks.append(
                {
                    "text": f"[{title} | {block['section']}]\n{calculator_table_text}\nParameters: {params_text}",
                    "metadata": {
                        "title": title,
                        "url": url,
                        "section": block["section"],
                        "content_type": "calculator_table",
                    },
                }
            )
        # NOTE: Can extend this for other block types as needed
        # Only need to extend if parser.py adds new block types

    # Optionally, split chunks further if text is too long for your embedding model
    # NOTE: KIV - implement smarter splitting if needed
    final_chunks = []
    for chunk in chunks:
        text = chunk["text"]
        if len(text) > max_length:
            # Simple split by sentences or lines
            lines = text.split("\n")
            buffer = []
            for line in lines:
                buffer.append(line)
                if sum(len(l) for l in buffer) > max_length:
                    final_chunks.append({**chunk, "text": "\n".join(buffer)})
                    buffer = []
            if buffer:
                final_chunks.append({**chunk, "text": "\n".join(buffer)})
        else:
            final_chunks.append(chunk)

    return final_chunks


# Example usage:
# parsed = ... # Load your parsed ContentItem
# chunks = chunk_page(parsed)
# for chunk in chunks:
#     print(chunk["section"], chunk["content_type"], chunk["text"][:100])
