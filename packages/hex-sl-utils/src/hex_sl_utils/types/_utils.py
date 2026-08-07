def clean_doc_comment(doc: str | None) -> str:
    """Clean a doc comment for use as a JSON Schema description."""
    if not doc:
        return ""

    result = ""
    for line in doc.strip().split("\n"):
        result += "\n" if not line.strip() else line.strip() + " "
    return result
