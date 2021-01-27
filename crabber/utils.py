import re


def parse_error_message(html_body: str) -> str:
    """ Gets error title and description from HTML page.
    """
    return re.search(r'<title>([^<]+)</title>(?:.|\s)+<p>([^<]+)</p>',
                     html_body).groups()
