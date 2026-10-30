from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from enum import Enum

# WHY: Pydantic models provide strict type validation and automatic OpenAPI schema generation for FastAPI.

class UrlType(str, Enum):
    GITHUB_REPO = "github_repo"
    GITHUB_PROFILE = "github_profile"
    LINKEDIN = "linkedin"
    PORTFOLIO = "portfolio"
    OTHER = "other"

class ExtractedURL(BaseModel):
    url: str
    url_type: UrlType

class ResumeAnalysis(BaseModel):
    full_text: str
    skills: List[str]
    experience_items: List[str]
    extracted_urls: List[ExtractedURL]

class CodeFile(BaseModel):
    file_path: str
    content: str
    language: str

class GitHubRepoInfo(BaseModel):
    repo_name: str
    owner: str
    description: Optional[str] = None
    languages: Dict[str, int] = {}
    readme_content: Optional[str] = None
    key_files: List[CodeFile] = []
    stars: int = 0
    topics: List[str] = []

class LinkInspectionResult(BaseModel):
    github_repos: List[GitHubRepoInfo] = []
    portfolio_data: List[Dict[str, Any]] = []
    linkedin_data: Optional[Dict[str, Any]] = None

class VisualContextType(str, Enum):
    GITHUB_CODE = "github_code"
    LIVE_PROJECT = "live_project"
    LINKEDIN_EXPERIENCE = "linkedin_experience"

class VisualContext(BaseModel):
    type: VisualContextType
    repo_name: Optional[str] = None
    file_path: Optional[str] = None
    github_url: Optional[str] = None
    language: Optional[str] = None
    code_snippet: Optional[str] = None
    highlight_lines: Optional[List[int]] = None
    context_title: str

# ---------------------------------------------------------------------------
# Persona & Language Configurations
# ---------------------------------------------------------------------------

class AIProvider(str, Enum):
    GEMINI = "gemini"            # Google Gemini 3.6 Flash (Default Cloud)
    GROQ = "groq"                # Groq Llama 3.3 70B (Ultra-Fast 200ms)
    OLLAMA_LOCAL = "ollama_local"# Local Ollama (ResumeGrind Fine-Tuned Llama 3)

class InterviewPersona(str, Enum):
    FRIENDLY = "friendly"              # Encouraging, supportive mentor
    STRICT_ROAST = "strict_roast"      # Savage, cynical FAANG bar-raiser who roasts buzzwords
    PROFESSIONAL = "professional"      # Formal, objective corporate interviewer

class InterviewLanguage(str, Enum):
    EN = "en"  # English
    HI = "hi"  # Hindi / Hinglish
    ES = "es"  # Spanish
    FR = "fr"  # French
    DE = "de"  # German

class InterviewConfig(BaseModel):
    language: InterviewLanguage = InterviewLanguage.EN
    persona: InterviewPersona = InterviewPersona.STRICT_ROAST
    provider: AIProvider = AIProvider.GEMINI
    target_role: Optional[str] = None
    target_job_description: Optional[str] = None

class SpeechMetrics(BaseModel):
    wpm: int = 130
    filler_word_count: int = 0
    filler_words_detected: List[str] = []
    pacing_rating: str = "Optimal"  # Fast | Optimal | Slow
    clarity_score: int = 8


# ---------------------------------------------------------------------------
# Conversational Questions, Answers, and Visual Learning Cards
# ---------------------------------------------------------------------------

class InterviewQuestion(BaseModel):
    question_text: str
    voice_text: str
    visual_context: Optional[VisualContext] = None
    difficulty: str = "medium"
    category: str = "technical"
    is_cross_question: bool = False
    context_reference: Optional[str] = None # Mentions the candidate's previous claim

class LearningConcept(BaseModel):
    concept_title: str
    summary: str
    theory: Optional[str] = None # Deep conceptual breakdown: Mechanics, real-world case study, pitfalls
    table_markdown: str  # Markdown comparison table (e.g. Approach A vs Approach B)
    diagram_ascii: str   # Clean ASCII or flowchart architecture breakdown
    key_takeaways: List[str]
    resume_project_connection: Optional[str] = None # Direct architecture advice connecting question to student's resume project

class ConversationTurn(BaseModel):
    turn_index: int
    question: InterviewQuestion
    candidate_answer: Optional[str] = None
    score: Optional[int] = None
    persona_reaction: Optional[str] = None # e.g. "Did you actually write that or did Copilot hallucinate it?"
    strengths: List[str] = []
    improvements: List[str] = []
    learning_concept: Optional[LearningConcept] = None

class InterviewSession(BaseModel):
    session_id: str
    config: InterviewConfig = InterviewConfig()
    candidate_name: Optional[str] = None
    resume_summary: str
    current_question: InterviewQuestion
    conversation_history: List[ConversationTurn] = []
    total_turns_completed: int = 0

class AnswerSubmission(BaseModel):
    session_id: str
    transcript: str

class AnswerFeedback(BaseModel):
    score: int = Field(ge=1, le=10)
    strengths: List[str]
    improvements: List[str]
    persona_reaction: str
    speech_metrics: Optional[SpeechMetrics] = None

class SubmitAnswerResponse(BaseModel):
    feedback: AnswerFeedback
    persona_reaction: str
    spoken_reaction: Optional[str] = None
    next_question: Optional[InterviewQuestion] = None
    learning_concept: Optional[LearningConcept] = None
    is_complete: bool = False

class SessionReportDetail(BaseModel):
    question: str
    transcript: str
    score: int
    strengths: List[str]
    improvements: List[str]
    persona_reaction: Optional[str] = None
    learning_concept: Optional[LearningConcept] = None
    speech_metrics: Optional[SpeechMetrics] = None

class ResumeBulletImprovement(BaseModel):
    original: str
    improved: str
    explanation: str

class CodeRefactorSuggestion(BaseModel):
    file_path: str
    issue: str
    diff_suggestion: str

class SessionReport(BaseModel):
    session_id: str
    overall_score: int
    category_scores: Dict[str, int]
    details: List[SessionReportDetail]
    recommendations: List[str]
    persona_used: str = "strict_roast"
    language_used: str = "en"
    target_role: Optional[str] = None
    jd_match_score: Optional[int] = None
    speech_summary: Optional[Dict[str, Any]] = None
    resume_bullet_improvements: List[ResumeBulletImprovement] = []
    code_refactoring_suggestions: List[CodeRefactorSuggestion] = []
