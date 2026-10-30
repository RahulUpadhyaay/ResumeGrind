import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY

def build_pdf(filename="Rahul_Upadhyay_Resume.pdf"):
    # Margins matching standard 0.5 inch (36pt)
    margin = 36
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        leftMargin=margin,
        rightMargin=margin,
        topMargin=30,
        bottomMargin=30
    )
    
    styles = getSampleStyleSheet()
    
    # Original Times-Roman Serif Typography
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Times-Bold',
        fontSize=18,
        leading=20,
        alignment=TA_CENTER,
        textColor=colors.black
    )
    
    contact_style = ParagraphStyle(
        'DocContact',
        parent=styles['Normal'],
        fontName='Times-Roman',
        fontSize=9.5,
        leading=12,
        alignment=TA_CENTER,
        textColor=colors.black
    )
    
    section_heading_style = ParagraphStyle(
        'SectionHeading',
        parent=styles['Normal'],
        fontName='Times-Bold',
        fontSize=10.5,
        leading=12,
        textColor=colors.black,
        spaceBefore=5,
        spaceAfter=2
    )
    
    body_style = ParagraphStyle(
        'BodyTextCustom',
        parent=styles['Normal'],
        fontName='Times-Roman',
        fontSize=9.5,
        leading=12,
        alignment=TA_JUSTIFY,
        textColor=colors.black
    )
    
    body_right_style = ParagraphStyle(
        'BodyRight',
        parent=body_style,
        alignment=2,
        fontName='Times-Roman',
        textColor=colors.black
    )
    
    bullet_style = ParagraphStyle(
        'BulletCustom',
        parent=styles['Normal'],
        fontName='Times-Roman',
        fontSize=9,
        leading=11.5,
        alignment=TA_JUSTIFY,
        leftIndent=12,
        firstLineIndent=-10,
        spaceAfter=2.5,
        textColor=colors.black
    )
    
    project_title_style = ParagraphStyle(
        'ProjectTitle',
        parent=styles['Normal'],
        fontName='Times-Bold',
        fontSize=9.5,
        leading=12,
        textColor=colors.black,
        spaceAfter=2
    )
    
    story = []
    
    # 1. Header Name & Contact
    story.append(Paragraph("RAHUL UPADHYAY", title_style))
    story.append(Spacer(1, 3))
    story.append(Paragraph("+91-8738871912 &nbsp;|&nbsp; rahul64828@gmail.com &nbsp;|&nbsp; linkedin.com/in/rahul-upadhyay &nbsp;|&nbsp; github.com/rahulupadhyay", contact_style))
    story.append(Spacer(1, 4))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.black, spaceBefore=1, spaceAfter=4))
    
    # Helper for Section Headers (Matching original underlined design)
    def add_section(header_text):
        story.append(Paragraph(header_text.upper(), section_heading_style))
        story.append(HRFlowable(width="100%", thickness=0.75, color=colors.black, spaceBefore=1, spaceAfter=4))

    # 2. Professional Summary
    add_section("PROFESSIONAL SUMMARY")
    summary_text = (
        "AI & Backend Engineer specializing in building scalable Retrieval-Augmented Generation (RAG) pipelines, "
        "production-ready REST APIs, and microservices architecture. Proficient in Python, FastAPI, Node.js, Express.js, "
        "Vector Databases (Qdrant), Redis, Docker, and AWS. Experienced in building secure authentication systems, "
        "high-concurrency backend services, and AI agent workflows."
    )
    story.append(Paragraph(summary_text, body_style))
    story.append(Spacer(1, 3))
    
    # 3. Education
    add_section("EDUCATION")
    
    edu1_left = "<b>G.L. BAJAJ INSTITUTE OF TECHNOLOGY AND MANAGEMENT</b><br/>" \
                "<i>Bachelor of Technology - Computer Science and Engineering with Specialization in AI</i>"
    edu1_right = "<b>Greater Noida, India</b><br/>" \
                 "CGPA: 7.25 &nbsp;|&nbsp; Sept. 2023 - July 2027"
    
    edu2_left = "<b>MERRY CITY SCHOOL</b><br/>" \
                "<i>Intermediate (2020 - 2022) &nbsp;|&nbsp; High School (2018 - 2020)</i>"
    edu2_right = "<b>Varanasi, India</b>"
    
    t_edu = Table([
        [Paragraph(edu1_left, body_style), Paragraph(edu1_right, body_right_style)],
        [Paragraph(edu2_left, body_style), Paragraph(edu2_right, body_right_style)]
    ], colWidths=[370, 170])
    
    t_edu.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('TOPPADDING', (0,0), (-1,-1), 1),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(t_edu)
    story.append(Spacer(1, 3))
    
    # 4. Technical Skills and Interests
    add_section("TECHNICAL SKILLS AND INTERESTS")
    skills_data = [
        ("AI / Machine Learning & LLMs:", "Large Language Models (LLMs), RAG (Retrieval-Augmented Generation), Agentic Workflows, PyTorch, LangChain, Prompt Engineering, Vector Databases (Qdrant, Pinecone), Fine-Tuning"),
        ("Programming Languages:", "Python, Java, JavaScript"),
        ("Frameworks & Libraries:", "FastAPI, Node.js, Express.js, PyTorch, OpenCV, NumPy, Pandas, Scikit-Learn"),
        ("Databases & Caching:", "MongoDB, SQL (PostgreSQL/MySQL), Redis (Caching & Distributed Locking), Vector Search"),
        ("Backend, Cloud & DevOps:", "REST API Design, Microservices, Docker, Docker Compose, AWS (EC2, S3), Git, GitHub, Rate Limiting, JWT Authentication, System Design"),
        ("Area of Interest:", "Artificial Intelligence, Backend Engineering, Cloud Systems, Competitive Programming")
    ]
    for label, val in skills_data:
        p_text = f"■ &nbsp;<b>{label}</b> {val}"
        story.append(Paragraph(p_text, bullet_style))
    story.append(Spacer(1, 3))
    
    # 5. Projects
    add_section("PROJECTS")
    
    # Project 1
    p1_head = "DevOps Copilot — Infrastructure & Log Analytics RAG Platform"
    p1_sub = "<font color='#333333'><i>(Python, FastAPI, Qdrant, Gemini LLM, PostgreSQL, Redis, JWT, Docker)</i></font>"
    story.append(Paragraph(f"<b>{p1_head}</b> {p1_sub}", project_title_style))
    
    p1_bullets = [
        "<b>Vector RAG Search Architecture:</b> Engineered an end-to-end RAG-powered log analytics system parsing live server error logs (Kubernetes, AWS, Nginx) and executing dense vector similarity search in Qdrant against indexed DevOps documentation with &lt;100ms retrieval latency.",
        "<b>AI Root-Cause Synthesis:</b> Integrated Google Gemini LLM with prompt engineering and context injection to synthesize automated root-cause analysis reports and exact terminal fix commands for system failures.",
        "<b>Security & Authentication:</b> Secured REST API endpoints using JWT Bearer authentication, role-based access control, and Bcrypt password hashing; persisted user scan history and audit reports in PostgreSQL.",
        "<b>Containerized Microservices:</b> Containerized FastAPI backend, Qdrant vector database, and Redis service using Docker &amp; Docker Compose for seamless single-command cloud deployment."
    ]
    for b in p1_bullets:
        story.append(Paragraph(f"• &nbsp;{b}", bullet_style))
        
    story.append(Spacer(1, 3))
    
    # Project 2
    p2_head = "Scalable Movie Ticket Booking Backend System"
    p2_sub = "<font color='#333333'><i>(Node.js, Express.js, PostgreSQL, Redis, JWT Authentication, REST API)</i></font>"
    story.append(Paragraph(f"<b>{p2_head}</b> {p2_sub}", project_title_style))
    
    p2_bullets = [
        "<b>High-Concurrency Ticket Locking:</b> Architected a high-throughput movie ticket booking REST API utilizing Redis distributed locks and atomic transactions to prevent double-booking of seats during peak traffic booking surges.",
        "<b>RESTful Services & Auth:</b> Implemented modular REST endpoints for user authentication (JWT + Bcrypt), movie/showtime management, and ticket reservations with strict request schema validation.",
        "<b>Database Design & ACID Compliance:</b> Designed an optimized PostgreSQL relational schema with indexed queries, foreign key constraints, and ACID-compliant transaction handling for seat status management.",
        "<b>Automated Expiration Queue:</b> Built an asynchronous Redis background worker queue to automatically release reserved seats if payment confirmation is not received within a 5-minute timeout window."
    ]
    for b in p2_bullets:
        story.append(Paragraph(f"• &nbsp;{b}", bullet_style))
        
    story.append(Spacer(1, 3))
    
    # 6. Achievements
    add_section("ACHIEVEMENTS")
    achievements = [
        "<b>Smart India Hackathon 2025:</b> Advanced to national-level SIH as one of the top 45 teams (selected from 350+ internal teams at the college level) for building innovative AI pattern recognition models.",
        "<b>LeetCode:</b> Solved 250+ coding questions on LeetCode demonstrating strong data structures, algorithms, and computational problem-solving proficiency."
    ]
    for a in achievements:
        story.append(Paragraph(f"• &nbsp;{a}", bullet_style))
        
    doc.build(story)
    print(f"Successfully generated {filename}")

if __name__ == "__main__":
    build_pdf()
