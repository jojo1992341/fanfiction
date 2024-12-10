from bs4 import BeautifulSoup
from config.settings import KINDLE_CSS
import logging

logger = logging.getLogger(__name__)

class HTMLCleaner:
    @staticmethod
    def clean_for_kindle(html_content: str) -> str:
        """Clean and format HTML content for Kindle while preserving structure."""
        if not html_content or not html_content.strip():
            logger.warning("Received empty HTML content")
            return ""

        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Log initial content structure
            logger.debug(f"Initial HTML structure: {soup.prettify()[:200]}...")

            # Preserve important attributes
            preserved_attrs = ['id', 'class', 'href', 'src', 'lang', 'dir']
            
            # Remove unwanted attributes while keeping important ones
            for tag in soup.find_all():
                attrs = dict(tag.attrs)
                for attr in attrs:
                    if attr not in preserved_attrs:
                        del tag[attr]

            # Ensure basic HTML structure
            if not soup.html:
                new_html = soup.new_tag('html')
                new_html['lang'] = 'fr'
                for child in soup.children:
                    new_html.append(child)
                soup.clear()
                soup.append(new_html)

            # Ensure head and body tags exist
            if not soup.head:
                head = soup.new_tag('head')
                soup.html.insert(0, head)

            if not soup.body:
                body = soup.new_tag('body')
                for child in list(soup.html.children):
                    if child != soup.head:
                        body.append(child)
                soup.html.append(body)

            # Add Kindle-friendly CSS
            style = soup.new_tag('style')
            style.string = KINDLE_CSS
            soup.head.append(style)

            # Add meta charset
            meta_charset = soup.new_tag('meta')
            meta_charset['charset'] = 'utf-8'
            soup.head.insert(0, meta_charset)

            cleaned_content = str(soup)
            logger.debug(f"Cleaned content length: {len(cleaned_content)}")
            return cleaned_content

        except Exception as e:
            logger.error(f"Error cleaning HTML: {str(e)}")
            return html_content
