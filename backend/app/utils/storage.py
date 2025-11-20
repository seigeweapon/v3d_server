from pathlib import Path
from typing import BinaryIO

UPLOAD_DIR = Path("storage/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def save_file(filename: str, file_data: BinaryIO) -> str:
    destination = UPLOAD_DIR / filename
    with open(destination, "wb") as f:
        f.write(file_data.read())
    return str(destination)
