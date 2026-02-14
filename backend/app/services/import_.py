import logging
from typing import Tuple, List

from ..schemas.import_ import ImportRequest
from ..repositories.interfaces import Repository
from ..infra.config import settings
from ..infra.exceptions import ValidationError, ExternalServiceError
from .text_processor import TextProcessor
from .web_scraper import WebScraper

logger = logging.getLogger(__name__)


class ImportService:
    """
    Orchestrates content import from various sources.

    Coordinates between text processing, web scraping, and content storage
    while maintaining separation of concerns.
    """

    def __init__(
        self,
        repo: Repository,
        text_processor: TextProcessor | None = None,
        web_scraper: WebScraper | None = None
    ) -> None:
        self.repo = repo
        self.text_processor = text_processor or TextProcessor()
        self.web_scraper = web_scraper or WebScraper(
            whitelist_domains=settings.import_whitelist or [],
            timeout=10
        )

    def run(self, payload: ImportRequest) -> Tuple[str, List[str]]:
        """
        Import content from text or URL source.

        Args:
            payload: Import request containing type and content

        Returns:
            Tuple of (content_id, segments)

        Raises:
            ValidationError: If input is invalid
            ExternalServiceError: If external service fails
        """
        try:
            if payload.type == "text":
                return self._import_text(payload.payload)
            elif payload.type == "url":
                return self._import_url(payload.payload)
            else:
                raise ValidationError(f"Unsupported import type: {payload.type}", "type")

        except (ValidationError, ExternalServiceError):
            # Re-raise our custom exceptions
            raise
        except Exception as e:
            logger.error(
                "Unexpected error during import",
                extra={"type": payload.type, "error": str(e)}
            )
            raise ExternalServiceError(f"Import failed: {str(e)}", "import")

    def _import_text(self, text: str) -> Tuple[str, List[str]]:
        """Import text content."""
        if not text or not text.strip():
            raise ValidationError("Text content cannot be empty", "text")

        logger.info("Importing text content", extra={"length": len(text)})

        # Process text
        cleaned_text = self.text_processor.clean_text(text)
        segments = self.text_processor.split_sentences(cleaned_text)
        estimated_level = self.text_processor.estimate_reading_level(cleaned_text)
        keywords = self.text_processor.extract_keywords(cleaned_text)

        # Create content document
        doc = {
            "type": "sentence",
            "level": estimated_level,
            "tags": ["import", "text"] + keywords[:3],  # Add top 3 keywords as tags
            "text": cleaned_text,
            "audio_url": None,
            "segments": segments,
        }

        content_id = self.repo.put("content", doc)
        logger.info(
            "Text import completed",
            extra={
                "content_id": content_id,
                "segments_count": len(segments),
                "estimated_level": estimated_level
            }
        )

        return content_id, segments

    def _import_url(self, url: str) -> Tuple[str, List[str]]:
        """Import content from URL."""
        if not url or not url.strip():
            raise ValidationError("URL cannot be empty", "url")

        logger.info("Importing URL content", extra={"url": url})

        try:
            # Extract content using web scraper
            extracted_data = self.web_scraper.extract_content(url)

            # Process extracted text
            text_content = extracted_data.get("text", "")
            title = extracted_data.get("title", "")

            if not text_content:
                # Use fallback data if no text extracted
                fallback_segments = extracted_data.get("segments", [])
                if not fallback_segments:
                    domain_info = self.web_scraper.get_domain_info(url)
                    fallback_segments = [f"Imported from {domain_info['hostname']}"]

                doc = {
                    "type": "sentence",
                    "level": "A1",
                    "tags": ["import", "url", "fallback"],
                    "text": f"URL: {url}",
                    "audio_url": None,
                    "segments": fallback_segments,
                    "source_url": url,
                    "title": title or "Imported Content"
                }

                content_id = self.repo.put("content", doc)
                return content_id, fallback_segments

            # Process extracted text content
            cleaned_text = self.text_processor.clean_text(text_content)
            segments = self.text_processor.split_sentences(cleaned_text)
            estimated_level = self.text_processor.estimate_reading_level(cleaned_text)
            keywords = self.text_processor.extract_keywords(cleaned_text)

            # Create content document
            doc = {
                "type": "sentence",
                "level": estimated_level,
                "tags": ["import", "url"] + keywords[:3],
                "text": cleaned_text[:2000],  # Limit stored text length
                "audio_url": None,
                "segments": segments,
                "source_url": url,
                "title": title or "Imported Content",
                "extraction_method": extracted_data.get("extraction_method", "unknown")
            }

            content_id = self.repo.put("content", doc)
            logger.info(
                "URL import completed",
                extra={
                    "content_id": content_id,
                    "url": url,
                    "segments_count": len(segments),
                    "estimated_level": estimated_level,
                    "extraction_method": extracted_data.get("extraction_method")
                }
            )

            return content_id, segments

        except (ValidationError, ExternalServiceError):
            # Re-raise our custom exceptions
            raise
        except Exception as e:
            logger.error(
                "URL import failed",
                extra={"url": url, "error": str(e)}
            )
            raise ExternalServiceError(f"Failed to import from URL: {str(e)}", "import")
