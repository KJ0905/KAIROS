import json
from pathlib import Path
from uuid import uuid4

from backend.config import DATA_DIR, UPLOAD_DIR
from backend.schemas import Resume, PersonalProfile

PERSONAL_PROFILE_FILE = DATA_DIR / "personal_profile.json"
PORTFOLIO_FILE = DATA_DIR / "portfolio.json"
RESUME_FILE = DATA_DIR / "portfolio_resume.json"
CONVERSATIONS_DIR = DATA_DIR / "conversations"

CONVERSATIONS_DIR.mkdir(parents=True, exist_ok=True)


def get_portfolio() -> dict | None:
    if not PORTFOLIO_FILE.exists():
        return None

    try:
        return json.loads(PORTFOLIO_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def save_portfolio(resume: Resume, original_filename: str) -> dict:
    portfolio = {
        "resume": resume.model_dump(mode="json"),
        "original_filename": original_filename,
    }

    temporary_file = PORTFOLIO_FILE.with_suffix(".tmp")
    temporary_file.write_text(
        json.dumps(portfolio, indent=2),
        encoding="utf-8",
    )
    temporary_file.replace(PORTFOLIO_FILE)

    return portfolio


def delete_portfolio() -> bool:
    portfolio = get_portfolio()

    if portfolio is None:
        return False

    original_filename = portfolio.get("original_filename", "")
    PORTFOLIO_FILE.unlink(missing_ok=True)
    RESUME_FILE.unlink(missing_ok=True)

    safe_name = Path(original_filename).name

    for path in UPLOAD_DIR.iterdir():
        if path.is_file() and path.name.endswith(f"_{safe_name}"):
            path.unlink(missing_ok=True)

    return True


def create_conversation() -> str:
    conversation_id = str(uuid4())

    conversation_data = {
        "conversation_id": conversation_id,
        "messages": [],
    }

    file_path = CONVERSATIONS_DIR / f"{conversation_id}.json"
    file_path.write_text(
        json.dumps(conversation_data, indent=2),
        encoding="utf-8",
    )

    return conversation_id


def get_conversation(conversation_id: str) -> dict | None:
    file_path = CONVERSATIONS_DIR / f"{conversation_id}.json"

    if not file_path.exists():
        return None

    try:
        return json.loads(file_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def save_conversation(conversation: dict) -> None:
    conversation_id = conversation["conversation_id"]
    file_path = CONVERSATIONS_DIR / f"{conversation_id}.json"

    file_path.write_text(
        json.dumps(conversation, indent=2),
        encoding="utf-8",
    )


def get_personal_profile() -> PersonalProfile:
    if not PERSONAL_PROFILE_FILE.exists():
        return PersonalProfile()

    try:
        data = json.loads(
            PERSONAL_PROFILE_FILE.read_text(encoding="utf-8")
        )
        return PersonalProfile.model_validate(data)

    except (json.JSONDecodeError, OSError, ValueError):
        return PersonalProfile()


def save_personal_profile(profile: PersonalProfile) -> dict:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    data = profile.model_dump(mode="json")

    temporary_file = PERSONAL_PROFILE_FILE.with_suffix(".tmp")
    temporary_file.write_text(
        json.dumps(data, indent=2),
        encoding="utf-8",
    )
    temporary_file.replace(PERSONAL_PROFILE_FILE)

    return data


def delete_personal_profile() -> bool:
    if not PERSONAL_PROFILE_FILE.exists():
        return False

    PERSONAL_PROFILE_FILE.unlink()
    return True
