# ResumeGrind — API Reference

Base URL: `http://localhost:8000` (development) | `https://<api-id>.execute-api.<region>.amazonaws.com/<stage>` (production)

---

## Health Check

### `GET /api/health`

Returns the server status.

**Response** `200 OK`
```json
{
  "status": "healthy",
  "service": "ResumeGrind API",
  "version": "1.0.0"
}
```

---

## Resume Upload & Parsing

### `POST /api/upload-resume`

Upload a PDF or DOCX resume file for parsing. Extracts text content, skills, experience items, and all embedded URLs.

**Request**: `multipart/form-data`
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `file` | File | Yes | PDF or DOCX resume file (max 10MB) |

**Response** `200 OK`
```json
{
  "full_text": "John Doe\nSoftware Engineer\n...",
  "skills": ["Python", "React", "AWS", "FastAPI", "Docker"],
  "experience_items": [
    "Software Engineer at TechCorp (2022-2024)",
    "Backend Intern at StartupXYZ (2021-2022)"
  ],
  "extracted_urls": [
    {
      "url": "https://github.com/johndoe/chat-app",
      "url_type": "github_repo"
    },
    {
      "url": "https://linkedin.com/in/johndoe",
      "url_type": "linkedin"
    },
    {
      "url": "https://johndoe.dev",
      "url_type": "portfolio"
    }
  ]
}
```

**Errors**:
- `400`: Invalid file type (only PDF and DOCX supported)
- `422`: No file provided

---

## Link Inspection

### `POST /api/inspect-links`

Deep-crawl a list of URLs extracted from a resume. For GitHub repos, fetches metadata, languages, README, and key source files. For portfolio sites, extracts metadata and technology stack.

**Request**: `application/json`
```json
{
  "urls": [
    { "url": "https://github.com/johndoe/chat-app", "url_type": "github_repo" },
    { "url": "https://johndoe.dev", "url_type": "portfolio" }
  ]
}
```

**Response** `200 OK`
```json
{
  "github_repos": [
    {
      "repo_name": "chat-app",
      "owner": "johndoe",
      "description": "Real-time chat with WebSocket support",
      "languages": { "Python": 65.2, "JavaScript": 30.1, "HTML": 4.7 },
      "readme_content": "# Chat App\nA real-time chat application...",
      "key_files": [
        {
          "file_path": "backend/server.py",
          "content": "from fastapi import FastAPI, WebSocket...",
          "language": "python"
        },
        {
          "file_path": "frontend/src/App.jsx",
          "content": "import React, { useState }...",
          "language": "javascript"
        }
      ],
      "stars": 12,
      "topics": ["websocket", "fastapi", "react", "real-time"]
    }
  ],
  "portfolio_data": [
    {
      "url": "https://johndoe.dev",
      "title": "John Doe - Software Engineer",
      "description": "Full-stack developer specializing in...",
      "technologies": ["React", "Node.js", "Python"]
    }
  ],
  "linkedin_data": null
}
```

---

## Start Interview Session

### `POST /api/start-interview`

Generate a full interview session with AI-generated questions based on the resume analysis and link inspection results.

**Request**: `application/json`
```json
{
  "resume_analysis": { /* ResumeAnalysis object from /upload-resume */ },
  "inspection_result": { /* LinkInspectionResult object from /inspect-links */ }
}
```

**Response** `200 OK`
```json
{
  "session_id": "sess_a1b2c3d4e5",
  "candidate_name": "John Doe",
  "resume_summary": "Experienced full-stack developer...",
  "questions": [
    {
      "question_text": "I noticed in your repository 'chat-app', you implemented a WebSocket handler in server.py. Can you explain how you handle client reconnections?",
      "voice_text": "I noticed in your chat app repository, you implemented a WebSocket handler in server dot py. Can you explain how you handle client reconnections?",
      "visual_context": {
        "type": "github_code",
        "repo_name": "chat-app",
        "file_path": "backend/server.py",
        "github_url": "https://github.com/johndoe/chat-app/blob/main/backend/server.py#L15-L42",
        "language": "python",
        "code_snippet": "@app.websocket('/ws/{client_id}')\nasync def websocket_endpoint(websocket: WebSocket, client_id: str):\n    await manager.connect(websocket, client_id)\n    ...",
        "highlight_lines": [3, 4, 8, 9],
        "context_title": "GitHub: chat-app / server.py (Lines 15-42)"
      },
      "difficulty": "medium",
      "category": "technical"
    },
    {
      "question_text": "Your portfolio mentions you built a real-time notification system. Walk me through the architecture decisions you made.",
      "voice_text": "Your portfolio mentions you built a real-time notification system. Walk me through the architecture decisions you made.",
      "visual_context": {
        "type": "live_project",
        "repo_name": null,
        "file_path": null,
        "github_url": null,
        "language": null,
        "code_snippet": null,
        "highlight_lines": [],
        "context_title": "Portfolio: johndoe.dev — Notification System"
      },
      "difficulty": "hard",
      "category": "system_design"
    }
  ]
}
```

---

## Submit Answer

### `POST /api/submit-answer`

Submit a candidate's transcribed answer for AI evaluation. Returns scoring, feedback, and optionally a follow-up question.

**Request**: `application/json`
```json
{
  "session_id": "sess_a1b2c3d4e5",
  "question_index": 0,
  "transcript": "So in my chat app, I used a connection manager class that maintains a dictionary of active WebSocket connections. When a client disconnects, the disconnect handler removes them from the dictionary and broadcasts a notification..."
}
```

**Response** `200 OK`
```json
{
  "score": 7,
  "strengths": "Good understanding of the connection manager pattern. Correctly identified the disconnect handling mechanism.",
  "improvements": "Could have discussed reconnection strategies like exponential backoff, message queuing during disconnection, and heartbeat mechanisms to detect stale connections.",
  "follow_up_question": {
    "question_text": "How would you handle the case where a client reconnects but missed messages while offline?",
    "voice_text": "How would you handle the case where a client reconnects but missed messages while offline?",
    "visual_context": null,
    "difficulty": "hard",
    "category": "technical"
  }
}
```

---

## Session Report

### `GET /api/session-report/{session_id}`

Get the complete interview performance report for a session.

**Response** `200 OK`
```json
{
  "session_id": "sess_a1b2c3d4e5",
  "overall_score": 72,
  "category_scores": {
    "technical": 75,
    "communication": 80,
    "project_knowledge": 65,
    "problem_solving": 70
  },
  "question_feedbacks": [
    {
      "question_index": 0,
      "question_text": "...",
      "candidate_answer": "...",
      "score": 7,
      "strengths": "...",
      "improvements": "..."
    }
  ],
  "recommendations": [
    "Deepen your understanding of WebSocket reconnection strategies",
    "Practice explaining system design decisions with concrete trade-offs",
    "Good communication skills — keep using structured answers"
  ]
}
```

**Errors**:
- `404`: Session not found or expired
