import os
import re
from typing import List, Dict, Any


def load_knowledge_base_documents(knowledge_base_dir: str) -> List[Dict[str, Any]]:
    """
    Recursively scans and loads markdown and text documents from knowledge_base_dir.
    Extracts header metadata (Document Type, Supplier, Version, etc.)
    """
    if not os.path.exists(knowledge_base_dir):
        raise FileNotFoundError(f"Knowledge base directory not found at {knowledge_base_dir}")

    loaded_documents = []

    for root, _, files in os.walk(knowledge_base_dir):
        for file in files:
            if file.endswith(".md") or file.endswith(".txt"):
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, knowledge_base_dir)
                
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                # Determine default document_type from folder name if not in header
                folder_type = os.path.basename(root)

                # Parse simple inline metadata key-values from document top header
                meta = {
                    "document_name": file,
                    "relative_path": rel_path,
                    "document_type": folder_type,
                    "source": "synthetic"
                }

                doc_type_match = re.search(r"\*\*Document Type\*\*:\s*(.+)", content)
                if doc_type_match:
                    meta["document_type"] = doc_type_match.group(1).strip()

                supplier_match = re.search(r"\*\*Supplier\*\*:\s*(.+)", content)
                if supplier_match:
                    meta["supplier"] = supplier_match.group(1).strip()

                version_match = re.search(r"\*\*Version\*\*:\s*(.+)", content)
                if version_match:
                    meta["version"] = version_match.group(1).strip()

                loaded_documents.append({
                    "document_name": file,
                    "document_type": meta["document_type"],
                    "content": content,
                    "metadata": meta
                })

    return loaded_documents
