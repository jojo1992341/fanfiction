"""HTML cleaning and formatting utilities."""
from bs4 import BeautifulSoup
from config.settings import KINDLE_CSS
import logging
from .validation import validate_html_content

logger = logging.getLogger(__name__)

class HTMLCleaner:
    def __init__(self):
        self.preserved_attrs = ['id', 'class', 'href', 'src', 'lang', 'dir']

    def clean_for_kindle(self, html_content: str) -> str:
        """Clean and format HTML content for Kindle while preserving structure."""
        if not validate_html_content(html_content):
            return ""

        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Log initial content structure
            logger.debug(f"Initial HTML structure: {soup.prettify()[:200]}...")

            self._clean_attributes(soup)
            self._ensure_html_structure(soup)
            self._add_kindle_styles(soup)

            cleaned_content = str(soup)
            logger.debug(f"Cleaned content length: {len(cleaned_content)}")
            return cleaned_content

        except Exception as e:
            logger.error(f"Error cleaning HTML: {str(e)}")
            return html_content

    def _clean_attributes(self, soup: BeautifulSoup) -> None:
        """Remove unwanted attributes while keeping important ones."""
        for tag in soup.find_all():
            attrs = dict(tag.attrs)
            for attr in attrs:
                if attr not in self.preserved_attrs:
                    del tag[attr]

    def _ensure_html_structure(self, soup: BeautifulSoup) -> None:
        """Ensure proper HTML structure with html, head, and body tags."""
        if not soup.html:
            new_html = soup.new_tag('html')
            new_html['lang'] = 'fr'
            for child in soup.children:
                new_html.append(child)
            soup.clear()
            soup.append(new_html)

        if not soup.head:
            head = soup.new_tag('head')
            soup.html.insert(0, head)

        if not soup.body:
            body = soup.new_tag('body')
            for child in list(soup.html.children):
                if child != soup.head:
                    body.append(child)
            soup.html.append(body)

    def _add_kindle_styles(self, soup: BeautifulSoup) -> None:
        """Add Kindle-friendly CSS and meta tags."""
        style = soup.new_tag('style')
        style.string = KINDLE_CSS
        soup.head.append(style)

        meta_charset = soup.new_tag('meta')
        meta_charset['charset'] = 'utf-8'
        soup.head.insert(0, meta_charset)
