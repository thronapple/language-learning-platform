"""
Web scraping utilities for content extraction from URLs.
"""
import logging
import requests
from urllib.parse import urlparse
from typing import Optional, List, Dict, Any

try:
    from bs4 import BeautifulSoup  # type: ignore
except ImportError:  # pragma: no cover
    BeautifulSoup = None  # type: ignore

from ..infra.exceptions import ExternalServiceError, ValidationError

logger = logging.getLogger(__name__)


class WebScraper:
    """Handles web content extraction with domain validation and rate limiting."""

    def __init__(self, whitelist_domains: List[str], timeout: int = 10):
        """
        Initialize web scraper with configuration.

        Args:
            whitelist_domains: List of allowed domains for scraping
            timeout: Request timeout in seconds
        """
        self.whitelist_domains = [domain.lower() for domain in whitelist_domains]
        self.timeout = timeout
        self.headers = {
            "User-Agent": "LanguageLearningBot/1.0 (+https://example.com/bot)",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
        }

    def is_allowed_domain(self, url: str) -> bool:
        """
        Check if URL domain is in the whitelist.

        Args:
            url: URL to validate

        Returns:
            True if domain is allowed, False otherwise
        """
        try:
            parsed = urlparse(url)
            hostname = (parsed.hostname or "").lower()

            if not hostname:
                return False

            return any(hostname.endswith(domain) for domain in self.whitelist_domains)
        except Exception as e:
            logger.warning(f"Domain validation failed for URL: {url}", extra={"error": str(e)})
            return False

    def extract_content(self, url: str) -> Dict[str, Any]:
        """
        Extract text content from a web page.

        Args:
            url: URL to scrape

        Returns:
            Dictionary containing extracted content and metadata

        Raises:
            ValidationError: If URL domain is not allowed
            ExternalServiceError: If scraping fails
        """
        if not self.is_allowed_domain(url):
            parsed = urlparse(url)
            hostname = parsed.hostname or "unknown"
            raise ValidationError(f"Domain not allowed for scraping: {hostname}", "url")

        if BeautifulSoup is None:
            raise ExternalServiceError("BeautifulSoup not available - install beautifulsoup4", "scraper")

        try:
            logger.info(f"Scraping content from URL: {url}")

            response = requests.get(
                url,
                timeout=self.timeout,
                headers=self.headers,
                allow_redirects=True
            )
            response.raise_for_status()

            # Parse HTML content
            soup = BeautifulSoup(response.text, "html.parser")

            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "aside"]):
                script.decompose()

            # Extract content from preferred containers
            content_node = self._find_main_content(soup)

            if content_node:
                # Extract text while preserving structure
                text_content = self._extract_structured_text(content_node)
                title = self._extract_title(soup)

                result = {
                    "text": text_content,
                    "title": title,
                    "url": url,
                    "content_length": len(text_content),
                    "extraction_method": "structured"
                }

                logger.info(
                    "Successfully extracted content",
                    extra={
                        "url": url,
                        "content_length": len(text_content),
                        "title": title[:50] if title else None
                    }
                )

                return result
            else:
                # Fallback to basic text extraction
                return self._fallback_extraction(url, soup)

        except requests.RequestException as e:
            logger.error(f"HTTP request failed for URL: {url}", extra={"error": str(e)})
            raise ExternalServiceError(f"Failed to fetch URL: {str(e)}", "scraper")
        except Exception as e:
            logger.error(f"Content extraction failed for URL: {url}", extra={"error": str(e)})
            raise ExternalServiceError(f"Content extraction failed: {str(e)}", "scraper")

    def _find_main_content(self, soup) -> Optional[Any]:
        """Find the main content container in the HTML."""
        # Try common content containers in order of preference
        selectors = [
            "article",
            "main",
            "[role='main']",
            ".content",
            ".post-content",
            ".article-content",
            ".entry-content",
            "#content",
            "body"
        ]

        for selector in selectors:
            node = soup.select_one(selector)
            if node:
                return node

        return soup.body if soup.body else soup

    def _extract_structured_text(self, node) -> str:
        """Extract text while preserving paragraph structure."""
        paragraphs = []

        # Extract text from paragraphs and other text containers
        for element in node.find_all(['p', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li']):
            text = element.get_text(strip=True)
            if text and len(text) > 10:  # Filter very short texts
                paragraphs.append(text)

        if paragraphs:
            content = "\n".join(paragraphs)
        else:
            # Fallback to all text
            content = node.get_text(separator=" ", strip=True)

        # Limit content length to prevent excessive data
        return content[:8000] if content else ""

    def _extract_title(self, soup) -> Optional[str]:
        """Extract page title."""
        title_tag = soup.find("title")
        if title_tag:
            return title_tag.get_text(strip=True)

        # Try Open Graph title
        og_title = soup.find("meta", property="og:title")
        if og_title:
            return og_title.get("content", "").strip()

        # Try h1 as fallback
        h1 = soup.find("h1")
        if h1:
            return h1.get_text(strip=True)

        return None

    def _fallback_extraction(self, url: str, soup) -> Dict[str, Any]:
        """Fallback extraction method when structured extraction fails."""
        parsed = urlparse(url)
        hostname = parsed.hostname or "unknown"

        # Generate basic segments from URL path
        path_parts = [p for p in parsed.path.split("/") if p]
        segments = []

        if path_parts:
            segments = [
                f"Imported from {hostname}",
                *[part.replace("-", " ").replace("_", " ") for part in path_parts[:5]]
            ]
        else:
            segments = [f"Imported from {hostname}"]

        result = {
            "text": f"Content from: {url}",
            "title": f"Import from {hostname}",
            "url": url,
            "content_length": len(url),
            "segments": segments,
            "extraction_method": "fallback"
        }

        logger.warning(
            "Used fallback extraction method",
            extra={"url": url, "hostname": hostname}
        )

        return result

    def get_domain_info(self, url: str) -> Dict[str, str]:
        """
        Extract domain information from URL.

        Args:
            url: URL to analyze

        Returns:
            Dictionary with domain information
        """
        try:
            parsed = urlparse(url)
            return {
                "hostname": parsed.hostname or "",
                "scheme": parsed.scheme or "http",
                "path": parsed.path or "/",
                "domain": (parsed.hostname or "").lower()
            }
        except Exception as e:
            logger.warning(f"Failed to parse URL: {url}", extra={"error": str(e)})
            return {
                "hostname": "",
                "scheme": "http",
                "path": "/",
                "domain": ""
            }