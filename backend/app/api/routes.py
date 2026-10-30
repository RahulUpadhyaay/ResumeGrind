from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List, Optional, Dict
from pydantic import BaseModel

from app.schemas.models import (
    ExtractedURL, ResumeAnalysis, LinkInspectionResult,
    InterviewSession, InterviewQuestion, AnswerFeedback,
    SessionReport, VisualContext, InterviewConfig, SubmitAnswerResponse,
    ConversationTurn, LearningConcept
)
from app.services.resume_parser import resume_parser
from app.services.link_inspector import link_inspector
from app.services.ai_interviewer import ai_interviewer
from app.services.session_store import session_store

router = APIRouter()


# =============================================================================
# 1. UPLOAD RESUME
# =============================================================================
@router.post("/upload-resume", response_model=ResumeAnalysis)
async def upload_resume(file: UploadFile = File(...)):
    """
    Upload a PDF or DOCX resume file for parsing.
    Extracts text content, skills, experience items, and all embedded URLs.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required")

    allowed_extensions = ('.pdf', '.docx')
    if not file.filename.lower().endswith(allowed_extensions):
        raise HTTPException(
            status_code=400,
            detail=f"Only {', '.join(allowed_extensions)} files are supported"
        )

    content = await file.read()
    try:
        analysis = await resume_parser.parse(content, file.filename)
        return analysis
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse resume: {str(e)}")


# =============================================================================
# 2. INSPECT LINKS
# =============================================================================
class InspectLinksRequest(BaseModel):
    urls: List[ExtractedURL]

@router.post("/inspect-links", response_model=LinkInspectionResult)
async def inspect_links(request: InspectLinksRequest):
    """
    Deep-crawl URLs from resume: GitHub repo code and portfolio websites.
    """
    try:
        inspection = await link_inspector.inspect_all(request.urls)
        return inspection
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# 3. START INTERVIEW (With Multi-Language & Persona Support)
# =============================================================================
class StartInterviewRequest(BaseModel):
    resume_analysis: ResumeAnalysis
    inspection_result: LinkInspectionResult
    config: Optional[InterviewConfig] = None

@router.post("/start-interview", response_model=InterviewSession)
async def start_interview(request: StartInterviewRequest):
    """
    Starts an interactive interview from scratch with chosen language and persona.
    """
    config = request.config or InterviewConfig()
    try:
        session = await ai_interviewer.generate_session(
            request.resume_analysis,
            request.inspection_result,
            config
        )
        # Store context for dynamic multi-turn conversation
        await session_store.save_session(session)
        await session_store.save_resume(session.session_id, request.resume_analysis)
        await session_store.save_inspection(session.session_id, request.inspection_result)
        return session
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# 4. SUBMIT ANSWER & DYNAMIC CROSS-EXAMINATION
# =============================================================================
class SubmitAnswerRequest(BaseModel):
    session_id: str
    question_index: Optional[int] = 0
    transcript: str

@router.post("/submit-answer", response_model=SubmitAnswerResponse)
async def submit_answer(request: SubmitAnswerRequest):
    """
    Evaluates candidate's answer, delivers in-character persona response,
    and dynamically cross-examines their claims with a targeted follow-up question.
    """
    session = await session_store.get_session(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    resume = await session_store.get_resume(request.session_id) or ResumeAnalysis(full_text="", skills=[], experience_items=[], extracted_urls=[])
    inspection = await session_store.get_inspection(request.session_id) or LinkInspectionResult()

    try:
        response = await ai_interviewer.evaluate_and_cross_examine(
            session,
            request.transcript,
            resume,
            inspection
        )

        # Record this turn into conversation history
        turn = ConversationTurn(
            turn_index=len(session.conversation_history) + 1,
            question=session.current_question,
            candidate_answer=request.transcript,
            score=response.feedback.score,
            persona_reaction=response.persona_reaction,
            strengths=response.feedback.strengths,
            improvements=response.feedback.improvements,
            learning_concept=response.learning_concept
        )
        session.conversation_history.append(turn)
        session.total_turns_completed += 1

        # Advance current question to the new dynamic cross-question
        if response.next_question:
            session.current_question = response.next_question

        # Persist updated session state
        await session_store.save_session(session)

        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# 5. TEACH CONCEPT (Interactive Learning Phase with Tables & Diagrams)
# =============================================================================
class TeachConceptRequest(BaseModel):
    topic: str
    session_id: Optional[str] = None
    question_text: Optional[str] = None

@router.post("/teach-concept", response_model=LearningConcept)
async def teach_concept(request: TeachConceptRequest):
    """
    Generates an interactive visual learning card with comparison tables
    and architecture diagrams for engineering concept mastery.
    If session_id is provided, tailors the advice directly to the candidate's resume projects!
    """
    try:
        resume = None
        if request.session_id:
            resume = await session_store.get_resume(request.session_id)
        concept = await ai_interviewer.generate_learning_concept(
            request.topic,
            resume=resume,
            question_text=request.question_text
        )
        return concept
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# 6. SESSION REPORT
# =============================================================================
@router.get("/session-report/{session_id}", response_model=SessionReport)
async def get_session_report(session_id: str):
    """
    Get the comprehensive performance report across all multi-turn conversation rounds.
    """
    session = await session_store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found or expired")

    try:
        report = await ai_interviewer.generate_report(session)
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


from app.services.code_executor import code_executor, CodeExecutionRequest, CodeExecutionResponse
from app.services.rag_service import rag_service

# =============================================================================
# 7. EXECUTE CODE (Live Monaco Sandbox Execution Engine)
# =============================================================================
@router.post("/execute-code", response_model=CodeExecutionResponse)
async def execute_code(request: CodeExecutionRequest):
    """
    Executes Python or JavaScript code inside a sandboxed subprocess
    with 5-second process timeout guards.
    """
    try:
        result = await code_executor.execute_code(request)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# 8. SEMANTIC RAG SEARCH (Vector Search across GitHub Codebase)
# =============================================================================
class RAGSearchRequest(BaseModel):
    query: str

@router.post("/rag-search")
async def rag_search(request: RAGSearchRequest):
    """
    Performs dense vector similarity search across indexed repository code chunks.
    """
    try:
        results = await rag_service.query_code_vector_db(request.query)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# 9. HEALTH CHECK
# =============================================================================
@router.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "ResumeGrind API",
        "version": "3.0.0 (Multi-Provider RAG & Monaco Sandbox Engine)"
    }

