import os
import unittest

from bbc_http import fetch_text
from bbc_parse import (
    MIN_EXPECTED_GOSSIP_ITEMS,
    extract_gossip_items,
    get_latest_gossip_url,
    get_parse_diagnostics,
    parse_gossip_article,
    select_article_paragraphs,
    to_soup,
)
from config import GOSSIP_MAIN_URL, HEADERS
from pipeline import is_today_article


@unittest.skipUnless(os.getenv("SMOKE_TEST") == "1", "set SMOKE_TEST=1 to run")
class BbcSmokeTest(unittest.TestCase):
    def test_current_bbc_gossip_page_is_parseable(self) -> None:
        main_soup = to_soup(fetch_text(GOSSIP_MAIN_URL, headers=HEADERS))
        article_url = get_latest_gossip_url(main_soup)
        self.assertIsNotNone(article_url)

        article_soup = to_soup(fetch_text(article_url, headers=HEADERS))
        title, published_date, soup = parse_gossip_article(article_soup)
        selector, paragraphs = select_article_paragraphs(soup)
        items = extract_gossip_items(soup)
        diagnostics = get_parse_diagnostics(soup)

        print("smoke_article_url:", article_url)
        print("smoke_title:", title)
        print("smoke_published_date:", published_date)
        print("smoke_selector:", selector)
        print("smoke_paragraph_count:", len(paragraphs))
        print("smoke_item_count:", len(items))
        print("smoke_diagnostics:", diagnostics)

        self.assertTrue(title)
        self.assertIsNotNone(published_date)
        self.assertGreater(len(paragraphs), 0)

        if is_today_article(published_date):
            self.assertGreaterEqual(len(items), MIN_EXPECTED_GOSSIP_ITEMS)
        else:
            self.assertGreater(
                len(items),
                0,
                "Latest article is not today, but it should still be parseable.",
            )


if __name__ == "__main__":
    unittest.main()
