"""
End-to-End Interview Flow Test Script
Simulates a complete 5-round interview as a student using the Ollama custom model.
Tests: Session start -> Answer submission -> DSA pivot -> System Design -> Report
"""
import httpx
import json
import sys
import time

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

BASE = "http://127.0.0.1:8000/api"

def pj(data):
    print(json.dumps(data, indent=2, ensure_ascii=False)[:2000])

# ============================================
# STEP 1: Upload resume (simulate with text)
# ============================================
print("=" * 60)
print("STEP 1: Preparing resume analysis and inspection data")
print("=" * 60)

resume_analysis = {
    "full_text": "Rahul Upadhyay - AI Backend Engineer with experience in Python, Java, FastAPI, Docker, Kubernetes, and Kafka. Projects: 1) AI DevOps Log Analyzer using LLM-powered log analysis. 2) Scalable Movie Ticket Booking System handling 10k concurrent users with Redis caching and PostgreSQL. 3) ResumeGrind - AI Voice Mock Interviewer.",
    "skills": ["Python", "Java", "FastAPI", "Docker", "Kubernetes", "Kafka", "Redis", "PostgreSQL", "LLM", "AI Agents"],
    "experience_items": [
        "Built AI DevOps Log Analyzer with LLM-powered log analysis",
        "Designed scalable movie ticket booking system for 10k concurrent users",
        "Created ResumeGrind AI Voice Mock Interviewer"
    ],
    "extracted_urls": []
}

inspection_result = {
    "github_repos": [],
    "portfolio_data": [],
    "linkedin_data": None
}

# ============================================
# STEP 2: Start interview with Ollama custom model
# ============================================
print("\n" + "=" * 60)
print("STEP 2: Starting interview session (provider: ollama_local)")
print("=" * 60)

start_payload = {
    "resume_analysis": resume_analysis,
    "inspection_result": inspection_result,
    "config": {
        "language": "en",
        "persona": "strict_roast",
        "provider": "ollama_local"
    }
}

t0 = time.time()
r = httpx.post(f"{BASE}/start-interview", json=start_payload, timeout=120.0)
elapsed = time.time() - t0
print(f"Status: {r.status_code} | Time: {elapsed:.1f}s")

if r.status_code != 200:
    print("ERROR starting interview:")
    pj(r.json())
    sys.exit(1)

session = r.json()
session_id = session["session_id"]
question = session["current_question"]

print(f"\nSession ID: {session_id}")
print(f"Resume Summary: {session.get('resume_summary', 'N/A')}")
print(f"\n--- OPENING QUESTION (Round 1) ---")
print(f"question_text: {repr(question['question_text'])}")
print(f"voice_text: {repr(question.get('voice_text', ''))}")
print(f"category: {question.get('category', 'N/A')}")
print(f"question_text length: {len(question['question_text'])}")

# Check for the "h" bug
if len(question["question_text"]) <= 5:
    print(f"\n!!! BUG DETECTED: question_text is only '{question['question_text']}' (length {len(question['question_text'])})")
    print("This is the 'h' bug - model returned truncated/malformed output")

# ============================================
# STEP 3: Submit introduction answer (Round 1)
# ============================================
print("\n" + "=" * 60)
print("STEP 3: Submitting introduction answer (Round 1)")
print("=" * 60)

answer1 = "Hello my name is Rahul Upadhyay and I am an AI backend engineer. I have built several projects including an AI DevOps Log Analyzer where users send log queries and my LLM analyzes and resolves issues. I also built a scalable movie ticket booking system using Redis caching and PostgreSQL that handles 10,000 concurrent users with proper connection pooling and write-ahead logging."

submit_payload = {
    "session_id": session_id,
    "transcript": answer1
}

t0 = time.time()
r = httpx.post(f"{BASE}/submit-answer", json=submit_payload, timeout=120.0)
elapsed = time.time() - t0
print(f"Status: {r.status_code} | Time: {elapsed:.1f}s")

if r.status_code != 200:
    print("ERROR submitting answer:")
    pj(r.json())
    sys.exit(1)

result1 = r.json()
print(f"\nScore: {result1['feedback']['score']}/10")
print(f"Reaction: {result1['persona_reaction']}")
print(f"Strengths: {result1['feedback']['strengths']}")
print(f"Improvements: {result1['feedback']['improvements']}")
if result1.get("next_question"):
    nq = result1["next_question"]
    print(f"\n--- NEXT QUESTION (Round 2) ---")
    print(f"question_text: {repr(nq['question_text'])}")
    print(f"category: {nq.get('category', 'N/A')}")
    print(f"question_text length: {len(nq['question_text'])}")

# ============================================
# STEP 4: Submit technical answer (Round 2)
# ============================================
print("\n" + "=" * 60)
print("STEP 4: Submitting technical answer (Round 2)")
print("=" * 60)

answer2 = "For handling 10,000 concurrent writes per second in my ticket booking system, I implemented an asynchronous event-driven architecture using Kafka as a write buffer. The API immediately acknowledges with a booking ticket ID, and background consumer workers batch insert into partitioned PostgreSQL tables. I also used Redis atomic counters with Lua scripts for seat availability checks to prevent double-booking race conditions."

submit_payload2 = {
    "session_id": session_id,
    "transcript": answer2
}

t0 = time.time()
r = httpx.post(f"{BASE}/submit-answer", json=submit_payload2, timeout=120.0)
elapsed = time.time() - t0
print(f"Status: {r.status_code} | Time: {elapsed:.1f}s")

if r.status_code == 200:
    result2 = r.json()
    print(f"\nScore: {result2['feedback']['score']}/10")
    print(f"Reaction: {result2['persona_reaction']}")
    if result2.get("next_question"):
        nq2 = result2["next_question"]
        print(f"\n--- NEXT QUESTION (Round 3) ---")
        print(f"question_text: {repr(nq2['question_text'])}")
        print(f"category: {nq2.get('category', 'N/A')}")

# ============================================
# STEP 5: Request DSA coding pivot (Round 3)
# ============================================
print("\n" + "=" * 60)
print("STEP 5: Requesting DSA coding pivot (Round 3)")
print("=" * 60)

answer3 = "Can you give me a data structures and algorithms question? I want to showcase my coding skills and solve a problem in the code editor."

submit_payload3 = {
    "session_id": session_id,
    "transcript": answer3
}

t0 = time.time()
r = httpx.post(f"{BASE}/submit-answer", json=submit_payload3, timeout=120.0)
elapsed = time.time() - t0
print(f"Status: {r.status_code} | Time: {elapsed:.1f}s")

if r.status_code == 200:
    result3 = r.json()
    print(f"\nScore: {result3['feedback']['score']}/10")
    print(f"Reaction: {result3['persona_reaction']}")
    if result3.get("next_question"):
        nq3 = result3["next_question"]
        print(f"\n--- DSA QUESTION ---")
        print(f"question_text: {repr(nq3['question_text'])}")
        print(f"category: {nq3.get('category', 'N/A')}")
        vc = nq3.get("visual_context")
        if vc:
            print(f"visual_context.type: {vc.get('type', 'N/A')}")
            print(f"visual_context.code_snippet present: {bool(vc.get('code_snippet'))}")
            print(f"Has Code Editor: YES")
        else:
            print(f"Has Code Editor: NO (visual_context is missing!)")

# ============================================
# STEP 6: Submit deflection (Round 4) - test deflection catching
# ============================================
print("\n" + "=" * 60)
print("STEP 6: Testing deflection detection (Round 4)")
print("=" * 60)

answer4 = "I don't know about this topic. Can we just skip it and ask something else?"

submit_payload4 = {
    "session_id": session_id,
    "transcript": answer4
}

t0 = time.time()
r = httpx.post(f"{BASE}/submit-answer", json=submit_payload4, timeout=120.0)
elapsed = time.time() - t0
print(f"Status: {r.status_code} | Time: {elapsed:.1f}s")

if r.status_code == 200:
    result4 = r.json()
    print(f"\nScore: {result4['feedback']['score']}/10")
    print(f"Reaction: {result4['persona_reaction']}")
    if result4['feedback']['score'] >= 7:
        print("!!! BUG: Deflection scored 7+ (should be 1-4)")

print("\n" + "=" * 60)
print("INTERVIEW FLOW TEST COMPLETE")
print("=" * 60)
