from __future__ import annotations

"""FastAPI entrypoint for the examination document-processing workflow."""

import mimetypes
import importlib.util
import os
from pathlib import Path
from typing import Any, Literal
from uuid import uuid4

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from full_pipeline import process_file_to_question_results
from template_builder.service import build_template_draft
from template_registry.service import (
    TEMPLATE_ROOT,
    TemplateNotBoundError,
    bind_exam_template,
    create_exam,
    get_exam,
    get_exam_questions,
    get_template,
    list_exams,
    publish_template,
    review_template,
    set_exam_status,
)


app = FastAPI(title="Exam Document Processing API", version="2.0.0")
TEMPLATE_ROOT.mkdir(parents=True, exist_ok=True)
app.mount("/api/template-assets", StaticFiles(directory=str(TEMPLATE_ROOT)), name="template-assets")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[item.strip() for item in os.getenv("EXAM_API_CORS_ORIGINS", "http://localhost:3000,http://localhost:5173").split(",") if item.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ExamCreateRequest(BaseModel):
    exam_id: str = Field(min_length=1, max_length=128)
    exam_name: str = Field(min_length=1, max_length=256)
    status: Literal["draft", "published"] = "draft"


class TemplateReviewRequest(BaseModel):
    pages: list[dict[str, Any]]
    publish: bool = False


class BindTemplateRequest(BaseModel):
    template_id: str


class ExamStatusRequest(BaseModel):
    status: Literal["draft", "published"]


@app.get("/health")
def health() -> dict[str, Any]:
    dependencies = {
        "paddleocr": _module_available("paddleocr"),
        "paddlepaddle": _module_available("paddle"),
        "opencv": _module_available("cv2"),
    }
    return {
        "status": "ok" if dependencies["paddleocr"] and dependencies["paddlepaddle"] else "degraded",
        "dependencies": dependencies,
    }


@app.post("/api/exams", status_code=201)
def create_exam_endpoint(payload: ExamCreateRequest) -> dict[str, Any]:
    return _run_or_http(lambda: create_exam(payload.exam_id, payload.exam_name, payload.status))


@app.get("/api/exams")
def list_exams_endpoint() -> list[dict[str, Any]]:
    return list_exams()


@app.get("/api/exams/{exam_id}")
def get_exam_endpoint(exam_id: str) -> dict[str, Any]:
    return _run_or_http(lambda: get_exam(exam_id))


@app.get("/api/exams/{exam_id}/questions")
def get_exam_questions_endpoint(exam_id: str) -> list[dict[str, Any]]:
    return _run_or_http(lambda: get_exam_questions(exam_id))


@app.patch("/api/exams/{exam_id}/status")
def set_exam_status_endpoint(exam_id: str, payload: ExamStatusRequest) -> dict[str, Any]:
    return _run_or_http(lambda: set_exam_status(exam_id, payload.status))


@app.post("/api/templates/drafts", status_code=201)
async def create_template_draft_endpoint(
    file: UploadFile = File(...),
    template_id: str = Form(...),
    template_name: str = Form(...),
    version: int = Form(...),
    exam_id: str = Form(...),
) -> dict[str, Any]:
    source_path, mime_type = await _save_upload(file, "template_uploads")
    template = _run_or_http(lambda: build_template_draft(template_id, template_name, source_path, mime_type, version, exam_id))
    return {"template": template, "review_required": True}


@app.get("/api/templates/{template_id}")
def get_template_endpoint(template_id: str) -> dict[str, Any]:
    return _run_or_http(lambda: get_template(template_id))


@app.put("/api/templates/{template_id}/review")
def review_template_endpoint(template_id: str, payload: TemplateReviewRequest) -> dict[str, Any]:
    template = _run_or_http(lambda: review_template(template_id, payload.pages, payload.publish))
    return {"template": template}


@app.post("/api/templates/{template_id}/publish")
def publish_template_endpoint(template_id: str) -> dict[str, Any]:
    template = _run_or_http(lambda: publish_template(template_id))
    return {"template": template}


@app.post("/api/exams/{exam_id}/template")
def bind_template_endpoint(exam_id: str, payload: BindTemplateRequest) -> dict[str, Any]:
    return _run_or_http(lambda: bind_exam_template(exam_id, payload.template_id))


@app.post("/api/process")
async def process_document_endpoint(
    file: UploadFile = File(...),
    document_role: Literal["question_paper", "answer_sheet"] = Form(...),
    exam_id: str | None = Form(None),
    submission_id: str | None = Form(None),
) -> dict[str, Any]:
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")
    origin_name = file.filename or "upload.bin"
    mime_type = _guess_mime_type(origin_name, file.content_type)
    try:
        return process_file_to_question_results(
            submission_id=submission_id or f"sub_{uuid4().hex[:12]}",
            origin_name=origin_name,
            mime_type=mime_type,
            file_size=len(content),
            file_bytes=content,
            exam_id=exam_id,
            document_role=document_role,
        )
    except TemplateNotBoundError as exc:
        raise HTTPException(status_code=422, detail={"error_code": "TEMPLATE_NOT_BOUND", "message": str(exc)}) from exc
    except (ValueError, FileNotFoundError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise _runtime_http_exception(exc) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


async def _save_upload(file: UploadFile, folder_name: str) -> tuple[Path, str]:
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")
    origin_name = file.filename or "upload.bin"
    mime_type = _guess_mime_type(origin_name, file.content_type)
    extension = Path(origin_name).suffix.lower() or _extension_for_mime_type(mime_type)
    target_dir = Path("storage") / folder_name
    target_dir.mkdir(parents=True, exist_ok=True)
    path = target_dir / f"{uuid4().hex}{extension}"
    path.write_bytes(content)
    return path, mime_type


def _guess_mime_type(origin_name: str, supplied: str | None) -> str:
    allowed = {
        ".pdf": "application/pdf", ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png",
    }
    if Path(origin_name).suffix.lower() in allowed:
        return allowed[Path(origin_name).suffix.lower()]
    if supplied:
        return supplied
    guessed, _ = mimetypes.guess_type(origin_name)
    if guessed:
        return guessed
    raise HTTPException(status_code=400, detail="Unsupported file type")


def _extension_for_mime_type(mime_type: str) -> str:
    return {"application/pdf": ".pdf", "image/jpeg": ".jpg", "image/png": ".png"}.get(mime_type, ".bin")


def _run_or_http(operation):
    try:
        return operation()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise _runtime_http_exception(exc) from exc


def _runtime_http_exception(exc: RuntimeError) -> HTTPException:
    message = str(exc)
    if "PaddleOCR" in message or "paddleocr" in message or "paddlepaddle" in message:
        return HTTPException(
            status_code=503,
            detail={
                "error_code": "OCR_DEPENDENCY_MISSING",
                "message": message,
                "hint": "Use a Python runtime supported by PaddlePaddle, then install paddlepaddle and paddleocr.",
            },
        )
    return HTTPException(status_code=500, detail=message)


def _module_available(name: str) -> bool:
    return importlib.util.find_spec(name) is not None
