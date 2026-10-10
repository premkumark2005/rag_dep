"""Load source documents for ingestion."""

from pathlib import Path

from backend.models.schemas import Document
from backend.utils.exceptions import IngestionError


def load_txt_documents(data_directory: Path) -> list[Document]:
    """Load all .txt documents from a directory."""
    if not data_directory.exists():
        raise IngestionError(f"Data directory does not exist: {data_directory}")

    txt_files = sorted(data_directory.glob("*.txt"))
    if not txt_files:
        raise IngestionError(f"No .txt files found in {data_directory}")

    documents: list[Document] = []
    for index, path in enumerate(txt_files, start=1):
        text = path.read_text(encoding="utf-8").strip()
        if not text:
            continue
        documents.append(
            Document(
                document_id=f"doc_{index:03d}",
                title=path.stem,
                text=text,
                source=str(path.resolve()),
            )
        )

    if not documents:
        raise IngestionError("All discovered .txt files were empty.")
    return documents

