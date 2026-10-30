import json
import uuid
import httpx
import asyncio
from typing import List, Dict, Any, Optional

from app.config import settings
from app.schemas.models import (
    ResumeAnalysis, LinkInspectionResult, InterviewSession,
    InterviewQuestion, AnswerFeedback, SessionReport, SessionReportDetail,
    VisualContext, VisualContextType, InterviewConfig, InterviewPersona, InterviewLanguage,
    ConversationTurn, LearningConcept, SubmitAnswerResponse
)
from app.services.providers.base_provider import BaseAIProvider
from app.services.providers.gemini_provider import GeminiProvider

class GroqProvider(BaseAIProvider):
    """
    Groq API Implementation of BaseAIProvider (Ultra-Fast 200ms Llama 3.3 70B).
    Falls back gracefully to GeminiProvider if GROQ_API_KEY is not configured.
    """

    def __init__(self):
        self.api_key = settings.GROQ_API_KEY
        self.base_url = "https://api.groq.com/openai/v1/chat/completions"
        self.model = "llama-3.3-70b-versatile"
        self.fallback_provider = GeminiProvider()

    async def _call_groq(self, prompt: str, system_prompt: str = "") -> str:
        if not self.api_key:
            raise ValueError("GROQ_API_KEY is not set. Falling back to Gemini.")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt or "You are an expert technical interviewer. Output valid JSON ONLY."},
                {"role": "user", "content": prompt}
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.7,
            "max_tokens": 1200
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.post(self.base_url, headers=headers, json=payload)
            res.raise_for_status()
            data = res.json()
            return data["choices"][0]["message"]["content"]

    async def generate_session(
        self, resume: ResumeAnalysis, inspection: LinkInspectionResult, config: InterviewConfig
    ) -> InterviewSession:
        if not self.api_key:
            return await self.fallback_provider.generate_session(resume, inspection, config)

        session_id = str(uuid.uuid4())
        context = self.fallback_provider._build_candidate_context(resume, inspection)
        persona_instructions = self.fallback_provider._get_persona_instructions(config.persona)
        language_instructions = self.fallback_provider._get_language_instructions(config.language)

        prompt = f"""You are conducting a live technical interview.
{persona_instructions}
{language_instructions}

{context}

Generate the very FIRST opening question for this candidate from scratch.
Return ONLY valid JSON matching this schema:
{{
    "resume_summary": "one-line candidate summary",
    "question": {{
        "question_text": "text for UI",
        "voice_text": "text spoken aloud",
        "difficulty": "medium",
        "category": "introduction"
    }}
}}"""

        try:
            res_text = await self._call_groq(prompt)
            data = json.loads(self.fallback_provider._clean_json_text(res_text), strict=False)
            q_data = data.get("question", {})
            gen_q = q_data.get("question_text", "").strip()

            if gen_q:
                first_q = InterviewQuestion(
                    question_text=gen_q,
                    voice_text=q_data.get("voice_text", gen_q),
                    difficulty="medium",
                    category="introduction",
                    is_cross_question=False
                )
            else:
                first_q = self.fallback_provider._get_fallback_initial_question(resume, inspection, config)

            return InterviewSession(
                session_id=session_id,
                config=config,
                resume_summary=data.get("resume_summary", "Candidate Profile (Groq Llama 3.3 Engine)"),
                current_question=first_q,
                conversation_history=[],
                total_turns_completed=0
            )

        except Exception as e:
            print(f"[GROQ PROVIDER] Fallback to Gemini ({e})")
            return await self.fallback_provider.generate_session(resume, inspection, config)

    async def evaluate_and_cross_examine(
        self, session: InterviewSession, transcript: str, resume: ResumeAnalysis, inspection: LinkInspectionResult
    ) -> SubmitAnswerResponse:
        if not self.api_key:
            return await self.fallback_provider.evaluate_and_cross_examine(session, transcript, resume, inspection)

        try:
            current_turn = len(session.conversation_history) + 1
            last_question = session.current_question
            persona_instructions = self.fallback_provider._get_persona_instructions(session.config.persona)
            language_instructions = self.fallback_provider._get_language_instructions(session.config.language)
            candidate_context = self.fallback_provider._build_candidate_context(resume, inspection)

            prompt = f"""You are the technical interviewer continuing an interactive multi-turn interview.
{persona_instructions}
{language_instructions}

{candidate_context}

PREVIOUS QUESTION ASKED: "{last_question.question_text}"
CANDIDATE'S SPOKEN ANSWER: "{transcript}"
CURRENT TURN NUMBER: {current_turn}

Return ONLY valid JSON matching this schema:
{{
    "score": 8,
    "strengths": ["Clear fundamental reasoning"],
    "improvements": ["Deepen architecture analysis"],
    "persona_reaction": "Your in-character feedback reaction",
    "next_question": {{
        "question_text": "text for UI",
        "voice_text": "spoken voice text",
        "difficulty": "hard",
        "category": "cross_examination",
        "context_reference": "Direct reference to answer"
    }}
}}"""

            res_text = await self._call_groq(prompt)
            data = json.loads(self.fallback_provider._clean_json_text(res_text), strict=False)

            score = max(1, min(10, int(data.get("score", 7))))
            persona_reaction = data.get("persona_reaction", "Let's move to the next technical topic.")
            strengths = data.get("strengths", ["Solid technical understanding"])
            improvements = data.get("improvements", ["Provide quantitative system metrics"])

            nq_data = data.get("next_question", {})
            gen_q_text = nq_data.get("question_text", "How would you optimize this under load?").strip()
            combined_voice_text = f"{persona_reaction.strip()} ... {nq_data.get('voice_text', gen_q_text)}"

            first_repo = inspection.github_repos[0] if inspection.github_repos else None
            vc = None
            if current_turn >= 2 and first_repo and first_repo.key_files:
                kf = first_repo.key_files[0]
                vc = VisualContext(
                    type=VisualContextType.GITHUB_CODE,
                    repo_name=first_repo.repo_name,
                    file_path=kf.file_path,
                    github_url=f"https://github.com/{first_repo.owner}/{first_repo.repo_name}",
                    language=kf.language,
                    code_snippet=kf.content[:1000],
                    highlight_lines=[1, 2, 3, 4],
                    context_title=f"GitHub: {first_repo.repo_name} / {kf.file_path}"
                )

            next_q = InterviewQuestion(
                question_text=gen_q_text,
                voice_text=combined_voice_text,
                difficulty="hard",
                category="cross_examination",
                is_cross_question=True,
                visual_context=vc
            )

            feedback = AnswerFeedback(
                score=score,
                strengths=strengths,
                improvements=improvements,
                persona_reaction=persona_reaction
            )

            return SubmitAnswerResponse(
                feedback=feedback,
                persona_reaction=persona_reaction,
                spoken_reaction=persona_reaction,
                next_question=next_q,
                learning_concept=None,
                is_complete=False
            )
        except Exception as e:
            print(f"[GROQ PROVIDER] Fallback to Gemini ({e})")
            return await self.fallback_provider.evaluate_and_cross_examine(session, transcript, resume, inspection)

    async def generate_learning_concept(self, topic: str) -> LearningConcept:
        return await self.fallback_provider.generate_learning_concept(topic)
