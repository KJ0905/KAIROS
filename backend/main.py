import hashlib
import hmac
import json
import os
import re
import secrets
import time
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from backend.ai_service import generate_answer
from backend.config import (
    FRONTEND_DIR,
    MAX_UPLOAD_MB,
    UPLOAD_DIR,
)
from backend.job_matcher import calculate_job_match
from backend.resume_parser import (
    categorize_urls,
    extract_pdf_links,
    extract_urls_from_text,
    parse_resume,
    read_pdf,
)
from backend.schemas import (
    AdminLoginRequest,
    ChatRequest,
    JobMatchRequest,
    NewConversationRequest,
    Resume,
)
from backend.storage import (
    CONVERSATIONS_DIR,
    PORTFOLIO_FILE,
    create_conversation,
    delete_portfolio,
    get_conversation,
    get_portfolio,
    save_conversation,
    save_portfolio,
)

app = FastAPI(title="AI Portfolio Chatbot")

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")
SESSION_SECRET = os.getenv("SESSION_SECRET", "")
SESSION_COOKIE = "portfolio_admin_session"
SESSION_DURATION = 8 * 60 * 60


def make_session_token() -> str:
    expiry = str(int(time.time()) + SESSION_DURATION)
    nonce = secrets.token_urlsafe(24)
    payload = f"{expiry}:{nonce}"
    signature = hmac.new(
        SESSION_SECRET.encode(),
        payload.encode(),
        hashlib.sha256,
    ).hexdigest()
    return f"{payload}:{signature}"


def is_admin(request: Request) -> bool:
    if not SESSION_SECRET:
        return False

    token = request.cookies.get(SESSION_COOKIE, "")
    parts = token.split(":")

    if len(parts) != 3:
        return False

    expiry, nonce, supplied_signature = parts

    if not expiry.isdigit() or int(expiry) < int(time.time()):
        return False

    payload = f"{expiry}:{nonce}"
    expected_signature = hmac.new(
        SESSION_SECRET.encode(),
        payload.encode(),
        hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(supplied_signature, expected_signature)


def require_admin(request: Request) -> None:
    if not is_admin(request):
        raise HTTPException(status_code=401, detail="Admin login required.")


def get_active_resume() -> Resume:
    portfolio = get_portfolio()

    if portfolio is None:
        raise HTTPException(
            status_code=404,
            detail="The portfolio resume has not been uploaded yet.",
        )

    try:
        return Resume.model_validate(portfolio["resume"])
    except (KeyError, ValueError):
        raise HTTPException(
            status_code=500,
            detail="The saved portfolio resume is invalid.",
        )


@app.get("/api/health")
def health_check():
    return {"status": "ok"}


@app.post("/api/admin/login")
def admin_login(credentials: AdminLoginRequest):
    if not ADMIN_USERNAME or not ADMIN_PASSWORD or not SESSION_SECRET:
        raise HTTPException(
            status_code=503,
            detail="Admin authentication is not configured.",
        )

    username_ok = hmac.compare_digest(
        credentials.username,
        ADMIN_USERNAME,
    )
    password_ok = hmac.compare_digest(
        credentials.password,
        ADMIN_PASSWORD,
    )

    if not (username_ok and password_ok):
        raise HTTPException(status_code=401, detail="Invalid credentials.")

    response = JSONResponse({"message": "Admin login successful."})
    response.set_cookie(
        key=SESSION_COOKIE,
        value=make_session_token(),
        httponly=True,
        secure=os.getenv("COOKIE_SECURE", "false").lower() == "true",
        samesite="strict",
        max_age=SESSION_DURATION,
        path="/",
    )
    return response


@app.post("/api/admin/logout")
def admin_logout():
    response = JSONResponse({"message": "Logged out."})
    response.delete_cookie(
        key=SESSION_COOKIE,
        path="/",
        httponly=True,
        samesite="strict",
        secure=os.getenv("COOKIE_SECURE", "false").lower() == "true",
    )
    return response


@app.get("/api/admin/status")
def admin_status(request: Request):
    return {"authenticated": is_admin(request)}


@app.get("/api/portfolio")
def public_portfolio():
    portfolio = get_portfolio()

    if portfolio is None:
        return {"available": False, "name": None, "skills": []}

    resume = portfolio.get("resume", {})
    return {
        "available": True,
        "name": resume.get("name"),
        "skills": resume.get("skills", []),
        "projects": resume.get("projects", []),
        "education": resume.get("education", []),
    }


@app.get("/api/admin/portfolio")
def admin_portfolio(request: Request):
    require_admin(request)
    portfolio = get_portfolio()

    if portfolio is None:
        return {"available": False}

    return {
        "available": True,
        "original_filename": portfolio.get("original_filename"),
        "resume": portfolio.get("resume"),
    }


@app.post("/api/admin/resume")
async def upload_resume(request: Request, file: UploadFile = File(...)):
    require_admin(request)

    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Please upload a PDF file.")

    content = await file.read()
    max_bytes = MAX_UPLOAD_MB * 1024 * 1024

    if len(content) > max_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File exceeds the {MAX_UPLOAD_MB} MB upload limit.",
        )

    if not content:
        raise HTTPException(status_code=400, detail="The uploaded file is empty.")

    safe_name = re.sub(r"[^A-Za-z0-9._-]", "_", Path(file.filename).name)
    saved_path = UPLOAD_DIR / f"{uuid4()}_{safe_name}"

    try:
        saved_path.write_bytes(content)
        resume_text = read_pdf(saved_path)

        if not resume_text.strip():
            raise ValueError("No readable text was found in the PDF.")

        pdf_links = extract_pdf_links(saved_path)
        resume = parse_resume(resume_text, pdf_links)

        visible_urls = extract_urls_from_text(resume_text)
        embedded_urls = extract_pdf_links(saved_path)

        all_urls = list(dict.fromkeys(visible_urls + embedded_urls))
        extracted_links = categorize_urls(all_urls)

        existing_links = resume.profile_links.model_dump()
        extracted_data = extracted_links.model_dump()

        for field in (
            "linkedin",
            "github",
            "codeforces",
            "codechef",
            "atcoder",
            "portfolio",
        ):
            if extracted_data[field]:
                existing_links[field] = extracted_data[field]

        existing_links["other_links"] = list(dict.fromkeys(
            existing_links.get("other_links", [])
            + extracted_data["other_links"]
        ))

        resume.profile_links = type(resume.profile_links).model_validate(
            existing_links
        )


        old_portfolio = get_portfolio()
        save_portfolio(resume, file.filename)

        if old_portfolio:
            old_name = Path(
                old_portfolio.get("original_filename", "")
            ).name
            for old_file in UPLOAD_DIR.iterdir():
                if (
                    old_file.is_file()
                    and old_file != saved_path
                    and old_file.name.endswith(f"_{old_name}")
                ):
                    old_file.unlink(missing_ok=True)

        return {
            "message": "Portfolio resume saved successfully.",
            "filename": file.filename,
            "resume": resume.model_dump(mode="json"),
        }

    except ValueError as exc:
        saved_path.unlink(missing_ok=True)
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        saved_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=500,
            detail="Could not process the resume. Check server logs.",
        ) from exc


@app.delete("/api/admin/resume")
def remove_resume(request: Request):
    require_admin(request)

    if not delete_portfolio():
        raise HTTPException(status_code=404, detail="No portfolio resume exists.")

    for path in CONVERSATIONS_DIR.glob("*.json"):
        path.unlink(missing_ok=True)

    return {"message": "Portfolio resume and conversation history deleted."}


@app.get("/api/resume")
def download_resume():
    portfolio = get_portfolio()

    if portfolio is None:
        raise HTTPException(status_code=404, detail="No portfolio resume exists.")

    filename = Path(
        portfolio.get("original_filename", "resume.pdf")
    ).name
    safe_name = re.sub(r"[^A-Za-z0-9._-]", "_", filename)

    for path in UPLOAD_DIR.iterdir():
        if path.is_file() and path.name.endswith(f"_{safe_name}"):
            return FileResponse(
                path,
                media_type="application/pdf",
                filename=safe_name,
            )

    raise HTTPException(status_code=404, detail="Resume PDF not found.")


@app.post("/api/conversations")
def new_conversation(request: NewConversationRequest):
    get_active_resume()
    return {"conversation_id": create_conversation()}


@app.post("/api/chat")
def chat(request: ChatRequest):
    resume = get_active_resume()
    conversation = get_conversation(request.conversation_id)

    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found.")

    history = conversation.get("messages", [])

    def stream_response():
        try:
            answer = generate_answer(
                resume=resume,
                conversation_history=history,
                question=request.question,
            )

            history.append({"role": "user", "content": request.question})
            history.append({"role": "assistant", "content": answer})
            conversation["messages"] = history
            save_conversation(conversation)

            for word in re.findall(r"\S+\s*", answer):
                yield f"data: {json.dumps({'text': word})}\n\n"

            yield "data: [DONE]\n\n"

        except Exception:
            yield (
                f"data: {json.dumps({'error': 'Could not generate an answer.'})}\n\n"
            )

    return StreamingResponse(
        stream_response(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@app.post("/api/job-match")
def job_match(request: JobMatchRequest):
    resume = get_active_resume()
    return calculate_job_match(resume, request.job_description)

@app.get("/api/portfolio/resume")
def view_current_resume():
    resume_path = Path("backend/my_resume.pdf")

    if not resume_path.exists():
        raise HTTPException(status_code=404, detail="Resume not found")

    return FileResponse(
        path=resume_path,
        media_type="application/pdf",
        filename="my_resume.pdf",
        content_disposition_type="inline",
    )


if FRONTEND_DIR.exists():
    app.mount(
        "/",
        StaticFiles(directory=FRONTEND_DIR, html=True),
        name="frontend",
    )

