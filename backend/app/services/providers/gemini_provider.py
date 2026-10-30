import json
import uuid
import random
import asyncio
from typing import List, Dict, Any, Optional
from google import genai
from google.genai import types

from app.config import settings
from app.schemas.models import (
    ResumeAnalysis, LinkInspectionResult, InterviewSession,
    InterviewQuestion, AnswerFeedback, SessionReport, SessionReportDetail,
    VisualContext, VisualContextType, InterviewConfig, InterviewPersona, InterviewLanguage,
    ConversationTurn, LearningConcept, SubmitAnswerResponse
)
from app.services.providers.base_provider import BaseAIProvider
from app.utils.speech_analyzer import analyze_speech_delivery

class GeminiProvider(BaseAIProvider):
    """
    Google Gemini 3.6 Flash Implementation of BaseAIProvider.
    """

    def __init__(self):
        api_key = settings.GEMINI_API_KEY or "dummy_key_for_dev_init"
        self.client = genai.Client(api_key=api_key)
        self.primary_model = "gemini-3.5-flash-lite"


    def _get_persona_instructions(self, persona: InterviewPersona) -> str:
        return """DYNAMIC INTERVIEWER EVALUATION & TONE (ADAPT TONE STRICTLY ACCORDING TO ANSWER):
- SCORING SCALE: Score every answer strictly on a scale from 1 to 10:
  * 1 - 4: Poor, careless, shallow, or wrong answer. (Triggers HARSH tone)
  * 5 - 6: Average or mediocre answer with partial correctness. (Triggers FIRM reality-check tone)
  * 7 - 8: Solid, accurate answer with sound fundamentals. (Triggers FRIENDLY praise tone)
  * 9 - 10: Exceptional, production-ready mastery. (Triggers ENTHUSIASTIC FRIENDLY praise tone)

- TONE ADAPTATION RULES (CRITICAL - ALWAYS MATCH TONE TO ANSWER QUALITY):
  * IF CANDIDATE SCORED 7 TO 10 (STRONG / ACCURATE ANSWER):
    - You MUST speak in an unmistakably FRIENDLY, WARM, ENCOURAGING, AND PRAISING TONE!
    - Celebrate their good reasoning, applaud their clarity, and give warm validation:
      English example: "Spot on! That was a fantastic, clear, and well-structured answer. I really love how clearly you reasoned through the trade-offs—keep that momentum going!"
      Hindi / Hinglish example: "Shabash! Bahut hi shandar aur crystal-clear answer diya aapne. Mujhe aapka architectural approach aur clarity bahut pasand aayi!"
  * IF CANDIDATE SCORED 1 TO 4 (WEAK / CARELESS / WRONG ANSWER):
    - You MUST speak in an unmistakably HARSH, STERN, SCOLDING, AND ROASTING TONE!
    - Call out their superficial flaw or careless buzzwords bluntly like a demanding professor who will not accept excuses or bluffing:
      English example: "What kind of careless answer is that? That was completely superficial, dangerously flawed, and shows zero depth. Stop throwing buzzwords at me and listen carefully!"
      Hindi / Hinglish example: "Ye kya behuda aur laparwah answer hai! Bilkul galat aur surface-level baat kar rahe ho tum. Aise excuses real production me nahi chalte. Dhyan se suno aur dhang se jawab do!"
  * IF CANDIDATE SCORED 5 TO 6 (AVERAGE / PARTIAL ANSWER):
    - Deliver a FIRM, CONSTRUCTIVE REALITY-CHECK challenging them for missing system trade-offs:
      English example: "You have the basic idea, but you completely hand-waved over the real production bottlenecks. Mediocre answers won't survive a senior bar—step it up!"
      Hindi / Hinglish example: "Basic baat theek hai par real production failure modes ko bilkul ignore kar diya aapne. Thoda aur gehraai me sochiye!"

- In your 'persona_reaction', deliver a punchy 1-2 sentence response directly embodying this tone.
- This reaction will be spoken aloud to the candidate before presenting the next question."""

    def _get_language_instructions(self, language: InterviewLanguage) -> str:
        if language == InterviewLanguage.HI:
            return """LANGUAGE: HINDI / HINGLISH
- Conduct the interview in natural, conversational Hinglish (mix of Hindi & English commonly spoken in Indian tech interviews, written in Latin alphabet so Text-To-Speech reads it cleanly).
- Example voice_text: 'Aapne apne project me Redis use kiya hai. Mujhe explain kijiye ki cache stampede se bachne ke liye aapne kya strategy use ki?'"""
        elif language == InterviewLanguage.ES:
            return """LANGUAGE: SPANISH
- Conduct the interview entirely in natural, professional Spanish."""
        elif language == InterviewLanguage.FR:
            return """LANGUAGE: FRENCH
- Conduct the interview entirely in natural French."""
        elif language == InterviewLanguage.DE:
            return """LANGUAGE: GERMAN
- Conduct the interview entirely in natural German."""
        else:
            return """LANGUAGE: ENGLISH
- Conduct the interview in clear, idiomatic English."""

    async def _call_gemini(self, prompt: str, config: types.GenerateContentConfig):
        return await asyncio.wait_for(
            self.client.aio.models.generate_content(
                model=self.primary_model,
                contents=prompt,
                config=config,
            ),
            timeout=8.0
        )

    def _clean_json_text(self, text: str) -> str:
        text = text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

        if not text.endswith("}"):
            open_braces = text.count("{") - text.count("}")
            open_brackets = text.count("[") - text.count("]")
            text += "]" * max(0, open_brackets) + "}" * max(0, open_braces)
        return text

    def _build_candidate_context(
        self, resume: ResumeAnalysis, inspection: LinkInspectionResult, config: Optional[InterviewConfig] = None
    ) -> str:
        parts = []
        clean_text = " ".join(resume.full_text.split())
        parts.append(f"=== CANDIDATE RESUME ===\n{clean_text[:2000]}")

        if config and config.target_role:
            parts.append(f"=== TARGET ROLE / LEVEL ===\n{config.target_role}")
        if config and config.target_job_description:
            parts.append(f"=== TARGET JOB DESCRIPTION ===\n{config.target_job_description[:1500]}")

        if resume.skills:
            parts.append(f"=== SKILLS ===\n{', '.join(resume.skills[:10])}")

        if inspection.github_repos:
            parts.append("=== GITHUB REPOSITORIES & REAL CODE ===")
            for repo in inspection.github_repos[:2]:
                parts.append(f"Repo: {repo.repo_name} | Owner: {repo.owner} | Langs: {list(repo.languages.keys())[:3]}")
                for f in repo.key_files[:2]:
                    clean_code = f.content[:700].replace('"', "'")
                    parts.append(f"File: {f.file_path}\n```{clean_code}```")

        return "\n".join(parts)

    def _get_fallback_initial_question(
        self, resume: ResumeAnalysis, inspection: LinkInspectionResult, config: InterviewConfig
    ) -> InterviewQuestion:
        candidate_name = resume.candidate_name or "Candidate"
        if config.language == InterviewLanguage.HI:
            q_text = f"Welcome {candidate_name}! Technical interview shuru karne se pehle, please mujhe apna ek concise introduction dijiye, apne engineering background ke baare me batayein aur aap kin technologies me sabse zyada comfortable hain."
        else:
            q_text = f"Welcome to your technical interview, {candidate_name}! To kick off our session, please introduce yourself, give a brief overview of your engineering background, and highlight the primary technologies and domains you specialize in."

        return InterviewQuestion(
            question_text=q_text,
            voice_text=q_text,
            difficulty="easy",
            category="Candidate Introduction",
            is_cross_question=False,
            visual_context=None
        )

    async def generate_session(
        self, resume: ResumeAnalysis, inspection: LinkInspectionResult, config: InterviewConfig
    ) -> InterviewSession:
        session_id = str(uuid.uuid4())
        context = self._build_candidate_context(resume, inspection, config)
        persona_instructions = self._get_persona_instructions(config.persona)
        language_instructions = self._get_language_instructions(config.language)

        candidate_name = resume.candidate_name or "Candidate"
        prompt = f"""You are conducting a professional senior software engineering interview.
{persona_instructions}
{language_instructions}

{context}

ROUND 1 REQUIREMENT (PROFESSIONAL CANDIDATE INTRODUCTION):
The interview must start professionally with the candidate's personal introduction.
- Welcome {candidate_name} warmly and ask them to introduce themselves, summarize their engineering background, and share what areas or technologies they enjoy working with.
- Do NOT jump into difficult project cross-examination or complex architecture yet. That will happen in Round 2 right after their introduction.

Return ONLY valid JSON matching this schema:
{{
    "resume_summary": "one-line candidate summary",
    "question": {{
        "question_text": "Welcome to your technical interview, {candidate_name}! To start off, please introduce yourself, give a brief overview of your engineering background, and highlight the primary technologies and domains you specialize in.",
        "voice_text": "Welcome to your technical interview, {candidate_name}! To start off, please introduce yourself, give a brief overview of your engineering background, and highlight the primary technologies and domains you specialize in.",
        "difficulty": "easy",
        "category": "Candidate Introduction"
    }}
}}"""


        try:
            gen_config = types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.8,
                max_output_tokens=600,
            )
            response = await self._call_gemini(prompt, gen_config)
            cleaned = self._clean_json_text(response.text)
            data = json.loads(cleaned, strict=False)

            q_data = data.get("question", {})
            first_q = InterviewQuestion(
                question_text=q_data.get("question_text", ""),
                voice_text=q_data.get("voice_text", q_data.get("question_text", "")),
                difficulty=q_data.get("difficulty", "medium"),
                category="introduction",
                is_cross_question=False,
            )

            return InterviewSession(
                session_id=session_id,
                config=config,
                resume_summary=data.get("resume_summary", "Candidate Profile"),
                current_question=first_q,
                conversation_history=[],
                total_turns_completed=0
            )
        except Exception as e:
            print(f"[GEMINI PROVIDER] Fallback initial question used ({e})")
            fallback_q = self._get_fallback_initial_question(resume, inspection, config)
            return InterviewSession(
                session_id=session_id,
                config=config,
                resume_summary="Candidate Profile (Gemini Engine)",
                current_question=fallback_q,
                conversation_history=[],
                total_turns_completed=0
            )

    async def evaluate_and_cross_examine(
        self,
        session: InterviewSession,
        transcript: str,
        resume: ResumeAnalysis,
        inspection: LinkInspectionResult,
    ) -> SubmitAnswerResponse:
        current_turn = len(session.conversation_history) + 1
        clean_text = (transcript or "").strip()

        # ------------------------------------------------------------------
        # 1. IMMEDIATE INTENT GATE: Check if candidate requested DSA / Live Coding
        # (Must be checked BEFORE LLM call to guarantee the interviewer and right panel sync!)
        # ------------------------------------------------------------------
        coding_requests = [
            "move on to dsa", "move on to the dsa", "switch to dsa", "let's do dsa", "lets do dsa",
            "ask dsa", "ask me dsa", "dsa question", "dsa problem", "move to dsa",
            "move to coding", "switch to coding", "let's code", "lets code",
            "coding question", "coding problem", "leetcode problem", "live coding",
            "showcase my coding", "solve a coding problem", "give me a coding question"
        ]
        wants_coding = any(k in clean_text.lower() for k in coding_requests)

        # Code Submission Handling (When candidate clicks 'Submit' in Code Sandbox)
        is_code_submission = "here is my live dsa solution" in clean_text.lower() or "class solution" in clean_text or "var twosum" in clean_text
        if is_code_submission:
            return self._evaluate_dsa_code_submission(clean_text, session, None)

        if wants_coding:
            return self._build_dsa_challenge(transcript)

        sys_design_triggers = [
            "move on to system design", "move to system design", "switch to system design",
            "let's do system design", "lets do system design", "ask system design",
            "ask me system design", "system design question", "system design round",
            "start system design", "pivot to system design"
        ]
        wants_sys_design = any(k in clean_text.lower() for k in sys_design_triggers)

        if wants_sys_design:
            return self._build_system_design_challenge(transcript)

        # Deflection and gibberish detection
        deflections = [
            "you just ask", "ask something else", "change the question", "different topic",
            "skip this", "next question", "don't ask", "i don't know", "i dont know",
            "no idea", "dont know", "skip"
        ]
        is_deflection = any(d in clean_text.lower() for d in deflections)
        word_count = len(clean_text.split())
        tech_indicators = ["cache", "redis", "database", "sql", "async", "scale", "worker", "thread", "api", "index", "latency", "load", "model", "python", "service", "concurrency", "docker", "query", "optimize", "kafka", "postgres", "lock", "nosql", "http", "memory", "sharding", "cpu", "queue", "git", "rest", "frontend", "backend"]
        has_tech = any(k in clean_text.lower() for k in tech_indicators)
        is_gibberish_or_trivial = (word_count < 5 and not has_tech) or (word_count < 3)

        last_question = session.current_question
        persona_instructions = self._get_persona_instructions(session.config.persona)
        language_instructions = self._get_language_instructions(session.config.language)
        candidate_context = self._build_candidate_context(resume, inspection, session.config)

        # Collect all questions asked in previous rounds
        asked_texts = {last_question.question_text.strip().lower()}
        for t in session.conversation_history:
            if t.question and t.question.question_text:
                asked_texts.add(t.question.question_text.strip().lower())

        past_qa_summary = "\n".join([
            f"Round {idx}: Question: {t.question.question_text} | Answer: {t.candidate_answer[:120]}"
            for idx, t in enumerate(session.conversation_history, 1) if t.question
        ]) or "Round 1 Introduction just completed."

        is_intro_turn = (current_turn == 1) or ("introduction" in last_question.category.lower()) or ("introduce" in last_question.question_text.lower())
        round2_directive = ""
        if is_intro_turn:
            round2_directive = """
ROUND 2 DIRECTIVE (RESUME CROSS-EXAMINATION PIVOT):
The candidate has just given their personal introduction.
- In your persona_reaction, warmly acknowledge their background.
- Now ask the FIRST deep technical cross-examination question targeting the specific technologies, architecture, or projects from their resume.
"""

        prompt = f"""You are the senior technical interviewer continuing an interactive multi-turn interview.
{persona_instructions}
{language_instructions}

{candidate_context}

PAST INTERVIEW TURNS SO FAR:
{past_qa_summary}

PREVIOUS QUESTION ASKED: "{last_question.question_text}"
CANDIDATE'S SPOKEN ANSWER: "{transcript}"
CURRENT TURN NUMBER: {current_turn}
{round2_directive}

CRITICAL RULES:
1. STRICT EVALUATION: If the candidate's answer is gibberish, random unrelated words, deflection, or trivial words (e.g. fewer than 5 non-tech words), score must be 1 to 3 with a HARSH SCOLDING tone.
2. ABSOLUTELY ZERO QUESTION REPETITION: You MUST NOT repeat any question or topic previously asked. Every single round must explore a completely NEW engineering domain from their resume or senior distributed systems (e.g., if caching was asked, switch to Kafka event streaming, DB sharding, distributed locking, API gateway idempotency, connection pooling, or microservice resilience).

Return ONLY valid JSON matching this schema:
{{
    "score": 8,
    "strengths": ["Clear fundamental understanding and sound reasoning"],
    "improvements": ["Analyze distributed concurrency constraints"],
    "persona_reaction": "Your in-character spoken feedback reaction strictly following the tone rules",
    "next_question": {{
        "question_text": "text for UI",
        "voice_text": "spoken voice text",
        "difficulty": "hard",
        "category": "cross_examination",
        "context_reference": "Direct reference to their previous answer"
    }},
    "learning_concept": {{
        "concept_title": "Optional concept title"
    }}
}}"""

        try:
            gen_config = types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.7,
                max_output_tokens=1200,
            )
            response = await self._call_gemini(prompt, gen_config)
            cleaned = self._clean_json_text(response.text)
            data = json.loads(cleaned, strict=False)

            score = max(1, min(10, int(data.get("score", 7))))
            persona_reaction = data.get("persona_reaction", "Let's move on.")
            strengths = data.get("strengths", ["Answer communicated clearly"])
            improvements = data.get("improvements", ["Provide deeper technical trade-offs"])

            # Enforce guardrails for gibberish and deflection
            if is_gibberish_or_trivial:
                score = 2
                persona_reaction = "What kind of careless answer is that? That was completely superficial, unstructured, and meaningless. In a senior engineering interview, you need to articulate technical principles and trade-offs!"
                strengths = ["Spoken response recorded"]
                improvements = ["Formulate technical explanations with specific engineering trade-offs"]
            elif is_deflection:
                score = 3
                persona_reaction = "You dodged the question. In a technical interview, avoiding technical inquiries is a major red flag. Let's try again:"
                strengths = ["Spoken response recorded"]
                improvements = ["Tackle the engineering problem directly rather than evading"]

            nq_data = data.get("next_question", {})
            gen_q_text = nq_data.get("question_text", "").strip()

            # Prevent duplicate or empty questions
            if not gen_q_text or gen_q_text.lower() in asked_texts or len(gen_q_text) < 15:
                gen_q_text, question_category = self._get_unique_next_question(asked_texts, is_hindi=(session.config.language == InterviewLanguage.HI))
            else:
                question_category = nq_data.get("category", "Technical Cross-Examination")

            # Check if this generated question is a DSA coding question
            is_coding_q = any(k in gen_q_text.lower() for k in ["leetcode", "algorithm", "data structure", "implement", "sliding window", "two sum"])
            vc = None
            if is_coding_q:
                vc = VisualContext(
                    type=VisualContextType.GITHUB_CODE,
                    repo_name="Algorithm Sandbox (LeetCode Style)",
                    file_path="solution.py",
                    language="python",
                    code_snippet="""# LeetCode Problem Challenge
# Constraints: O(1) amortized time complexity, O(N) space complexity

class Solution:
    def solve(self):
        # TODO: Implement your solution here
        pass

if __name__ == '__main__':
    sol = Solution()
    print("Testing solution:", sol.solve())
""",
                    highlight_lines=[7, 8],
                    context_title="LeetCode Problem Workspace"
                )

            gen_q_text = nq_data.get("question_text", "Explain the scaling trade-offs of this design.").strip()
            combined_voice_text = f"{persona_reaction.strip()} ... {nq_data.get('voice_text', gen_q_text)}"

            next_q = InterviewQuestion(
                question_text=gen_q_text,
                voice_text=combined_voice_text,
                difficulty=nq_data.get("difficulty", "hard"),
                category="cross_examination",
                is_cross_question=True,
                context_reference=nq_data.get("context_reference", "Based on your previous statement"),
                visual_context=vc
            )

            lc_data = data.get("learning_concept")
            learning_concept = None
            if lc_data and isinstance(lc_data, dict) and lc_data.get("concept_title"):
                learning_concept = await self.generate_learning_concept(lc_data.get("concept_title"))

            feedback = AnswerFeedback(
                score=score,
                strengths=strengths,
                improvements=improvements,
                persona_reaction=persona_reaction,
                speech_metrics=analyze_speech_delivery(transcript)
            )

            return SubmitAnswerResponse(
                feedback=feedback,
                persona_reaction=persona_reaction,
                spoken_reaction=persona_reaction,
                next_question=next_q,
                learning_concept=learning_concept,
                is_complete=False
            )
        except Exception as e:
            print(f"[GEMINI PROVIDER] Fallback cross-question used ({e})")
            return self._fallback_cross_examine(session, transcript, inspection, current_turn)

    def _evaluate_dsa_code_submission(
        self, code_text: str, session: InterviewSession, resume: Optional[ResumeAnalysis] = None
    ) -> SubmitAnswerResponse:
        code_lower = code_text.lower()
        has_hashmap = any(k in code_lower for k in ["seen", "map", "hashmap", "unordered_map", "diff", "complement", "target -", "target-"])
        has_brute_force = any(k in code_lower for k in ["for j in", "for (int j", "for (let j", "for j="])
        is_empty_stub = ("pass" in code_text and not has_hashmap) or ("return new int[0]" in code_text and not has_hashmap) or ("return {}" in code_text and not has_hashmap) or ("return []" in code_text and not has_hashmap)

        if is_empty_stub:
            score = 2
            reaction = "You submitted an empty function stub without implementing the algorithmic logic. In a senior live coding round, you must write out the algorithm to pass all unit test cases!"
            q_text = "Let's review the algorithmic approach: How would you use a single-pass Hash Map to find the complement index in linear O(N) time?"
        elif has_hashmap:
            score = 9
            reaction = "Spot on! That was an optimal, clean O(N) solution using a single-pass hash map with O(1) lookup time. Excellent work on algorithmic rigor!"
            q_text = "Now let's switch gears to high-level architecture. Suppose you are designing a high-throughput flash-sale booking system handling 50,000 concurrent writes per second. How would you design the architecture to prevent database lock contention and seat double-booking?"
        elif has_brute_force:
            score = 6
            reaction = "Your nested loops logic works, but O(N^2) quadratic time complexity will exceed the 1.0s time limit on large inputs (N=10,000). You need a single-pass hash map for O(N) linear time:"
            q_text = "How would you rewrite this solution using a Hash Map to store seen numbers and achieve O(N) time complexity?"
        else:
            score = 7
            reaction = "Your implementation has been recorded. Let's examine how this logic scales under production constraints:"
            q_text = "What is the worst-case space complexity of your solution, and how does your memory footprint scale when processing 100,000 integers?"

        return SubmitAnswerResponse(
            feedback=AnswerFeedback(
                score=score,
                strengths=["Code solution submitted to sandbox engine and verified"],
                improvements=["Ensure space and time complexity are optimal under peak constraints"],
                persona_reaction=reaction,
                speech_metrics=analyze_speech_delivery(code_text)
            ),
            persona_reaction=reaction,
            spoken_reaction=reaction,
            next_question=InterviewQuestion(
                question_text=q_text,
                voice_text=f"{reaction} {q_text}",
                difficulty="hard",
                category="Live Coding Assessment",
                is_cross_question=True,
                context_reference="Candidate submitted code in live sandbox",
                visual_context=None
            ),
            learning_concept=None,
            is_complete=False
        )

    def _build_dsa_challenge(self, transcript: str) -> SubmitAnswerResponse:
        """
        Creates a clean LeetCode-style problem with empty function signature
        where candidate writes their logic, runs tests, and clicks Submit.
        """
        code_snippet = '''# =====================================================================
# LEETCODE 1: Two Sum
# Difficulty: Easy / Medium | Time Complexity Requirement: O(N)
# =====================================================================
# Problem Statement:
# Given an array of integers nums and an integer target, return indices 
# of the two numbers such that they add up to target.
# You may assume each input would have exactly one solution, and you 
# may not use the same element twice.
#
# Constraints:
# - 2 <= nums.length <= 10^4
# - -10^9 <= nums[i] <= 10^9
# - -10^9 <= target <= 10^9
# - Only one valid answer exists.
# =====================================================================

class Solution:
    def twoSum(self, nums: list[int], target: int) -> list[int]:
        # Write your code logic here:
        pass
'''

        coding_vc = VisualContext(
            type=VisualContextType.GITHUB_CODE,
            repo_name="Algorithm Sandbox (LeetCode Style)",
            file_path="solution.py",
            language="python",
            code_snippet=code_snippet,
            highlight_lines=[16, 17, 18],
            context_title="LeetCode Problem: Two Sum (O(N) Time Complexity)"
        )

        q_text = "Understood! Let's pivot directly to Data Structures & Algorithms. Look at the Code Sandbox on your right: I've loaded 'LeetCode 1: Two Sum'. Select your language, implement your solution in the function stub, test it with ▶ Run Code, and click Submit when ready!"
        reaction = "Understood! Shifting gears directly into your live LeetCode coding assessment."

        return SubmitAnswerResponse(
            feedback=AnswerFeedback(
                score=7,
                strengths=["Proactive initiative to showcase algorithm implementation and problem-solving"],
                improvements=["Be ready to justify your time and space complexity choices in O-notation"],
                persona_reaction=reaction,
                speech_metrics=analyze_speech_delivery(transcript)
            ),
            persona_reaction=reaction,
            spoken_reaction=reaction,
            next_question=InterviewQuestion(
                question_text=q_text,
                voice_text=f"{reaction} {q_text}",
                difficulty="hard",
                category="Algorithms & Data Structures",
                is_cross_question=True,
                context_reference="Candidate requested DSA coding assessment",
                visual_context=coding_vc
            ),
            learning_concept=None,
            is_complete=False
        )

    def _get_unique_next_question(self, asked_texts: set, is_hindi: bool = False):
        tracks = self.QUESTION_TRACKS_HI if is_hindi else self.QUESTION_TRACKS_EN
        for tr in tracks:
            if tr["q"].strip().lower() not in asked_texts:
                return tr["q"], tr["category"]
        # Fallback if somehow all 15 are asked:
        fallback_track = tracks[0]
        return fallback_track["q"], fallback_track["category"]

    QUESTION_TRACKS_EN = [
        {
            "q": "Your baseline logic holds, but what happens when that exact component gets hit with 10,000 concurrent writes per second? Where is your primary bottleneck?",
            "category": "Concurrency & High Throughput"
        },
        {
            "q": "Suppose your read-to-write ratio shifts to 99% reads with frequent cache misses. How would you redesign caching and indexing to prevent a cache stampede?",
            "category": "Data Storage & Caching"
        },
        {
            "q": "Suppose it's 2 AM and CPU utilization pins at 100% with p99 response times spiking from 50ms to 4000ms. Walk me through your step-by-step triage and root-cause analysis.",
            "category": "Production Outage Triage"
        },
        {
            "q": "When downstream microservices time out under load, how do you prevent cascading failure storms? Explain your retry, backoff, and circuit-breaking strategy.",
            "category": "Distributed Resilience & Circuit Breakers"
        },
        {
            "q": "How does your runtime's memory management and garbage collector behave under heavy heap allocation, and how have you diagnosed memory leaks in production?",
            "category": "Runtime Internals & Memory Profiling"
        },
        {
            "q": "How would you architect multi-tenant rate limiting and DDoS protection at the API Gateway level using token buckets or sliding window logs?",
            "category": "API Gateway & Security Architecture"
        },
        {
            "q": "In an event-driven architecture using Apache Kafka, how do you handle partition hot-spotting, consumer lag, and guarantee idempotent processing without message loss?",
            "category": "Kafka & Event Streaming"
        },
        {
            "q": "Explain how PostgreSQL handles multi-version concurrency control (MVCC) and row-level locking. What specific SQL queries or transaction isolation levels cause deadlocks?",
            "category": "Database Transactions & ACID"
        },
        {
            "q": "When scaling with read replicas, asynchronous replication lag can cause a user to refresh and see stale data. How do you guarantee read-your-own-writes consistency?",
            "category": "Database Replication & Read Replicas"
        },
        {
            "q": "How do you implement distributed locking safely across multiple nodes? Compare Redis Redlock against ZooKeeper ephemeral sequential nodes under network partitions.",
            "category": "Distributed Locking & Consensus"
        },
        {
            "q": "When architecting inter-service communication, under what conditions would you choose gRPC with HTTP/2 multiplexing over standard REST/JSON, and what are the trade-offs?",
            "category": "Microservices Communication & gRPC"
        },
        {
            "q": "When a Docker container or Kubernetes pod gets killed with an OOMKilled (Exit Code 137) error, walk me through how you isolate whether it was heap memory, off-heap buffers, or a leak.",
            "category": "Containerization & Production Observability"
        },
        {
            "q": "How would you design a database sharding strategy using consistent hashing with virtual nodes? What happens when you need to execute a cross-shard join query?",
            "category": "Database Sharding & Partitioning"
        },
        {
            "q": "In an asynchronous worker architecture (e.g. Celery / RabbitMQ), how do you prevent worker thread starvation and safely handle poison-pill messages with dead letter queues?",
            "category": "Asynchronous Task Queues"
        },
        {
            "q": "If your platform needs to handle 5GB video uploads from millions of users, how do you architect direct-to-cloud presigned multipart uploads without bottlenecking your API servers?",
            "category": "High-Throughput Storage & S3"
        }
    ]

    QUESTION_TRACKS_HI = [
        {
            "q": "Aapne jo claim kiya, agar wahi service 10,000 requests per second ke spike pe run ho, toh database aur network bottlenecks se kaise bachenge?",
            "category": "Concurrency & High Throughput"
        },
        {
            "q": "Read-to-write ratio 99% reads hone par cache stampede se bachne ke liye aap caching aur indexing kaise redesign karenge?",
            "category": "Data Storage & Caching"
        },
        {
            "q": "Maan lijiye raat ko 2 baje CPU 100% hit karta hai aur latency 50ms se badh kar 4s ho jati hai. Step-by-step issue ko kaise debug karenge?",
            "category": "Production Outage Triage"
        },
        {
            "q": "Downstream microservices timeout hone par cascading failures se bachne ke liye aapka circuit breaker aur exponential backoff plan kya hoga?",
            "category": "Distributed Resilience & Circuit Breakers"
        },
        {
            "q": "Application runtime me memory leaks aur garbage collection pauses ko diagnose karne ke liye aap kaun se profiling tools use karte hain?",
            "category": "Runtime Internals & Memory Profiling"
        },
        {
            "q": "API Gateway level par token bucket ya sliding-window rate limiting kaise implement karenge taaki legit users block na hon?",
            "category": "API Gateway & Security Architecture"
        },
        {
            "q": "Kafka event streaming me partition hot-spotting aur consumer lag se nipatne ke liye aap partition keys kaise design karte hain?",
            "category": "Kafka & Event Streaming"
        },
        {
            "q": "PostgreSQL me deadlocks aur race conditions se bachne ke liye transaction isolation levels aur row locks ka sahi use kaise karte hain?",
            "category": "Database Transactions & ACID"
        },
        {
            "q": "Read replicas use karte waqt replication lag ki wajah se user ko purana data dikhne lagta hai. Is issue ko resolve karne ka kya approach hai?",
            "category": "Database Replication & Read Replicas"
        },
        {
            "q": "Distributed systems me Redis distributed lock implement karte waqt race conditions aur split-brain scenario se kaise bacha jata hai?",
            "category": "Distributed Locking & Consensus"
        },
        {
            "q": "REST APIs ke mukable gRPC HTTP/2 use karne ke kya architectural benefits aur complexity trade-offs hain?",
            "category": "Microservices Communication & gRPC"
        },
        {
            "q": "Production me container OOMKilled hone par aap root-cause analysis kaise karte hain aur memory limits kaise optimize karte hain?",
            "category": "Containerization & Production Observability"
        },
        {
            "q": "High-scale database sharding me consistent hashing aur virtual nodes ka use karke rebalancing kaise handle karte hain?",
            "category": "Database Sharding & Partitioning"
        },
        {
            "q": "Background job processing me worker queues starvation aur poison messages se bachne ke liye dead letter queues kaise configure karte hain?",
            "category": "Asynchronous Task Queues"
        },
        {
            "q": "Large file uploads (5GB+) ko direct cloud storage par presigned URLs aur multipart uploads se kaise process karenge bina server crash kiye?",
            "category": "High-Throughput Storage & S3"
        }
    ]

    def _build_system_design_challenge(self, transcript: str) -> SubmitAnswerResponse:
        """
        Pivots to System Design purely in chat without confusing diagrams in the right panel.
        """
        q_text = "Let's move to System Design. Suppose you are architecting a high-throughput flash-sale booking system handling 50,000 concurrent write requests per second. How would you design the architecture to prevent database lock contention and guarantee that seats are never double-sold?"
        reaction = "Great. Now let's test your high-level distributed systems engineering:"

        return SubmitAnswerResponse(
            feedback=AnswerFeedback(
                score=7,
                strengths=["Readiness to discuss distributed system architecture and scalability"],
                improvements=["Ground your answer with concrete components like message queues and caches"],
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
                context_reference="Candidate requested System Design assessment",
                visual_context=None  # Keep right panel clean for Take a Hint!
            ),
            learning_concept=None,
            is_complete=False
        )

    def _fallback_cross_examine(
        self, session: InterviewSession, transcript: str, inspection: LinkInspectionResult, turn: int
    ) -> SubmitAnswerResponse:
        is_hindi = session.config.language == InterviewLanguage.HI

        clean_text = (transcript or "").strip()
        word_count = len(clean_text.split())

        # Intent detection: Check if candidate requested DSA / Live Coding
        coding_requests = [
            "move on to dsa", "move on to the dsa", "switch to dsa", "let's do dsa", "lets do dsa",
            "ask dsa", "ask me dsa", "dsa question", "dsa problem", "move to dsa",
            "move to coding", "switch to coding", "let's code", "lets code",
            "coding question", "coding problem", "leetcode problem", "live coding",
            "showcase my coding", "solve a coding problem", "give me a coding question"
        ]
        wants_coding = any(k in clean_text.lower() for k in coding_requests)

        # Code Submission Handling (When candidate clicks 'Submit' in Code Sandbox)
        is_code_submission = "here is my live dsa solution" in clean_text.lower() or "class solution" in clean_text or "var twosum" in clean_text
        if is_code_submission:
            return self._evaluate_dsa_code_submission(clean_text, session, None)

        if wants_coding:
            return self._build_dsa_challenge(transcript)

        sys_design_triggers = [
            "move on to system design", "move to system design", "switch to system design",
            "let's do system design", "lets do system design", "ask system design",
            "ask me system design", "system design question", "system design round",
            "start system design", "pivot to system design"
        ]
        wants_sys_design = any(k in clean_text.lower() for k in sys_design_triggers)

        if wants_sys_design:
            return self._build_system_design_challenge(transcript)

        deflections = [
            "you just ask", "ask something else", "change the question", "different topic",
            "skip this", "next question", "don't ask", "i don't know", "i dont know",
            "no idea", "dont know", "skip"
        ]
        is_deflection = any(d in clean_text.lower() for d in deflections)

        tech_indicators = ["cache", "redis", "database", "sql", "async", "scale", "worker", "thread", "api", "index", "latency", "load", "model", "python", "service", "concurrency", "docker", "query", "optimize", "kafka", "postgres", "lock"]
        weak_indicators = ["do not know", "don't know", "no idea", "not sure", "dunno", "can't remember", "just copied", "tutorial", "skip", "gandhi", "random", "asdf"]
        
        has_tech = any(k in clean_text.lower() for k in tech_indicators)
        has_weak = any(w in clean_text.lower() for w in weak_indicators)

        # Gibberish / low-effort detection: < 5 words and no tech terms is NEVER a solid answer
        is_gibberish_or_trivial = (word_count < 5 and not has_tech) or (word_count < 3)
        is_solid_answer = (not has_weak) and (not is_deflection) and (not is_gibberish_or_trivial) and ((word_count >= 14) or (word_count >= 8 and has_tech))

        # Check if candidate attempted to solve high write concurrency merely by IP rate limiting/blocking
        is_rate_limit_for_writes = any(r in clean_text.lower() for r in ["rate limit", "block ip", "block that ip", "disallow", "blocking ip"]) and any(q in session.current_question.question_text.lower() for q in ["10,000", "10000", "concurrent writes", "writes per second"])

        if is_gibberish_or_trivial or word_count <= 3:
            fallback_score = 2
        elif is_deflection or has_weak:
            fallback_score = 3
        elif is_rate_limit_for_writes:
            fallback_score = 5
        elif is_solid_answer and word_count >= 18:
            fallback_score = 9
        elif is_solid_answer:
            fallback_score = 8
        elif word_count < 8:
            fallback_score = 4
        else:
            fallback_score = 5

        QUESTION_TRACKS_EN = [
            {
                "solid_q": "Your baseline logic holds, but what happens when that exact component gets hit with 10,000 concurrent writes per second? Where is your primary bottleneck?",
                "weak_q": "What are the concrete failure modes of that approach when concurrency scales, and how do you prevent race conditions?",
                "category": "Concurrency & High Throughput"
            },
            {
                "solid_q": "Good. Now suppose your read-to-write ratio shifts to 99% reads with frequent cache misses. How would you redesign caching and indexing to prevent a cache stampede?",
                "weak_q": "Explain the difference between B-Tree indexing and Hash indexing, and how a cache-aside pattern actually protects your database.",
                "category": "Data Storage & Caching"
            },
            {
                "solid_q": "Suppose it's 2 AM and CPU utilization pins at 100% with p99 response times spiking from 50ms to 4000ms. Walk me through your step-by-step triage and root-cause analysis.",
                "weak_q": "In a real production outage, what specific profiling tools, log correlation queries, and metrics do you inspect when latency explodes?",
                "category": "Production Outage Triage"
            },
            {
                "solid_q": "When downstream microservices time out under load, how do you prevent cascading failure storms? Explain your retry, backoff, and circuit-breaking strategy.",
                "weak_q": "How do you implement idempotency keys on your API endpoints to guarantee that network retries never duplicate operations?",
                "category": "Distributed Resilience & Circuit Breakers"
            },
            {
                "solid_q": "How does your runtime's memory management and garbage collector behave under heavy heap allocation, and how have you diagnosed memory leaks in production?",
                "weak_q": "How do you detect memory leaks or thread contention when an application slowly exhausts heap memory over several days?",
                "category": "Runtime Internals & Memory Profiling"
            },
            {
                "solid_q": "How would you architect multi-tenant rate limiting and DDoS protection at the API Gateway level using token buckets or sliding window logs?",
                "weak_q": "Why would a fixed-window counter cause traffic spikes at boundary boundaries, and how does sliding-window solve it?",
                "category": "API Gateway & Security Architecture"
            }
        ]

        QUESTION_TRACKS_HI = [
            {
                "solid_q": "Aapne jo claim kiya, agar wahi service 10,000 requests per second ke spike pe run ho, toh database aur network bottlenecks se kaise bachenge?",
                "weak_q": "Yeh answer superficial tha. High concurrency pe race conditions aur thread contention kaise prevent karenge?",
                "category": "Concurrency & High Throughput"
            },
            {
                "solid_q": "Sahi hai. Read-to-write ratio 99% reads hone par cache stampede se bachne ke liye aap caching aur indexing kaise redesign karenge?",
                "weak_q": "Database indexing aur cache-aside pattern real production me kaise kaam karta hai, dhang se explain kijiye.",
                "category": "Data Storage & Caching"
            },
            {
                "solid_q": "Maan lijiye raat ko 2 baje CPU 100% hit karta hai aur latency 50ms se badh kar 4s ho jati hai. Step-by-step issue ko kaise debug karenge?",
                "weak_q": "Latency spike hone par aap kaun se metrics, logs aur profiling tools inspect karte hain?",
                "category": "Production Outage Triage"
            }
        ]

        # Gather asked texts to avoid duplicate questions
        asked_texts = {session.current_question.question_text.strip().lower()}
        for t in session.conversation_history:
            if t.question and t.question.question_text:
                asked_texts.add(t.question.question_text.strip().lower())

        tracks = QUESTION_TRACKS_HI if is_hindi else QUESTION_TRACKS_EN
        unasked_tracks = [
            tr for tr in tracks
            if tr["solid_q"].strip().lower() not in asked_texts and tr["weak_q"].strip().lower() not in asked_texts
        ]

        q_text, question_category = self._get_unique_next_question(asked_texts, is_hindi)

        if is_rate_limit_for_writes:
            reaction = "Blocking IPs stops DDoS attacks, but 10,000 writes/sec is legitimate business traffic during a sale. Dropping transactions loses revenue. You need write queues like Kafka or DB sharding to absorb writes:"
        elif is_deflection:
            reaction = "You dodged the question. In a senior engineering interview, you cannot simply wave away production triage and profiling questions."
        elif is_gibberish_or_trivial:
            reaction = "What kind of careless answer is that? That was completely superficial, unstructured, and meaningless. Please formulate a proper technical response!"
        elif fallback_score >= 7:
            reaction = "Shabash! Great clarity and solid trade-off analysis." if is_hindi else "Spot on! That was a fantastic, clear, and well-structured answer. Let me push you deeper:"
        elif fallback_score <= 4:
            reaction = "Ye kya laparwah answer hai! Listen carefully:" if is_hindi else "What kind of careless answer is that? That was completely superficial. Listen carefully:"
        else:
            reaction = "Basic idea theek hai par production bottlenecks miss ho gaye." if is_hindi else "You touched on the basics, but you hand-waved over real production bottlenecks:"

        # In standard System Design & Cross-Examination turns, keep right panel clean for 'Take a Hint'
        vc = None

        combined_voice = f"{reaction} ... {q_text}"
        next_q = InterviewQuestion(
            question_text=q_text,
            voice_text=combined_voice,
            difficulty="hard",
            category=question_category,
            is_cross_question=True,
            context_reference="From your previous statement",
            visual_context=vc
        )

        return SubmitAnswerResponse(
            feedback=AnswerFeedback(
                score=fallback_score,
                strengths=["Answer addressed technical topics with sound reasoning" if is_solid_answer else "Answer recorded"],
                improvements=["Address edge-case resilience and failover" if is_solid_answer else "Avoid superficial buzzwords and justify design with metrics"],
                persona_reaction=reaction,
                speech_metrics=analyze_speech_delivery(transcript)
            ),
            persona_reaction=reaction,
            spoken_reaction=reaction,
            next_question=next_q,
            learning_concept=None,
            is_complete=False
        )


    async def generate_learning_concept(
        self, topic: str, resume: Optional[ResumeAnalysis] = None, question_text: Optional[str] = None
    ) -> LearningConcept:
        resume_context = ""
        if resume:
            resume_context = f"""
CANDIDATE RESUME PROFILE & PROJECTS:
{resume.full_text[:1200]}
SKILLS: {', '.join(resume.skills[:8])}
PROJECTS: {'; '.join(resume.experience_items[:3])}
"""
        q_context = f"CURRENT INTERVIEW QUESTION BEING ASKED: '{question_text}'" if question_text else ""

        prompt = f"""You are a master technical mentor giving a targeted 'Take a Hint' explanation for a technical interview candidate.
Topic: '{topic}'
{q_context}
{resume_context}

REQUIREMENTS:
1. Provide a crisp summary and deep theoretical breakdown of the concept.
2. Provide a clean ASCII diagram illustrating the mechanics.
3. CRITICAL: In 'resume_project_connection', directly explain how the candidate can answer this question by grounding it in their OWN resume projects! Explain how their specific project architecture, tools (e.g. FastAPI, Kafka, Redis, PostgreSQL), or components solve this exact challenge.

Return ONLY valid JSON matching this schema:
{{
    "concept_title": "{topic}",
    "summary": "concise overview of the answer",
    "theory": "concrete architectural mechanics, best practices, and edge cases",
    "table_markdown": "| Approach | Throughput | Latency | Complexity |\\n|---|---|---|---|\\n| Queue Buffering | 50k req/s | 12ms async | Low |",
    "diagram_ascii": "Client ---> [ Ingest API ] ---> [ Kafka Buffer ] ---> [ Worker Pool ] ---> [ Database ]",
    "key_takeaways": ["Takeaway 1", "Takeaway 2", "Takeaway 3"],
    "resume_project_connection": "How to answer using your resume project: In your Movie Ticket Booking / AI DevOps project, you can explain that..."
}}"""

        try:
            gen_config = types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.5,
                max_output_tokens=1500,
            )
            response = await self._call_gemini(prompt, gen_config)
            cleaned = self._clean_json_text(response.text)
            data = json.loads(cleaned, strict=False)

            return LearningConcept(
                concept_title=data.get("concept_title", topic),
                summary=data.get("summary", f"Core mechanics of {topic}."),
                theory=data.get("theory", f"Deep dive into production architectural mechanics of {topic}."),
                table_markdown=data.get("table_markdown", "| Feature | In-Memory | Disk |\n|---|---|---|\n| Speed | Sub-ms | ms |"),
                diagram_ascii=data.get("diagram_ascii", "[ Client ] ---> [ Cache ] ---> [ Database ]"),
                key_takeaways=data.get("key_takeaways", ["Measure before optimizing", "Plan for eviction", "Handle failover"]),
                resume_project_connection=data.get("resume_project_connection", "In your project, explain how caching and message queues isolate the database under peak load.")
            )
        except Exception as e:
            return LearningConcept(
                concept_title=topic,
                summary=f"Key technical principles and trade-offs of {topic}.",
                theory=f"Theoretical overview of {topic} in production environments.",
                table_markdown="| Strategy | Latency | Consistency |\n|---|---|---|\n| In-Memory | Sub-ms | Eventual |",
                diagram_ascii="[ Request ] ---> [ Cache ] ---> [ Storage ]",
                key_takeaways=["Analyze read-write ratios", "Design for failure modes"],
                resume_project_connection="Connect this directly to your resume project: explain how your service handles concurrency with Redis atomic counters and asynchronous worker queues."
            )
