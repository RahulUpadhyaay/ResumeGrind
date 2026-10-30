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
from app.utils.speech_analyzer import analyze_speech_delivery

class OllamaProvider(BaseAIProvider):
    """
    Local Ollama Custom Model Implementation of BaseAIProvider.
    Connects to http://localhost:11434 running fine-tuned ResumeGrind models (resumegrind-llama3).
    Features:
    1. Automatic detection of installed models via /api/tags.
    2. Structured prompt schema aligned with fine-tuning template.
    3. Intent detection for DSA / coding pivots with live Monaco sandbox.
    4. Dedicated System Design interview track with architecture diagrams & whiteboard notes.
    5. Clean fallback to resilient deterministic interview engine on errors.
    """

    def __init__(self):
        self.raw_base_url = settings.OLLAMA_BASE_URL.rstrip('/')
        if self.raw_base_url.endswith('/v1'):
            self.root_url = self.raw_base_url[:-3]
        else:
            self.root_url = self.raw_base_url
        self.model = "resumegrind-llama3"
        self.fallback_provider = GeminiProvider()

    async def _detect_best_model(self, client: httpx.AsyncClient) -> str:
        """Queries Ollama for installed models and picks the best available."""
        try:
            res = await client.get(f"{self.root_url}/api/tags", timeout=3.0)
            if res.status_code == 200:
                models = [m.get("name", "").split(":")[0] for m in res.json().get("models", [])]
                if "resumegrind-llama3" in models:
                    return "resumegrind-llama3"
                for pref in ["llama3.2", "llama3.1", "llama3", "mistral", "qwen2.5", "phi3"]:
                    if any(pref in m for m in models):
                        matching = [m for m in models if pref in m][0]
                        return matching
                if models:
                    return models[0]
        except Exception:
            pass
        return self.model

    async def _call_ollama(self, prompt: str, system_prompt: str = "") -> str:
        async with httpx.AsyncClient(timeout=45.0) as client:
            chosen_model = await self._detect_best_model(client)

            # Try native Ollama endpoint (/api/chat) first for best format=json reliability
            payload_native = {
                "model": chosen_model,
                "messages": [
                    {"role": "system", "content": system_prompt or "You are ResumeGrind-Llama3, an elite technical mock interviewer. Output valid JSON ONLY."},
                    {"role": "user", "content": prompt}
                ],
                "stream": False,
                "format": "json"
            }
            try:
                res = await client.post(f"{self.root_url}/api/chat", json=payload_native)
                if res.status_code == 200:
                    data = res.json()
                    content = data.get("message", {}).get("content", "").strip()
                    if content:
                        return content
            except Exception:
                pass

            # Fallback to OpenAI-compatible endpoint (/v1/chat/completions)
            payload_openai = {
                "model": chosen_model,
                "messages": [
                    {"role": "system", "content": system_prompt or "You are ResumeGrind-Llama3, an elite technical mock interviewer. Output valid JSON ONLY."},
                    {"role": "user", "content": prompt}
                ],
                "stream": False,
                "format": "json"
            }
            res = await client.post(f"{self.root_url}/v1/chat/completions", json=payload_openai)
            res.raise_for_status()
            data = res.json()
            return data["choices"][0]["message"]["content"]

    async def generate_session(
        self, resume: ResumeAnalysis, inspection: LinkInspectionResult, config: InterviewConfig
    ) -> InterviewSession:
        """
        Generates the first opening question for the candidate.
        Ensures the question begins naturally with an introduction request followed by
        probing the candidate's core resume skills/projects.
        """
        try:
            session_id = str(uuid.uuid4())
            context = self.fallback_provider._build_candidate_context(resume, inspection, config)
            persona_instructions = self.fallback_provider._get_persona_instructions(config.persona)
            language_instructions = self.fallback_provider._get_language_instructions(config.language)

            top_skill = resume.skills[0] if resume.skills else "Software Engineering"
            projects_summary = ", ".join(resume.experience_items[:2]) if resume.experience_items else "Backend Architecture"

            prompt = f"""You are ResumeGrind-Llama3 conducting an elite technical mock interview.
{persona_instructions}
{language_instructions}

{context}

Generate the very FIRST opening question (Round 1) for this candidate.
REQUIREMENTS:
1. First, warmly invite the candidate to give a concise introduction of themselves and their background.
2. Then, ask them to dive into the most challenging technical project or architecture from their resume ({top_skill} or {projects_summary}).

Return ONLY valid JSON matching this schema:
{{
    "resume_summary": "one-line candidate summary highlighting key tech stack",
    "question": {{
        "question_text": "Welcome to your technical interview! Please start with a concise introduction of yourself, and then walk me through the most technically challenging project on your resume, detailing your architecture and the trade-offs you made.",
        "voice_text": "Welcome to your technical interview! Please give me a concise introduction of yourself and tell me about the most difficult engineering challenge on your resume.",
        "difficulty": "medium",
        "category": "introduction"
    }}
}}"""

            res_text = await self._call_ollama(prompt)
            data = json.loads(self.fallback_provider._clean_json_text(res_text), strict=False)
            q_data = data.get("question", {})
            gen_q = q_data.get("question_text", "").strip()

            # Ensure non-trivial question
            if gen_q and len(gen_q) > 20:
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
                resume_summary=data.get("resume_summary", f"Senior {top_skill} Engineer"),
                current_question=first_q,
                conversation_history=[],
                total_turns_completed=0
            )

        except Exception as e:
            print(f"[OLLAMA PROVIDER] Ollama generate_session notice ({e}). Using resilient initial question.")
            session = await self.fallback_provider.generate_session(resume, inspection, config)
            return session

    async def evaluate_and_cross_examine(
        self, session: InterviewSession, transcript: str, resume: ResumeAnalysis, inspection: LinkInspectionResult
    ) -> SubmitAnswerResponse:
        current_turn = len(session.conversation_history) + 1
        clean_text = (transcript or "").strip()

        # ------------------------------------------------------------------
        # 1. DSA / Live Coding Sandbox Intent Detection
        # ------------------------------------------------------------------
        coding_requests = [
            "data structure", "algorithm", "dsa", "coding", "code", "leetcode",
            "problem solving", "showcase my coding", "write code", "sandbox", "editor",
            "move on to the dsa", "switch to coding", "coding question"
        ]
        wants_coding = any(k in clean_text.lower() for k in coding_requests)

        if wants_coding:
            return self.fallback_provider._build_dsa_challenge(transcript)

        # ------------------------------------------------------------------
        # 2. System Design Intent Detection (Pure Verbal - No Cluttered Right Panel)
        # ------------------------------------------------------------------
        sys_design_triggers = [
            "system design", "architecture", "scalability", "scale", "distributed system",
            "microservices", "sharding", "kafka", "caching", "rate limiting", "load balancer",
            "move on to system design", "switch to system design", "ask system design"
        ]
        wants_sys_design = any(k in clean_text.lower() for k in sys_design_triggers)

        if wants_sys_design:
            q_text = "Now let's move to System Design. How would you design a high-throughput flash-sale ticket reservation system handling 50,000 concurrent writes per second without database lock contention or double-booking seats?"
            reaction = "Now let's test your high-level engineering. Switching to distributed system design:"
            return SubmitAnswerResponse(
                feedback=AnswerFeedback(
                    score=8,
                    strengths=["Strong architectural aptitude"],
                    improvements=["Prepare to quantify throughput bottlenecks"],
                    persona_reaction=reaction,
                    speech_metrics=analyze_speech_delivery(transcript)
                ),
                persona_reaction=reaction,
                spoken_reaction=reaction,
                next_question=InterviewQuestion(
                    question_text=q_text,
                    voice_text=f"{reaction} {q_text}",
                    difficulty="hard",
                    category="System Design & Architecture",
                    is_cross_question=True,
                    context_reference="System Design Assessment",
                    visual_context=None  # Right panel is kept clean for Take a Hint!
                ),
                learning_concept=None,
                is_complete=False
            )

        # ------------------------------------------------------------------
        # 3. Deflection / Careless Evasion / Gibberish Detection
        # ------------------------------------------------------------------
        deflections = [
            "you just ask", "ask something else", "change the question", "different topic",
            "skip this", "next question", "don't ask", "i don't know", "i dont know",
            "no idea", "dont know", "skip"
        ]
        is_deflection = any(d in clean_text.lower() for d in deflections)
        word_count = len(clean_text.split())
        tech_indicators = ["cache", "redis", "database", "sql", "async", "scale", "worker", "thread", "api", "index", "latency", "load", "model", "python", "service", "concurrency", "docker", "query", "optimize", "kafka", "postgres", "lock"]
        has_tech = any(k in clean_text.lower() for k in tech_indicators)
        is_gibberish_or_trivial = (word_count < 5 and not has_tech) or (word_count < 3)

        # Rate limit blunder on 10k writes detection
        is_rate_limit_blunder = any(r in clean_text.lower() for r in ["rate limit", "block ip", "block that ip", "disallow him", "blocking ip"]) and any(q in session.current_question.question_text.lower() for q in ["10,000", "10000", "concurrent writes", "writes per second"])

        # ------------------------------------------------------------------
        # 4. Ollama LLM Evaluation Call with Fine-Tuned Model Schema
        # ------------------------------------------------------------------
        try:
            last_question = session.current_question
            persona_instructions = self.fallback_provider._get_persona_instructions(session.config.persona)
            language_instructions = self.fallback_provider._get_language_instructions(session.config.language)
            candidate_context = self.fallback_provider._build_candidate_context(resume, inspection, session.config)

            prompt = f"""You are ResumeGrind-Llama3 continuing an interactive mock interview.
{persona_instructions}
{language_instructions}

{candidate_context}

PREVIOUS QUESTION: "{last_question.question_text}"
CANDIDATE'S SPOKEN ANSWER: "{transcript}"
CURRENT ROUND: {current_turn}

EVALUATION RULES:
- If the candidate evaded, gave up, or said "I don't know": Give score 1-3 with a stern reality check.
- If the candidate suggested blocking user IPs for high legitimate traffic (e.g. 10k writes/sec): Give score 3-5 with a targeted architectural critique (explain Kafka/queues).
- If the candidate gave a solid answer: Give score 7-10 with enthusiastic praise and attack edge-case failure modes.

Return ONLY valid JSON matching this schema:
{{
    "score": 8,
    "strengths": ["Clear fundamental understanding"],
    "improvements": ["Account for distributed network partitions"],
    "persona_reaction": "Your direct spoken assessment following tone guidelines",
    "next_question": {{
        "question_text": "text for UI",
        "voice_text": "spoken voice text",
        "difficulty": "hard",
        "category": "cross_examination"
    }}
}}"""

            res_text = await self._call_ollama(prompt)
            data = json.loads(self.fallback_provider._clean_json_text(res_text), strict=False)

            score = max(1, min(10, int(data.get("score", 7))))
            persona_reaction = data.get("persona_reaction", "Let's examine that further.")
            strengths = data.get("strengths", ["Addressed core technical concepts"])
            improvements = data.get("improvements", ["Provide quantitative benchmarks"])

            # Enforce strict scoring bounds on known blunders
            if is_gibberish_or_trivial:
                score = 2
                persona_reaction = "What kind of careless answer is that? That was completely superficial and meaningless. In a senior engineering interview, you need to articulate technical principles! Listen carefully:"
            elif is_deflection:
                score = min(score, 3)
                persona_reaction = "What kind of careless answer is that? That was completely superficial. Evading technical questions is an immediate red flag in real senior interviews! Listen carefully:"
            elif is_rate_limit_blunder:
                score = min(score, 4)
                persona_reaction = "Wait a minute: 10,000 writes per second is legitimate peak business traffic during a flash sale, not an attack! If you block users hitting 20 req/s, you drop paying customers. Listen carefully:"

            nq_data = data.get("next_question", {})
            gen_q_text = nq_data.get("question_text", "").strip()

            asked_texts = {session.current_question.question_text.strip().lower()}
            for t in session.conversation_history:
                if t.question and t.question.question_text:
                    asked_texts.add(t.question.question_text.strip().lower())

            if not gen_q_text or gen_q_text.lower() in asked_texts or len(gen_q_text) < 15:
                return self.fallback_provider._fallback_cross_examine(session, transcript, inspection, current_turn)

            combined_voice_text = f"{persona_reaction.strip()} ... {nq_data.get('voice_text', gen_q_text)}"

            next_q = InterviewQuestion(
                question_text=gen_q_text,
                voice_text=combined_voice_text,
                difficulty="hard",
                category="cross_examination",
                is_cross_question=True,
                visual_context=None
            )

            return SubmitAnswerResponse(
                feedback=AnswerFeedback(
                    score=score,
                    strengths=strengths,
                    improvements=improvements,
                    persona_reaction=persona_reaction,
                    speech_metrics=analyze_speech_delivery(transcript)
                ),
                persona_reaction=persona_reaction,
                spoken_reaction=persona_reaction,
                next_question=next_q,
                learning_concept=None,
                is_complete=False
            )

        except Exception as e:
            print(f"[OLLAMA PROVIDER] Notice ({e}). Using deterministic fallback.")
            return self.fallback_provider._fallback_cross_examine(session, transcript, inspection, current_turn)

    async def generate_learning_concept(self, topic: str) -> LearningConcept:
        return await self.fallback_provider.generate_learning_concept(topic)
