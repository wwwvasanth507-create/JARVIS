"""
Structured Page Extraction and Web Search Module for JARVIS.
Extracts visible text, headings, forms, buttons, links, and search results without dumping raw HTML.
"""

from urllib.parse import quote_plus
import time
import logging
from typing import Any, Dict, List, Optional, Tuple

from jarvis.browser.session import BrowserSession
from jarvis.browser.state import BrowserActionResult, SearchResult

logger = logging.getLogger("jarvis.browser.extraction")


class BrowserExtraction:
    """Extracts structured text content, links, forms, and search engine results."""

    def __init__(self, session: BrowserSession):
        self.session = session

    def read_page(self, max_chars: int = 10000, max_links: int = 30) -> Dict[str, Any]:
        """
        Extracts lightweight, structured representation of active web page.
        Includes title, URL, headings, main visible text (truncated to max_chars), forms, and links (truncated to max_links).
        """
        page = self.session.get_active_page()
        if page.is_closed():
            return {"title": "", "url": "", "text": "", "headings": [], "links": [], "forms": []}

        url = page.url
        title = page.title()

        # Extract headings
        headings = []
        try:
            h_locs = page.locator("h1, h2, h3").all()
            for h in h_locs[:15]:
                t = h.inner_text().strip()
                if t:
                    headings.append(t)
        except Exception:
            pass

        # Extract main visible text
        main_text = ""
        try:
            body_text = page.inner_text("body")
            main_text = body_text.strip()[:max_chars]
        except Exception:
            pass

        # Extract links
        links = []
        try:
            a_locs = page.locator("a[href]").all()
            for a in a_locs:
                if len(links) >= max_links:
                    break
                try:
                    href = a.get_attribute("href") or ""
                    link_text = a.inner_text().strip()
                    if href and not href.startswith("javascript:"):
                        links.append({"text": link_text or href, "url": href})
                except Exception:
                    continue
        except Exception:
            pass

        # Extract forms & inputs
        forms = []
        try:
            input_locs = page.locator("input, select, textarea, button").all()
            for inp in input_locs[:20]:
                try:
                    role = inp.get_attribute("role") or inp.evaluate("el => el.tagName.toLowerCase()")
                    name = inp.get_attribute("name") or inp.get_attribute("id") or inp.get_attribute("placeholder") or ""
                    inp_type = inp.get_attribute("type") or "text"
                    forms.append({"role": role, "name": name, "type": inp_type})
                except Exception:
                    continue
        except Exception:
            pass

        return {
            "title": title,
            "url": url,
            "headings": headings,
            "main_text": main_text,
            "text": main_text,
            "links": links,
            "forms": forms,
            "character_count": len(main_text),
        }

    def search(
        self, query: str, search_engine_url: str = "https://html.duckduckgo.com/html/?q="
    ) -> Tuple[List[SearchResult], BrowserActionResult]:
        """
        Performs web search via browser engine and parses structured SearchResult items.
        """
        start_time = time.perf_counter()
        if not query:
            return [], BrowserActionResult(success=False, status="FAILED", message="Query string is empty")

        target_url = f"{search_engine_url}{quote_plus(query)}"
        logger.info(f"SEARCH_STARTED: Executing web search for '{query}' via {search_engine_url}")

        try:
            page = self.session.get_active_page()
            page.goto(target_url, wait_until="domcontentloaded")
            page.wait_for_load_state("domcontentloaded")

            results: List[SearchResult] = []
            
            # DuckDuckGo HTML parser
            try:
                result_locs = page.locator(".result, .links_main").all()
                for idx, r in enumerate(result_locs[:10]):
                    try:
                        title_elem = r.locator(".result__title, .result__a").first
                        title_text = title_elem.inner_text().strip()
                        url_val = title_elem.get_attribute("href") or ""
                        snippet_elem = r.locator(".result__snippet").first
                        snippet_text = snippet_elem.inner_text().strip() if snippet_elem.count() > 0 else ""

                        if title_text and url_val:
                            results.append(
                                SearchResult(
                                    title=title_text,
                                    url=url_val,
                                    snippet=snippet_text,
                                    position=idx + 1,
                                )
                            )
                    except Exception:
                        continue
            except Exception:
                pass

            # Fallback generic link parser if search container engine differed
            if not results:
                try:
                    a_elems = page.locator("a[href]").all()
                    for idx, a in enumerate(a_elems):
                        if len(results) >= 5:
                            break
                        href = a.get_attribute("href") or ""
                        txt = a.inner_text().strip()
                        if href.startswith("http") and len(txt) > 5 and not "duckduckgo" in href:
                            results.append(SearchResult(title=txt, url=href, snippet="", position=idx + 1))
                except Exception:
                    pass

            dur = time.perf_counter() - start_time
            logger.info(f"SEARCH_COMPLETED: Extracted {len(results)} search results in {dur*1000:.2f} ms")

            return results, BrowserActionResult(
                success=True,
                status="SUCCESS",
                message=f"Found {len(results)} search results for '{query}'",
                data=[r.model_dump() for r in results],
                duration_seconds=round(dur, 4),
                verified=True,
            )
        except Exception as e:
            logger.error(f"BROWSER_ERROR: Search failed for '{query}': {e}")
            return [], BrowserActionResult(
                success=False, status="FAILED", message=f"Search failed: {e}", duration_seconds=round(time.perf_counter() - start_time, 4)
            )
