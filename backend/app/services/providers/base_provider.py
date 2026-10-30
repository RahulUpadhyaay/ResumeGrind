from abc import ABC, abstractmethod
from typing import Optional
from app.schemas.models import (
    ResumeAnalysis, LinkInspectionResult, InterviewSession,
    InterviewConfig, SubmitAnswerResponse, LearningConcept
)

class BaseAIProvider(ABC):
    """
    Abstract Base Class for AI Model Providers (Strategy Pattern).
    Decouples LLM providers (Gemini, Groq, Ollama) from the rest of the application.
    """

    @abstractmethod
    async def generate_session(
        self,
        resume: ResumeAnalysis,
        inspection: LinkInspectionResult,
        config: InterviewConfig
    ) -> InterviewSession:
        """Starts a natural interview session with personalized opening question."""
        pass

    @abstractmethod
    async def evaluate_and_cross_examine(
        self,
        session: InterviewSession,
        transcript: str,
        resume: ResumeAnalysis,
        inspection: LinkInspectionResult,
    ) -> SubmitAnswerResponse:
        """Evaluates candidate answer and returns score, feedback, tone reaction, and cross-question."""
        pass

    @abstractmethod
    async def generate_learning_concept(
        self, topic: str, resume: Optional[ResumeAnalysis] = None, question_text: Optional[str] = None
    ) -> LearningConcept:
        """Generates visual learning card with theory, comparison tables, ASCII diagrams, and resume connections."""
        pass
