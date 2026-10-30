# ResumeGrind — System Architecture Document

## Overview

ResumeGrind is a serverless AI-powered mock interviewer that combines resume parsing, deep link inspection, and voice-based interviewing with real-time code visualization.

---

## High-Level Architecture

```mermaid
graph TB
    subgraph Client["Browser (Client-Side)"]
        UI[React SPA]
        WSA[Web Speech API]
        UI --> WSA
    end

    subgraph CDN["AWS CloudFront"]
        CF[CDN Edge Locations]
    end

    subgraph API_Layer["API Layer"]
        AG[API Gateway - HTTP API]
    end

    subgraph Compute["Serverless Compute"]
        LF[Lambda Function]
        subgraph FastAPI["FastAPI Application"]
            RP[Resume Parser Service]
            LI[Link Inspector Service]
            AI[AI Interviewer Service]
            S3S[S3 Service]
        end
        LF --> FastAPI
    end

    subgraph Storage["Data Layer"]
        S3R[(S3 - Resume Files)]
        DDB[(DynamoDB - Sessions)]
    end

    subgraph External["External APIs"]
        GH[GitHub REST API]
        GM[Google Gemini AI]
        WEB[Portfolio Websites]
    end

    Client -->|HTTPS| CF
    CF -->|Static Files| UI
    CF -->|/api/*| AG
    AG --> LF
    RP --> S3R
    LI --> GH
    LI --> WEB
    AI --> GM
    S3S --> S3R
    FastAPI --> DDB
```

---

## Data Flow

### Phase 1: Resume Upload & Parsing

```mermaid
sequenceDiagram
    participant B as Browser
    participant API as API Gateway
    participant L as Lambda/FastAPI
    participant S3 as S3 Bucket

    B->>API: POST /api/upload-resume (multipart/form-data)
    API->>L: Forward request
    L->>L: Parse PDF with pdfplumber
    L->>L: Extract text + hyperlink annotations
    L->>L: Classify URLs (GitHub/LinkedIn/Portfolio)
    L->>L: Extract skills and experience items
    L-->>B: ResumeAnalysis JSON
```

**Why `pdfplumber`?**
Most PDF libraries (PyPDF2, pdfminer) only extract visible text. But resume URLs are often embedded as hyperlink annotations — the URL is clickable but the visible text shows something else (e.g., "My Portfolio" links to `https://portfolio.dev`). `pdfplumber` extracts these annotations, catching URLs that text-only extraction would miss.

### Phase 2: Deep Link Inspection

```mermaid
sequenceDiagram
    participant B as Browser
    participant L as Lambda/FastAPI
    participant GH as GitHub API
    participant WEB as Portfolio Sites

    B->>L: POST /api/inspect-links [URLs]
    
    par Concurrent Crawling
        L->>GH: GET /repos/{owner}/{repo}
        L->>GH: GET /repos/{owner}/{repo}/languages
        L->>GH: GET /repos/{owner}/{repo}/readme
        L->>GH: GET /repos/{owner}/{repo}/contents/{file}
        L->>WEB: GET portfolio-site.com
    end

    GH-->>L: Repo metadata + source files
    WEB-->>L: HTML page content
    L->>L: Parse HTML with BeautifulSoup
    L-->>B: LinkInspectionResult (repos, code, metadata)
```

**Why Async Concurrent Crawling?**
A resume typically contains 3-8 URLs. Crawling them sequentially with `requests` takes 3-8 seconds. Using `httpx` with `asyncio.gather()`, we crawl all URLs simultaneously in ~1 second. This is a fundamental backend optimization pattern.

### Phase 3: Voice Interview with Live Code Display

```mermaid
sequenceDiagram
    participant U as Candidate (Voice)
    participant B as Browser (React)
    participant L as Lambda/FastAPI
    participant GM as Gemini AI

    B->>L: POST /api/start-interview
    L->>GM: Generate questions from resume + code context
    GM-->>L: Questions with visual_context
    L-->>B: InterviewSession (questions + code snippets)

    loop For Each Question
        B->>B: Display code in CodeInspector panel
        B->>U: AI Voice speaks question (SpeechSynthesis)
        U->>B: Candidate speaks answer (SpeechRecognition)
        B->>B: Transcribe speech to text
        B->>L: POST /api/submit-answer {transcript}
        L->>GM: Evaluate answer quality
        GM-->>L: Score + feedback + follow-up
        L-->>B: AnswerFeedback
    end

    B->>L: GET /api/session-report/{id}
    L-->>B: SessionReport (scores + recommendations)
```

---

## Design Decisions

### Why Serverless (Lambda) Over EC2/Containers?

| Factor | Lambda (Our Choice) | EC2 / ECS |
|--------|-------------------|-----------|
| **Scaling** | Auto-scales 0→1000+ instantly | Manual scaling, load balancers |
| **Cost at zero traffic** | $0.00 | ~$8.50/month (t2.micro) |
| **Maintenance** | Zero server management | OS patches, security updates |
| **Cold starts** | ~1-2s first request | None (always running) |
| **Best for** | Sporadic traffic (portfolio projects) | Steady high traffic |

### Why DynamoDB Over PostgreSQL/MongoDB?

For interview session data (JSON documents with TTL), DynamoDB is ideal:
- **Serverless**: No database server to manage
- **Schema-flexible**: Store varied question/answer structures naturally
- **TTL**: Auto-delete old sessions (privacy + cost control)
- **Free tier**: 25GB storage is more than enough

### Why Web Speech API Over OpenAI Whisper / ElevenLabs?

| Factor | Web Speech API (Our Choice) | Server-Side AI Voice |
|--------|---------------------------|---------------------|
| **Cost** | $0 (browser-native) | $0.006-$0.015 per request |
| **Latency** | Instant (no network round-trip) | 200-500ms API call |
| **Privacy** | Audio stays on device | Audio sent to third-party server |
| **Quality** | Good (depends on browser/OS) | Premium (more natural) |
| **Offline** | Works offline | Requires internet |

---

## Security Considerations

1. **S3 Presigned URLs**: Resume files are never publicly accessible. Time-limited, authenticated URLs control access.
2. **CORS Configuration**: In production, restrict origins to your CloudFront domain only.
3. **Environment Variables**: API keys stored in Lambda environment variables (encrypted at rest by AWS).
4. **DynamoDB TTL**: Interview data auto-deletes after 7 days.
5. **S3 Lifecycle**: Resume files auto-delete after 30 days.
6. **IAM Least Privilege**: Lambda function only has access to its specific S3 bucket and DynamoDB table.
