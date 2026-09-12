import re
from typing import List, Dict, Any


def chunk_document(
    doc: Dict[str, Any],
    chunk_size_words: int = 250,
    overlap_words: int = 40
) -> List[Dict[str, Any]]:
    """
    Splits document text into semantic section-aware chunks (~250-400 words)
    with word overlap, capturing section heading titles in metadata.
    """
    content = doc["content"]
    doc_name = doc["document_name"]
    doc_type = doc["document_type"]
    base_meta = doc.get("metadata", {})

    # Split document by markdown section headings (## Heading)
    sections = re.split(r"(?=\n##\s+)", content)
    chunks = []
    chunk_idx = 1

    for sec in sections:
        sec_text = sec.strip()
        if not sec_text:
            continue

        # Extract Section Title if available
        sec_title_match = re.match(r"^##\s+(.+)", sec_text)
        sec_title = sec_title_match.group(1).strip() if sec_title_match else "General Terms"

        words = sec_text.split()
        if len(words) <= chunk_size_words:
            chunk_meta = dict(base_meta)
            chunk_meta["section"] = sec_title
            chunk_meta["chunk_index"] = chunk_idx

            chunks.append({
                "document_name": doc_name,
                "document_type": doc_type,
                "chunk_index": chunk_idx,
                "content": sec_text,
                "metadata": chunk_meta
            })
            chunk_idx += 1
        else:
            # Sub-chunk longer sections with sliding word window overlap
            start = 0
            while start < len(words):
                end = min(start + chunk_size_words, len(words))
                sub_words = words[start:end]
                sub_text = " ".join(sub_words)

                chunk_meta = dict(base_meta)
                chunk_meta["section"] = sec_title
                chunk_meta["chunk_index"] = chunk_idx

                chunks.append({
                    "document_name": doc_name,
                    "document_type": doc_type,
                    "chunk_index": chunk_idx,
                    "content": sub_text,
                    "metadata": chunk_meta
                })
                chunk_idx += 1

                if end == len(words):
                    break
                start += (chunk_size_words - overlap_words)

    return chunks
