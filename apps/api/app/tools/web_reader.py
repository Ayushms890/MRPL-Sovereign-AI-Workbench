import re
import httpx
from app.tools.base import ToolResult

class WebReaderTool:
    name = "web_reader"
    description = (
        "Scrapes and reads the text/markdown content of a specific web URL. "
        "Use this tool after finding relevant URLs using web_search to read full documentation, articles, or web pages."
    )
    parameters = {
        "type": "object",
        "properties": {
            "url": {"type": "string", "description": "The full HTTP/HTTPS URL of the web page to scrape and read."},
        },
        "required": ["url"],
    }

    def execute(self, arguments: dict) -> ToolResult:
        result_text = self.run(arguments)
        return ToolResult(content=result_text)

    def run(self, arguments: dict) -> str:
        url = arguments.get("url", "").strip()
        if not url:
            return "Error: URL parameter is required."

        if not url.startswith(("http://", "https://")):
            return "Error: Invalid URL scheme. Must start with http:// or https://."

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }

        try:
            response = httpx.get(url, headers=headers, follow_redirects=True, timeout=12)
            response.raise_for_status()
        except httpx.TimeoutException:
            return f"Error: Request to {url} timed out after 12 seconds."
        except httpx.HTTPStatusError as exc:
            return f"Error: HTTP {exc.response.status_code} while fetching {url}."
        except httpx.HTTPError as exc:
            return f"Error: Could not fetch URL {url} ({exc})."

        html = response.text
        clean_text = self._strip_html_tags(html)
        
        if not clean_text:
            return f"Page at {url} loaded successfully, but contained no readable text content."

        # Limit return length for token safety
        truncated = clean_text[:4000]
        suffix = "\n\n...[Content truncated for length]" if len(clean_text) > 4000 else ""
        
        return f"### Page Content for: {url}\n\n{truncated}{suffix}"

    def _strip_html_tags(self, html: str) -> str:
        # Remove script and style elements
        text = re.sub(r"<(script|style).*?>.*?</\1>", "", html, flags=re.DOTALL | re.IGNORECASE)
        # Replace block tags with newline
        text = re.sub(r"<(p|div|h[1-6]|li|br|tr)[^>]*>", "\n", text, flags=re.IGNORECASE)
        # Strip all remaining tags
        text = re.sub(r"<[^>]+>", "", text)
        # Clean up whitespace
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        return "\n".join(lines)
