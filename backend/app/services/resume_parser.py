import io
import re
from typing import List
import pdfplumber
import docx
from app.schemas.models import ResumeAnalysis
from app.utils.url_extractor import extract_urls_from_text

class ResumeParser:
    """
    Parses resume files (PDF, DOCX) to extract text, skills, experience, and links.
    WHY: The raw text is needed for the LLM context, and structured data helps with routing.
    """
    async def parse(self, file_content: bytes, filename: str) -> ResumeAnalysis:
        text = ""
        
        # 1. Extract Text
        if filename.lower().endswith('.pdf'):
            text = self._parse_pdf(file_content)
        elif filename.lower().endswith('.docx'):
            text = self._parse_docx(file_content)
        else:
            raise ValueError("Unsupported file format. Only PDF and DOCX are supported.")

        # 2. Extract URLs
        extracted_urls = extract_urls_from_text(text)
        
        # 3. Extract Skills (Basic heuristic, relies mostly on LLM later)
        skills = self._extract_skills(text)
        
        # 4. Extract Experience (Basic heuristic)
        experience_items = self._extract_experience(text)

        return ResumeAnalysis(
            full_text=text,
            skills=skills,
            experience_items=experience_items,
            extracted_urls=extracted_urls
        )

    def _parse_pdf(self, file_content: bytes) -> str:
        """
        WHY: Using pdfplumber over PyPDF2 because it can better handle layouts and
        sometimes extracts hyperlinks directly if they are annotated.
        """
        text = ""
        with pdfplumber.open(io.BytesIO(file_content)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
                
                # Also try to grab hyperlinked URLs if they exist in annotations
                if page.hyperlinks:
                    for link in page.hyperlinks:
                        if 'uri' in link:
                            text += f" {link['uri']} "
        return text

    def _parse_docx(self, file_content: bytes) -> str:
        text = ""
        doc = docx.Document(io.BytesIO(file_content))
        for para in doc.paragraphs:
            text += para.text + "\n"
        return text

    def _extract_skills(self, text: str) -> List[str]:
        # Simple heuristic, real implementation would use NLP or an exhaustive list
        common_skills = ["Python", "Java", "C++", "JavaScript", "React", "Node.js", "AWS", "Docker", "Kubernetes", "SQL", "Machine Learning"]
        found = []
        for skill in common_skills:
            if re.search(r'\b' + re.escape(skill) + r'\b', text, re.IGNORECASE):
                found.append(skill)
        return found

    def _extract_experience(self, text: str) -> List[str]:
        # Heuristic to find job titles. 
        # For a full app, we might just let the LLM do this during the interview generation.
        lines = text.split('\n')
        exp = []
        for line in lines:
            if "Software Engineer" in line or "Developer" in line or "Manager" in line:
                if len(line) < 100: # Exclude long sentences that just mention it
                    exp.append(line.strip())
        return exp

resume_parser = ResumeParser()
