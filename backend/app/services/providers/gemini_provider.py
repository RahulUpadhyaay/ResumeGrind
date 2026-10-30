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
        top_skill = resume.skills[0] if resume.skills else "software engineering"
        second_skill = resume.skills[1] if len(resume.skills) > 1 else "system design"
        first_repo = inspection.github_repos[0] if inspection.github_repos else None
        repo_name = first_repo.repo_name if first_repo else None

        # Rich pool of randomized opening question templates
        if config.language == InterviewLanguage.HI:
            templates = [
                f"Welcome! Resume me aapne {top_skill} highlight kiya hai. Apne background ka overview dijiye aur batayein ki {top_skill} me aapne kaun si major production challenge solve ki hai?",
                f"Namaste! {top_skill} aur {second_skill} par kaam karte waqt aapne sabse bada architecture trade-off kya dekha? Apne favorite project ke baare me batayein.",
                f"Welcome to your technical interview. Aapne {top_skill} mention kiya hai. Apne baare me batayein aur walk me through a difficult bug or outage you debugged under pressure.",
            ]
            if repo_name:
                templates.append(f"Namaste! Aapke GitHub repo '{repo_name}' ko dekhte hue, mujhe is project ke system architecture aur design decisions ke baare me explain kijiye.")
        else:
            templates = [
                f"Welcome to your technical interview! Looking at your resume, you list {top_skill}. To kick off, introduce yourself and walk me through a challenging architectural problem you personally solved.",
                f"Welcome! You highlight experience with {top_skill} and {second_skill}. Give me a concise introduction and tell me about the most difficult production bug or outage you triaged.",
                f"Welcome. Let me jump straight into engineering trade-offs: introduce yourself, and explain a time with {top_skill} where you had to sacrifice convenience for raw performance.",
                f"Hello and welcome! Anyone can list {top_skill} on a resume. Tell me who you are, and walk me through an architectural decision you made that you would redesign differently today.",
                f"Welcome! Looking over your background, tell me about your engineering journey and walk me through the system design of a project you built recently that handled real load."
            ]
            if repo_name:
                templates.extend([
                    f"Welcome! Looking at your GitHub repository '{repo_name}', introduce yourself and walk me through the key architectural decisions behind this project.",
                    f"Hello! I noticed your repository '{repo_name}' on GitHub. To begin, tell me about your background and what technical trade-offs you made while building {repo_name}."
                ])

        q_text = random.choice(templates)
        vc = None
        if first_repo and first_repo.key_files:
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

        return InterviewQuestion(
            question_text=q_text,
            voice_text=q_text,
            difficulty="medium",
            category="introduction",
            is_cross_question=False,
            visual_context=vc
        )

    async def generate_session(
        self, resume: ResumeAnalysis, inspection: LinkInspectionResult, config: InterviewConfig
    ) -> InterviewSession:
        session_id = str(uuid.uuid4())
        context = self._build_candidate_context(resume, inspection, config)
        persona_instructions = self._get_persona_instructions(config.persona)
        language_instructions = self._get_language_instructions(config.language)

        prompt = f"""You are conducting a live technical interview.
{persona_instructions}
{language_instructions}

{context}

CRITICAL RANDOMNESS REQUIREMENT:
Generate the very FIRST opening question for this candidate from scratch.
- DO NOT use generic repetitive phrasing. Make every single opening question fresh, unique, and specific.
- Pick a random focus: (e.g. probe their top skill, OR question them on their GitHub repo code, OR ask about an architectural outage, OR ask about system scaling).

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
            "data structure", "algorithm", "dsa", "coding", "code", "leetcode",
            "problem solving", "showcase my coding", "write code", "solve a problem",
            "move on to the dsa", "switch to coding", "coding question"
        ]
        wants_coding = any(k in clean_text.lower() for k in coding_requests)

        if wants_coding:
            return self._build_dsa_challenge(transcript)

        sys_design_triggers = [
            "system design", "architecture", "scalability", "distributed system",
            "microservices", "sharding", "kafka", "caching", "rate limiting", "load balancer",
            "move on to system design", "switch to system design", "ask system design"
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

        prompt = f"""You are the technical interviewer continuing an interactive multi-turn interview.
{persona_instructions}
{language_instructions}

{candidate_context}

PREVIOUS QUESTION ASKED: "{last_question.question_text}"
CANDIDATE'S SPOKEN ANSWER: "{transcript}"
CURRENT TURN NUMBER: {current_turn}

CRITICAL EVALUATION RULES:
- If the candidate's answer is gibberish, random unrelated words, deflection, or lacks technical substance:
  Score must be 1 to 3 with a HARSH SCOLDING tone calling out the lack of engineering substance.
- Do NOT fabricate technical depth that the candidate did not mention.

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
            gen_q_text = nq_data.get("question_text", "Explain the scaling trade-offs of this design.").strip()
            
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

    def _build_dsa_challenge(self, transcript: str) -> SubmitAnswerResponse:
        """
        Creates a clean LeetCode-style problem with pure function signature
        where inputs/test cases are handled automatically behind the scenes.
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
        # Implement your O(N) logic here:
        seen = {}
        for i, num in enumerate(nums):
            diff = target - num
            if diff in seen:
                return [seen[diff], i]
            seen[num] = i
        return []
'''

        coding_vc = VisualContext(
            type=VisualContextType.GITHUB_CODE,
            repo_name="Algorithm Sandbox (LeetCode Style)",
            file_path="solution.py",
            language="python",
            code_snippet=code_snippet,
            highlight_lines=[17, 18, 19, 20, 21, 22, 23, 24],
            context_title="LeetCode Problem: Two Sum (O(N) Time Complexity)"
        )

        q_text = "Understood! Let's pivot directly to Data Structures & Algorithms. Look at the Code Sandbox on your right: I've loaded 'LeetCode 1: Two Sum' with constraints. Select your language from the dropdown, implement your function logic, and click ▶ Run Code to compile and verify against test cases!"
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
            "data structure", "algorithm", "dsa", "coding", "code", "leetcode",
            "problem solving", "showcase my coding", "write code", "move on to the dsa",
            "switch to coding", "coding question"
        ]
        wants_coding = any(k in clean_text.lower() for k in coding_requests)

        if wants_coding:
            return self._build_dsa_challenge(transcript)

        sys_design_triggers = [
            "system design", "architecture", "scalability", "distributed system",
            "microservices", "sharding", "kafka", "caching", "rate limiting", "load balancer",
            "move on to system design", "switch to system design", "ask system design"
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

        active_track = unasked_tracks[0] if unasked_tracks else tracks[(turn - 1) % len(tracks)]
        q_text = active_track["solid_q"] if is_solid_answer else active_track["weak_q"]
        question_category = active_track["category"]

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
