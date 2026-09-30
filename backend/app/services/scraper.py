from typing import Dict, List
from urllib.parse import urljoin, urlparse

import ssl
import requests

from requests.adapters import HTTPAdapter
from urllib3.poolmanager import PoolManager

from bs4 import BeautifulSoup

from app.utils.text_cleaner import (
    clean_line,
    clean_text,
)


DEFAULT_TIMEOUT = 20


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    )
}


# ============================================================
# LEGACY TLS ADAPTER
# ============================================================

class LegacyTLSAdapter(HTTPAdapter):
    """
    HTTPS adapter used only for servers that require
    legacy TLS renegotiation.

    SSL certificate verification remains enabled.
    """

    def __init__(self, *args, **kwargs):

        self.ssl_context = ssl.create_default_context()

        legacy_option = getattr(
            ssl,
            "OP_LEGACY_SERVER_CONNECT",
            None,
        )

        if legacy_option is None:

            raise RuntimeError(
                "This Python/OpenSSL installation does not "
                "support legacy TLS server connections."
            )

        self.ssl_context.options |= legacy_option

        super().__init__(
            *args,
            **kwargs,
        )


    def init_poolmanager(
        self,
        connections,
        maxsize,
        block=False,
        **pool_kwargs,
    ):

        self.poolmanager = PoolManager(

            num_pools=connections,

            maxsize=maxsize,

            block=block,

            ssl_context=self.ssl_context,

            **pool_kwargs,

        )


# ============================================================
# NORMAL HTTPS REQUEST
# ============================================================

def _normal_request(
    url: str,
):
    """
    Make a normal secure HTTPS request.
    """

    response = requests.get(

        url,

        headers=HEADERS,

        timeout=DEFAULT_TIMEOUT,

        allow_redirects=True,

    )

    response.raise_for_status()

    return response


# ============================================================
# LEGACY TLS REQUEST
# ============================================================

def _legacy_tls_request(
    url: str,
):
    """
    Retry using a compatibility TLS configuration.

    Certificate verification remains enabled.
    """

    session = requests.Session()

    adapter = LegacyTLSAdapter()

    session.mount(
        "https://",
        adapter,
    )

    try:

        response = session.get(

            url,

            headers=HEADERS,

            timeout=DEFAULT_TIMEOUT,

            allow_redirects=True,

        )

        response.raise_for_status()

        return response

    finally:

        session.close()


# ============================================================
# FETCH WEBPAGE
# ============================================================

def _fetch_webpage(
    url: str,
):
    """
    First try normal HTTPS.

    If the server specifically requires legacy TLS
    renegotiation, retry with the compatibility adapter.
    """

    try:

        return _normal_request(
            url
        )

    except requests.exceptions.SSLError as exc:

        error_text = str(exc)


        if (
            "UNSAFE_LEGACY_RENEGOTIATION_DISABLED"
            not in error_text
        ):

            raise


        try:

            return _legacy_tls_request(
                url
            )

        except Exception as legacy_exc:

            raise RuntimeError(
                "The website requires legacy TLS "
                "renegotiation, but the compatibility "
                f"connection also failed: {legacy_exc}"
            ) from legacy_exc


# ============================================================
# DISCOVER RELEVANT INTERNAL LINKS
# ============================================================

def discover_relevant_links(
    soup: BeautifulSoup,
    base_url: str,
) -> List[str]:
    """
    Discover internal pages that are likely to contain
    eligibility or application information.
    """

    keywords = [

        "eligib",

        "criteria",

        "about",

        "guideline",

        "guidelines",

        "faq",

        "frequently",

        "advertisement",

        "notice",

        "scheme",

        "application",

        "how-to-apply",

        "how_to_apply",

        "download",

        "qualification",

        "requirement",

        "condition",

        "income",

        "domicile",

    ]


    base_domain = urlparse(
        base_url
    ).netloc


    discovered = []


    for anchor in soup.find_all(
        "a",
        href=True,
    ):

        href = anchor.get(
            "href",
            "",
        ).strip()


        if not href:

            continue


        if href.startswith(
            (
                "#",
                "javascript:",
                "mailto:",
                "tel:",
            )
        ):

            continue


        absolute_url = urljoin(
            base_url,
            href,
        )


        parsed = urlparse(
            absolute_url
        )


        # Only follow pages on the same domain.
        if parsed.netloc != base_domain:

            continue


        link_text = anchor.get_text(
            " ",
            strip=True,
        )


        combined_text = (
            f"{link_text} "
            f"{absolute_url}"
        ).lower()


        if any(
            keyword in combined_text
            for keyword in keywords
        ):

            if (
                absolute_url
                not in discovered
            ):

                discovered.append(
                    absolute_url
                )


    return discovered


# ============================================================
# EXTRACT SECONDARY PAGE
# ============================================================

def extract_secondary_page(
    url: str,
) -> Dict:
    """
    Fetch and extract useful text from a discovered
    internal webpage.

    Secondary pages do not recursively discover more pages.
    This prevents uncontrolled crawling.
    """

    try:

        response = _fetch_webpage(
            url
        )


    except requests.exceptions.Timeout:

        return {

            "url":
                url,

            "title":
                "",

            "text":
                "",

            "error":
                "timeout",

        }


    except requests.exceptions.RequestException as exc:

        return {

            "url":
                url,

            "title":
                "",

            "text":
                "",

            "error":
                str(exc),

        }


    except RuntimeError as exc:

        return {

            "url":
                url,

            "title":
                "",

            "text":
                "",

            "error":
                str(exc),

        }


    # ========================================================
    # PARSE HTML
    # ========================================================

    soup = BeautifulSoup(

        response.text,

        "lxml",

    )


    # ========================================================
    # REMOVE NON-CONTENT ELEMENTS
    # ========================================================

    for element in soup(
        [
            "script",
            "style",
            "noscript",
            "svg",
            "iframe",
            "canvas",
            "template",
        ]
    ):

        element.decompose()


    # ========================================================
    # TITLE
    # ========================================================

    title = ""


    if soup.title:

        title = clean_line(

            soup.title.get_text(
                " ",
                strip=True,
            )

        )


    # ========================================================
    # COLLECT TEXT
    # ========================================================

    parts = []


    if title:

        parts.append(
            title
        )


    # --------------------------------------------------------
    # HEADINGS
    # --------------------------------------------------------

    for heading in soup.find_all(
        [
            "h1",
            "h2",
            "h3",
            "h4",
            "h5",
            "h6",
        ]
    ):

        text = clean_line(

            heading.get_text(
                " ",
                strip=True,
            )

        )


        if text:

            parts.append(
                text
            )


    # --------------------------------------------------------
    # PARAGRAPHS
    # --------------------------------------------------------

    for paragraph in soup.find_all(
        "p"
    ):

        text = clean_line(

            paragraph.get_text(
                " ",
                strip=True,
            )

        )


        if len(text) >= 15:

            parts.append(
                text
            )


    # --------------------------------------------------------
    # LIST ITEMS
    # --------------------------------------------------------

    for list_element in soup.find_all(
        [
            "ul",
            "ol",
        ]
    ):

        for item in list_element.find_all(
            "li"
        ):

            text = clean_line(

                item.get_text(
                    " ",
                    strip=True,
                )

            )


            if text:

                parts.append(
                    text
                )


    # --------------------------------------------------------
    # TABLES
    # --------------------------------------------------------

    for table in soup.find_all(
        "table"
    ):

        for row in table.find_all(
            "tr"
        ):

            cells = row.find_all(
                [
                    "th",
                    "td",
                ]
            )


            row_data = [

                clean_line(

                    cell.get_text(
                        " ",
                        strip=True,
                    )

                )

                for cell in cells

            ]


            row_data = [

                cell

                for cell in row_data

                if cell

            ]


            if row_data:

                parts.append(
                    " | ".join(
                        row_data
                    )
                )


    text = clean_text(
        "\n".join(parts)
    )


    return {

        "url":
            str(response.url),

        "title":
            title,

        "text":
            text,

        "error":
            None,

    }


# ============================================================
# MAIN WEBPAGE SCRAPER
# ============================================================

def scrape_webpage(
    url: str,
) -> Dict:
    """
    Download and extract useful information from a webpage.

    The scraper:

    1. Fetches the main webpage.
    2. Extracts its content.
    3. Discovers relevant internal links.
    4. Fetches a limited number of those pages.
    5. Combines their content.

    Returns:

        url
        title
        description
        headings
        paragraphs
        lists
        tables
        full_text
        relevant_links
        discovered_pages
    """

    # ========================================================
    # FETCH MAIN PAGE
    # ========================================================

    try:

        response = _fetch_webpage(
            url
        )


    except requests.exceptions.Timeout:

        raise RuntimeError(
            "The website took too long to respond."
        )


    except requests.exceptions.SSLError as exc:

        raise RuntimeError(
            "Secure connection to the website failed: "
            f"{exc}"
        )


    except requests.exceptions.RequestException as exc:

        raise RuntimeError(
            f"Unable to access the webpage: {exc}"
        )


    # ========================================================
    # PARSE HTML
    # ========================================================

    soup = BeautifulSoup(

        response.text,

        "lxml",

    )


    # ========================================================
    # DISCOVER LINKS BEFORE REMOVING ELEMENTS
    # ========================================================

    relevant_links = (
        discover_relevant_links(
            soup,
            str(response.url),
        )
    )


    # ========================================================
    # REMOVE NON-CONTENT ELEMENTS
    # ========================================================

    for element in soup(
        [
            "script",
            "style",
            "noscript",
            "svg",
            "iframe",
            "canvas",
            "template",
        ]
    ):

        element.decompose()


    # ========================================================
    # TITLE
    # ========================================================

    title = ""


    if soup.title:

        title = clean_line(

            soup.title.get_text(
                " ",
                strip=True,
            )

        )


    # ========================================================
    # META DESCRIPTION
    # ========================================================

    description = None


    meta_description = soup.find(

        "meta",

        attrs={

            "name": (
                lambda value:
                    value
                    and value.lower()
                    == "description"
            )

        },

    )


    if meta_description:

        description = clean_line(

            meta_description.get(
                "content",
                "",
            )

        )


    # ========================================================
    # HEADINGS
    # ========================================================

    headings: List[str] = []


    for heading in soup.find_all(
        [
            "h1",
            "h2",
            "h3",
            "h4",
            "h5",
            "h6",
        ]
    ):

        text = clean_line(

            heading.get_text(
                " ",
                strip=True,
            )

        )


        if (
            text
            and text not in headings
        ):

            headings.append(
                text
            )


    # ========================================================
    # PARAGRAPHS
    # ========================================================

    paragraphs: List[str] = []


    for paragraph in soup.find_all(
        "p"
    ):

        text = clean_line(

            paragraph.get_text(
                " ",
                strip=True,
            )

        )


        if (
            len(text) >= 15
            and text not in paragraphs
        ):

            paragraphs.append(
                text
            )


    # ========================================================
    # LIST ITEMS
    # ========================================================

    lists: List[str] = []


    for list_element in soup.find_all(
        [
            "ul",
            "ol",
        ]
    ):

        for item in list_element.find_all(
            "li"
        ):

            text = clean_line(

                item.get_text(
                    " ",
                    strip=True,
                )

            )


            if (
                text
                and text not in lists
            ):

                lists.append(
                    text
                )


    # ========================================================
    # TABLES
    # ========================================================

    tables: List[List[str]] = []


    for table in soup.find_all(
        "table"
    ):

        rows = []


        for row in table.find_all(
            "tr"
        ):

            cells = row.find_all(
                [
                    "th",
                    "td",
                ]
            )


            row_data = [

                clean_line(

                    cell.get_text(
                        " ",
                        strip=True,
                    )

                )

                for cell in cells

            ]


            row_data = [

                cell

                for cell in row_data

                if cell

            ]


            if row_data:

                rows.append(
                    row_data
                )


        if rows:

            tables.append(
                rows
            )


    # ========================================================
    # MAIN PAGE FULL TEXT
    # ========================================================

    text_parts = []


    if title:

        text_parts.append(
            title
        )


    if description:

        text_parts.append(
            description
        )


    if headings:

        text_parts.extend(
            headings
        )


    if paragraphs:

        text_parts.extend(
            paragraphs
        )


    if lists:

        text_parts.extend(
            lists
        )


    for table in tables:

        for row in table:

            text_parts.append(

                " | ".join(row)

            )


    full_text = clean_text(

        "\n".join(
            text_parts
        )

    )


    # ========================================================
    # FETCH RELEVANT SECONDARY PAGES
    # ========================================================

    discovered_pages = []


    # Only fetch the first 8 relevant pages.
    for link in relevant_links[:8]:

        page_result = (
            extract_secondary_page(
                link
            )
        )


        if page_result.get(
            "text"
        ):

            discovered_pages.append(
                page_result
            )


            full_text += (

                "\n\n"
                "===== RELATED OFFICIAL SOURCE =====\n"

                f"SOURCE URL: "
                f"{page_result['url']}\n"

                f"PAGE TITLE: "
                f"{page_result['title']}\n"

                "===== SOURCE CONTENT =====\n"

                f"{page_result['text']}"

            )


    full_text = clean_text(
        full_text
    )


    # ========================================================
    # RETURN
    # ========================================================

    return {

        "url":
            str(response.url),

        "title":
            title,

        "description":
            description,

        "headings":
            headings,

        "paragraphs":
            paragraphs,

        "lists":
            lists,

        "tables":
            tables,

        "full_text":
            full_text,

        "relevant_links":
            relevant_links[:15],

        "discovered_pages":
            discovered_pages,

    }