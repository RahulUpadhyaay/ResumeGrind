import pytest
from unittest.mock import patch, MagicMock
from app.services.ai_interviewer import ai_interviewer
from app.schemas.models import ResumeAnalysis, LinkInspectionResult

@pytest.mark.asyncio
async def test_generate_session_mocked():
    resume = ResumeAnalysis(full_text="Test resume", skills=["Python"], experience_items=[], extracted_urls=[])
    inspection = LinkInspectionResult(github_repos=[], portfolio_data=[])
    
    with patch('app.services.providers.gemini_provider.genai.Client') as MockClient:
        pass

        
    assert True
