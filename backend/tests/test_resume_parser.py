import pytest
from app.utils.url_extractor import extract_urls_from_text
from app.schemas.models import UrlType
from app.services.resume_parser import resume_parser

def test_extract_urls_from_text():
    text = "Check out my github at https://github.com/johndoe and my repo https://github.com/johndoe/project. Also linkedin: https://linkedin.com/in/johndoe"
    urls = extract_urls_from_text(text)
    
    assert len(urls) == 3
    
    # Check typing
    types = [u.url_type for u in urls]
    assert UrlType.GITHUB_PROFILE in types
    assert UrlType.GITHUB_REPO in types
    assert UrlType.LINKEDIN in types

@pytest.mark.asyncio
async def test_parse_unsupported_file():
    with pytest.raises(ValueError):
        await resume_parser.parse(b"dummy data", "resume.txt")
