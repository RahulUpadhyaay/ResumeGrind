import re
from typing import List
from app.schemas.models import ExtractedURL, UrlType

def extract_urls_from_text(text: str) -> List[ExtractedURL]:
    """
    Extracts and classifies URLs from raw text.
    WHY: Identifying URLs allows the downstream inspector to scrape candidate projects
    and online presence to personalize the interview.
    """
    # Basic URL regex
    url_pattern = re.compile(r'(https?://[^\s]+|www\.[^\s]+)')
    raw_urls = url_pattern.findall(text)
    
    # Clean up trailing punctuation if caught in regex
    cleaned_urls = []
    for url in raw_urls:
        url = url.rstrip('.,;)]}')
        if not url.startswith('http'):
            url = 'https://' + url
        cleaned_urls.append(url)
        
    extracted = []
    for url in cleaned_urls:
        url_lower = url.lower()
        if 'github.com' in url_lower:
            # Check if it's a specific repo or profile
            # e.g. github.com/username/repo
            parts = url_lower.split('github.com/')
            if len(parts) > 1:
                path = parts[1].strip('/')
                if '/' in path:
                    url_type = UrlType.GITHUB_REPO
                else:
                    url_type = UrlType.GITHUB_PROFILE
            else:
                url_type = UrlType.OTHER
        elif 'linkedin.com' in url_lower:
            url_type = UrlType.LINKEDIN
        else:
            url_type = UrlType.PORTFOLIO # Assume other URLs are portfolios/personal sites for now
            
        extracted.append(ExtractedURL(url=url, url_type=url_type))
        
    return extracted
