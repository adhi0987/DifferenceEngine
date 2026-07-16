"""Phase 2 AI APIs (design section 10.8) — submission, processing, retrieval.

Pipeline (mirrors design sequence 12.5):
  upload image -> store -> OCR extract text -> concept extraction (T5/heuristic)
  -> recommend resources for missing concepts -> persist feedback.

Processing runs as a FastAPI background task so the POST returns immediately with
``queued`` status, matching the documented contract.
"""
from __future__ import annotations

import json

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    HTTPException,
    UploadFile,
    status,
)
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import SessionLocal, get_db
from ..deps import require_roles
from ..services import audit, concepts, ocr, recommend, storage

router = APIRouter(tags=["ai"])


def _process_submission(submission_id: str) -> None:
    """Background worker: OCR -> concepts -> recommendations -> persist."""
    db = SessionLocal()
    try:
        submission = db.get(models.AiSubmission, submission_id)
        if submission is None:
            return
        submission.processing_status = "processing"
        db.commit()

        path = storage.resolve_path(submission.image_file_url)
        text, engine = ocr.extract_text(path)

        analysis = concepts.detect_concepts(text)
        recommended = recommend.recommend(
            db,
            submission.course_id,
            analysis.get("inferredTopic"),
            analysis.get("missingConcepts", []),
        )

        feedback = {
            "conceptCoverageScore": analysis["conceptCoverageScore"],
            "inferredTopic": analysis["inferredTopic"],
            "detectedConcepts": analysis["detectedConcepts"],
            "missingConcepts": analysis["missingConcepts"],
            "recommendedResources": recommended,
            "modelSummary": analysis.get("modelSummary"),
            "ocrEngine": engine,
        }

        submission.extracted_text = text
        submission.model_feedback = json.dumps(feedback)
        submission.processing_status = "completed"
        audit.record(
            db, submission.student_id, "AI_SUBMISSION_PROCESSED",
            "ai_submission", submission.id,
        )
        db.commit()
    except Exception:
        db.rollback()
        submission = db.get(models.AiSubmission, submission_id)
        if submission is not None:
            submission.processing_status = "failed"
            db.commit()
    finally:
        db.close()


@router.post(
    "/student/ai/uploads",
    response_model=schemas.ApiResponse[dict],
    status_code=status.HTTP_201_CREATED,
)
async def upload_file(
    file: UploadFile = File(...),
    user: models.User = Depends(require_roles("student")),
):
    """Upload an image/transcript and receive a ``storage://`` URI to submit."""
    data = await file.read()
    uri = storage.save_bytes(data, file.filename or "upload.png")
    return schemas.ApiResponse(
        message="File uploaded", data={"imageFileUrl": uri}
    )


@router.post(
    "/student/ai/submissions",
    response_model=schemas.ApiResponse[schemas.AiSubmissionCreated],
    status_code=status.HTTP_201_CREATED,
)
def create_submission(
    body: schemas.AiSubmissionRequest,
    background: BackgroundTasks,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_roles("student")),
):
    if not db.get(models.Course, body.courseId):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid courseId")
    if body.sessionId and not db.get(models.ClassSession, body.sessionId):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid sessionId")

    submission = models.AiSubmission(
        student_id=user.id,
        course_id=body.courseId,
        session_id=body.sessionId,
        image_file_url=body.imageFileUrl,
        processing_status="queued",
    )
    db.add(submission)
    db.flush()
    audit.record(db, user.id, "AI_SUBMISSION_CREATED", "ai_submission", submission.id)
    db.commit()

    background.add_task(_process_submission, submission.id)

    return schemas.ApiResponse(
        message="AI submission received",
        data=schemas.AiSubmissionCreated(
            submissionId=submission.id, processingStatus=submission.processing_status
        ),
    )


@router.get(
    "/student/ai/submissions/{submission_id}",
    response_model=schemas.ApiResponse[schemas.AiSubmissionResult],
)
def get_submission(
    submission_id: str,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_roles("student")),
):
    submission = db.get(models.AiSubmission, submission_id)
    if not submission:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Submission not found")
    if submission.student_id != user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Not your submission")

    feedback = (
        json.loads(submission.model_feedback) if submission.model_feedback else None
    )
    return schemas.ApiResponse(
        data=schemas.AiSubmissionResult(
            submissionId=submission.id,
            processingStatus=submission.processing_status,
            extractedText=submission.extracted_text,
            modelFeedback=feedback,
        )
    )
