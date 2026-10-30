import pytest
from app.services.session_store import session_store
from app.schemas.models import (
    InterviewSession, InterviewQuestion, InterviewConfig,
    ResumeAnalysis, LinkInspectionResult
)

@pytest.mark.asyncio
async def test_session_store_crud():
    session = InterviewSession(
        session_id="test-session-123",
        config=InterviewConfig(),
        candidate_name="Alice Developer",
        resume_summary="Full Stack Engineer with 4 years experience",
        current_question=InterviewQuestion(
            question_text="Tell me about your architectural decisions.",
            voice_text="Tell me about your architectural decisions."
        ),
        conversation_history=[],
        total_turns_completed=0
    )

    # Save session
    await session_store.save_session(session)

    # Retrieve session
    fetched = await session_store.get_session("test-session-123")
    assert fetched is not None
    assert fetched.session_id == "test-session-123"
    assert fetched.candidate_name == "Alice Developer"
    assert fetched.current_question.question_text == "Tell me about your architectural decisions."

@pytest.mark.asyncio
async def test_session_store_resume_and_inspection():
    resume = ResumeAnalysis(
        full_text="Experienced Python and React developer",
        skills=["Python", "FastAPI", "React"],
        experience_items=["Software Engineer at Tech Corp"],
        extracted_urls=[]
    )
    await session_store.save_resume("test-session-123", resume)

    fetched_resume = await session_store.get_resume("test-session-123")
    assert fetched_resume is not None
    assert "FastAPI" in fetched_resume.skills

    inspection = LinkInspectionResult(
        github_repos=[],
        portfolio_data=[{"title": "Alice Portfolio", "url": "https://alice.dev"}]
    )
    await session_store.save_inspection("test-session-123", inspection)

    fetched_inspection = await session_store.get_inspection("test-session-123")
    assert fetched_inspection is not None
    assert len(fetched_inspection.portfolio_data) == 1
