"""Submission Manager - Save, load, and list transaction submissions."""

import json
import logging
import os
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

from tools.data_adapter import normalize_transaction, denormalize_transaction

logger = logging.getLogger(__name__)

SUBMISSIONS_DIR = Path("submissions")


def _sanitize_dirname(name: str) -> str:
    """Create a filesystem-safe directory name from Hebrew/English text."""
    # Keep Hebrew, English, digits, underscores
    safe = re.sub(r"[^\w\u0590-\u05FF]", "_", name)
    # Collapse multiple underscores
    safe = re.sub(r"_+", "_", safe).strip("_")
    return safe[:50] if safe else "unnamed"


def save_submission(
    client_data: dict,
    uploaded_files: dict = None,
    base_dir: Path = SUBMISSIONS_DIR,
) -> str:
    """Save a transaction submission to disk.

    Args:
        client_data: Transaction data (flat or nested format).
        uploaded_files: Dict of {category: file_bytes_or_list}.
        base_dir: Base directory for submissions.

    Returns:
        Path to the saved submission directory.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Build directory name from property address or seller name
    address = (
        client_data.get("property_address", "")
        or client_data.get("property", {}).get("address", "")
        or "unknown"
    )
    dir_name = f"transaction_{_sanitize_dirname(address)}_{timestamp}"
    submission_dir = base_dir / dir_name
    submission_dir.mkdir(parents=True, exist_ok=True)

    # Save transaction data in nested format
    nested = denormalize_transaction(client_data) if "seller_name" in client_data else client_data
    data_path = submission_dir / f"{dir_name}.json"
    with open(data_path, "w", encoding="utf-8") as f:
        json.dump(nested, f, ensure_ascii=False, indent=2)

    # Save uploaded files
    if uploaded_files:
        files_dir = submission_dir / f"files_{dir_name}"
        files_dir.mkdir(exist_ok=True)

        for category, files in uploaded_files.items():
            if files is None:
                continue
            if not isinstance(files, list):
                files = [files]
            for file_obj in files:
                if hasattr(file_obj, "name") and hasattr(file_obj, "read"):
                    # Streamlit UploadedFile
                    file_path = files_dir / file_obj.name
                    with open(file_path, "wb") as f:
                        f.write(file_obj.read())
                        file_obj.seek(0)
                elif isinstance(file_obj, (str, Path)) and os.path.exists(file_obj):
                    shutil.copy2(file_obj, files_dir)

    return str(submission_dir)


def load_submission(submission_path: str) -> dict:
    """Load a submission and return normalized (flat) data.

    Args:
        submission_path: Path to submission directory or JSON file.

    Returns:
        Dict with keys: data (flat), nested_data, files (list of paths), path.
    """
    path = Path(submission_path)

    # Find the JSON file
    if path.is_file() and path.suffix == ".json":
        json_path = path
        sub_dir = path.parent
    elif path.is_dir():
        json_files = list(path.glob("*.json"))
        if not json_files:
            raise FileNotFoundError(f"No JSON file found in {path}")
        json_path = json_files[0]
        sub_dir = path
    else:
        raise FileNotFoundError(f"Submission not found: {submission_path}")

    with open(json_path, "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    flat_data = normalize_transaction(raw_data)

    # Find associated files
    file_dirs = list(sub_dir.glob("files_*"))
    files = []
    for fd in file_dirs:
        files.extend([str(p) for p in fd.iterdir() if p.is_file()])

    return {
        "data": flat_data,
        "nested_data": raw_data,
        "files": files,
        "path": str(sub_dir),
        "json_path": str(json_path),
    }


def list_submissions(base_dir: Path = SUBMISSIONS_DIR) -> list:
    """List all saved submissions.

    Returns:
        List of dicts with keys: name, path, timestamp, summary.
    """
    if not base_dir.exists():
        return []

    submissions = []
    for entry in sorted(base_dir.iterdir(), reverse=True):
        if not entry.is_dir() or entry.name.startswith("."):
            continue

        json_files = list(entry.glob("*.json"))
        if not json_files:
            continue

        try:
            with open(json_files[0], "r", encoding="utf-8") as f:
                data = json.load(f)

            # Extract summary
            if "sellers" in data:
                seller = data["sellers"][0]["name"] if data.get("sellers") else "?"
                buyer = data["buyers"][0]["name"] if data.get("buyers") else "?"
                address = data.get("property", {}).get("address", "?")
                price = data.get("transaction", {}).get("price", 0)
            else:
                seller = data.get("seller_name", "?")
                buyer = data.get("buyer_name", "?")
                address = data.get("property_address", "?")
                price = data.get("price", 0)

            # Extract timestamp from directory name
            ts_match = re.search(r"(\d{8}_\d{6})$", entry.name)
            timestamp = ts_match.group(1) if ts_match else ""

            submissions.append({
                "name": entry.name,
                "path": str(entry),
                "json_path": str(json_files[0]),
                "timestamp": timestamp,
                "seller": seller,
                "buyer": buyer,
                "address": address,
                "price": price,
            })
        except (json.JSONDecodeError, KeyError):
            continue

    return submissions


def upload_submission_to_drive(
    client_data: dict,
    uploaded_files: dict = None,
    artifacts_dir: str = "artifacts",
) -> dict:
    """Upload a transaction submission and its artifacts to Google Drive.

    Uses the existing drive_service.py (OAuth2).

    Args:
        client_data: Transaction data (flat or nested).
        uploaded_files: Dict of {category: file_bytes_or_list} from Streamlit.
        artifacts_dir: Path to the artifacts directory with generated contracts.

    Returns:
        Dict with folder_id, folder_link, and files_uploaded count.
    """
    from drive_service import (
        create_transaction_folder,
        upload_json,
        upload_bytes,
        upload_file,
    )

    # Determine property address for folder name
    address = (
        client_data.get("property_address", "")
        or client_data.get("property", {}).get("address", "")
        or "עסקה_ללא_כתובת"
    )

    # Create Drive folder
    logger.info(f"יוצר תיקייה בגוגל דרייב: {address}")
    folder_info = create_transaction_folder(address)
    folder_id = folder_info["folder_id"]

    files_uploaded = 0

    # Upload transaction JSON
    nested = denormalize_transaction(client_data) if "seller_name" in client_data else client_data
    upload_json(nested, "transaction_data.json", folder_id)
    files_uploaded += 1
    logger.info("הועלה: transaction_data.json")

    # Upload attached documents (Streamlit UploadedFile objects)
    if uploaded_files:
        for category, files in uploaded_files.items():
            if files is None:
                continue
            if not isinstance(files, list):
                files = [files]
            for i, f in enumerate(files):
                if hasattr(f, "name") and hasattr(f, "read"):
                    f.seek(0)
                    file_name = f"{category}_{i + 1}_{f.name}"
                    upload_bytes(f.read(), file_name, folder_id)
                    files_uploaded += 1
                    logger.info(f"הועלה: {file_name}")

    # Upload generated contracts and reports from artifacts/
    artifacts_path = Path(artifacts_dir)
    if artifacts_path.exists():
        for artifact in artifacts_path.iterdir():
            if artifact.is_file() and artifact.suffix in (
                ".docx", ".csv", ".json", ".html", ".md",
            ):
                upload_file(str(artifact), folder_id)
                files_uploaded += 1
                logger.info(f"הועלה: {artifact.name}")

    logger.info(f"העלאה ל-Drive הושלמה: {files_uploaded} קבצים -> {folder_info['folder_link']}")

    return {
        "folder_id": folder_id,
        "folder_link": folder_info["folder_link"],
        "folder_name": folder_info["folder_name"],
        "files_uploaded": files_uploaded,
    }
