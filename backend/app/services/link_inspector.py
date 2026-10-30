import asyncio
import httpx
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Optional
from app.config import settings
from app.schemas.models import (
    ExtractedURL, UrlType, LinkInspectionResult, 
    GitHubRepoInfo, CodeFile
)
from app.services.rag_service import rag_service

class LinkInspector:
    """
    Intelligent Multi-Language Code & Link Crawler.
    Features:
    1. Heuristic ranking across all modern languages (Python, TS, Go, Rust, Java, C++, etc.).
    2. Optional GitHub Personal Access Token authentication to bypass rate limits (60 -> 5,000 req/hr).
    3. Resilient fallback against GitHub 403 / 404 responses.
    4. Async parallel indexing into RAG semantic vector store.
    """
    def __init__(self):
        self.timeout = 10.0

    def _get_headers(self) -> Dict[str, str]:
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "ResumeGrind-DeepLink-Crawler"
        }
        if settings.GITHUB_TOKEN:
            headers["Authorization"] = f"token {settings.GITHUB_TOKEN}"
        return headers

    async def inspect_all(self, urls: List[ExtractedURL]) -> LinkInspectionResult:
        github_repos: List[GitHubRepoInfo] = []
        portfolio_data: List[Dict[str, Any]] = []
        linkedin_data: Optional[Dict[str, Any]] = None

        tasks = []
        for url_obj in urls:
            if url_obj.url_type == UrlType.GITHUB_REPO:
                tasks.append(self._inspect_github_repo(url_obj.url))
            elif url_obj.url_type == UrlType.GITHUB_PROFILE:
                tasks.append(self._inspect_github_profile(url_obj.url))
            elif url_obj.url_type == UrlType.PORTFOLIO:
                tasks.append(self._inspect_portfolio(url_obj.url))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for url_obj, result in zip(urls, results):
            if isinstance(result, Exception):
                print(f"[LINK INSPECTOR] Error inspecting {url_obj.url}: {result}")
                continue
                
            if url_obj.url_type == UrlType.GITHUB_REPO and isinstance(result, GitHubRepoInfo):
                github_repos.append(result)
            elif url_obj.url_type == UrlType.GITHUB_PROFILE and isinstance(result, list):
                github_repos.extend(result)
            elif url_obj.url_type == UrlType.PORTFOLIO and isinstance(result, dict):
                portfolio_data.append(result)

        # Trigger RAG vector indexing in background for all crawled repositories
        for repo in github_repos:
            if repo.key_files:
                asyncio.create_task(rag_service.index_repository_code(repo.repo_name, repo.key_files))

        return LinkInspectionResult(
            github_repos=github_repos,
            portfolio_data=portfolio_data,
            linkedin_data=linkedin_data
        )

    def _score_tree_item(self, path: str) -> int:
        """Scores a repository file path to identify the most significant architectural files."""
        path_lower = path.lower()
        parts = path_lower.split('/')
        filename = parts[-1]
        extension = filename.split('.')[-1] if '.' in filename else ''

        # Skip tests, vendors, minified bundles, assets
        ignored_patterns = ['test', 'spec', 'node_modules', 'vendor', '.min.', 'dist', 'build', '.git', 'coverage', '__pycache__', 'package-lock']
        if any(ign in path_lower for ign in ignored_patterns):
            return -100

        valid_code_exts = {'py', 'ts', 'tsx', 'js', 'jsx', 'go', 'rs', 'java', 'kt', 'cpp', 'c', 'cs', 'rb', 'swift'}
        if extension not in valid_code_exts and filename not in ['dockerfile', 'docker-compose.yml']:
            return -50

        score = 0
        # Priority for shallow paths (root or 1 level deep)
        if len(parts) <= 2:
            score += 30
        elif len(parts) <= 4:
            score += 15

        # Priority for primary entrypoints
        if any(filename.startswith(p) for p in ['main.', 'app.', 'index.', 'server.', 'application.', 'run.']):
            score += 50

        # Priority for business logic modules
        if any(k in path_lower for k in ['service', 'controller', 'handler', 'route', 'model', 'engine', 'algo', 'lib', 'core']):
            score += 40

        # Architecture & deployment
        if filename in ['dockerfile', 'docker-compose.yml']:
            score += 25

        return score

    async def _inspect_github_repo(self, url: str) -> GitHubRepoInfo:
        parts = url.rstrip('/').split('github.com/')
        if len(parts) < 2:
            raise ValueError(f"Invalid GitHub URL: {url}")
        
        path_parts = parts[1].split('/')
        if len(path_parts) < 2:
            raise ValueError(f"Missing owner/repo in {url}")
            
        owner, repo = path_parts[0], path_parts[1]
        headers = self._get_headers()

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            # 1. Metadata
            meta_res = await client.get(f"https://api.github.com/repos/{owner}/{repo}", headers=headers)
            if meta_res.status_code == 403:
                print(f"[LINK INSPECTOR] GitHub rate limit reached for {url}")
                return GitHubRepoInfo(repo_name=repo, owner=owner, description="Rate limit reached on GitHub API")
            meta_res.raise_for_status()
            meta = meta_res.json()

            default_branch = meta.get('default_branch', 'main')

            # 2. Languages
            lang_res = await client.get(f"https://api.github.com/repos/{owner}/{repo}/languages", headers=headers)
            languages = lang_res.json() if lang_res.status_code == 200 else {}

            # 3. Readme
            readme_res = await client.get(
                f"https://api.github.com/repos/{owner}/{repo}/readme",
                headers={**headers, "Accept": "application/vnd.github.raw"}
            )
            readme = readme_res.text if readme_res.status_code == 200 else None

            # 4. Fetch key files via intelligent tree scoring
            key_files = []
            try:
                tree_res = await client.get(
                    f"https://api.github.com/repos/{owner}/{repo}/git/trees/{default_branch}?recursive=1",
                    headers=headers
                )
                if tree_res.status_code == 200:
                    tree = tree_res.json().get('tree', [])
                    # Score and sort code candidates
                    scored_files = []
                    for item in tree:
                        if item.get('type') == 'blob':
                            score = self._score_tree_item(item['path'])
                            if score > 0:
                                scored_files.append((score, item['path']))

                    scored_files.sort(key=lambda x: x[0], reverse=True)

                    # Fetch the top 3 scored files
                    for _, path in scored_files[:3]:
                        raw_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{default_branch}/{path}"
                        content_res = await client.get(raw_url, headers=headers)
                        if content_res.status_code == 200:
                            ext = path.split('.')[-1].lower() if '.' in path else 'text'
                            key_files.append(CodeFile(
                                file_path=path,
                                content=content_res.text[:2500],
                                language=ext
                            ))
            except Exception as e:
                print(f"[LINK INSPECTOR] Tree analysis error on {repo}: {e}")

            return GitHubRepoInfo(
                repo_name=meta.get('name', repo),
                owner=owner,
                description=meta.get('description'),
                languages=languages,
                readme_content=readme[:1500] if readme else None,
                key_files=key_files,
                stars=meta.get('stargazers_count', 0),
                topics=meta.get('topics', [])
            )

    async def _inspect_github_profile(self, url: str) -> List[GitHubRepoInfo]:
        username = url.rstrip('/').split('github.com/')[-1]
        headers = self._get_headers()
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            res = await client.get(f"https://api.github.com/users/{username}/repos?sort=updated&per_page=3", headers=headers)
            if res.status_code != 200:
                return []
            
            repos = res.json()
            tasks = [self._inspect_github_repo(repo['html_url']) for repo in repos if 'html_url' in repo]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            return [r for r in results if isinstance(r, GitHubRepoInfo)]

    async def _inspect_portfolio(self, url: str) -> Dict[str, Any]:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                res = await client.get(url, follow_redirects=True)
                res.raise_for_status()
                soup = BeautifulSoup(res.text, 'html.parser')
                
                title = soup.title.string if soup.title else ""
                meta_desc = soup.find('meta', attrs={'name': 'description'})
                desc = meta_desc['content'] if meta_desc else ""
                
                # Extract text from main tags
                text = " ".join([p.get_text() for p in soup.find_all(['p', 'h1', 'h2', 'h3'])])
                
                return {
                    "url": url,
                    "title": title,
                    "description": desc,
                    "content_snippet": text[:1000]
                }
        except Exception as e:
            print(f"[LINK INSPECTOR] Failed to crawl portfolio {url}: {e}")
            return {"url": url, "error": str(e)}

link_inspector = LinkInspector()
