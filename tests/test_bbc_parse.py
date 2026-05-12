import unittest

from bbc_parse import (
    extract_gossip_items,
    get_latest_gossip_url,
    get_parse_diagnostics,
    select_article_paragraphs,
    split_body_and_source,
    to_soup,
)


class BbcParseTest(unittest.TestCase):
    def test_get_latest_gossip_url_normalizes_relative_bbc_link(self) -> None:
        soup = to_soup(
            """
            <html>
              <body>
                <a href="/sport/football/articles/c123">Gossip</a>
              </body>
            </html>
            """
        )

        self.assertEqual(
            get_latest_gossip_url(soup),
            "https://www.bbc.com/sport/football/articles/c123",
        )

    def test_extract_gossip_items_filters_non_gossip_paragraphs(self) -> None:
        soup = to_soup(
            """
            <html>
              <body>
                <main>
                  <p class="ssrcss-1q0x1qg-Paragraph">The Daily Express back page</p>
                  <p class="ssrcss-1q0x1qg-Paragraph">
                    Multiple clubs interested in a player, with two internal team links
                    but no external source. This summary should be ignored.
                    <a href="/sport/football/teams/liverpool">Liverpool</a>
                  </p>
                  <p class="ssrcss-1q0x1qg-Paragraph">
                    Manchester United want Player X and will bid £50m this summer.
                    <a href="https://example.com/story">(The Athletic) , external</a>
                  </p>
                  <p class="ssrcss-1q0x1qg-Paragraph">
                    Chelsea are monitoring Player Y before the summer window opens. (Mail)
                  </p>
                  <p class="ssrcss-1q0x1qg-Paragraph">
                    Copyright © 2026 BBC. The BBC is not responsible for the content of external sites.
                  </p>
                </main>
              </body>
            </html>
            """
        )

        items = extract_gossip_items(soup)

        self.assertEqual(
            items,
            [
                (
                    "Manchester United want Player X and will bid £50m this summer.",
                    "The Athletic",
                    "https://example.com/story",
                ),
                (
                    "Chelsea are monitoring Player Y before the summer window opens.",
                    "Mail",
                    None,
                ),
            ],
        )

    def test_select_article_paragraphs_uses_first_matching_fallback(self) -> None:
        soup = to_soup(
            """
            <html>
              <body>
                <article>
                  <p class="ssrcss-1q0x1qg-Paragraph">
                    Arsenal are considering Player Z as a summer target. (Mirror)
                  </p>
                </article>
              </body>
            </html>
            """
        )

        selector, paragraphs = select_article_paragraphs(soup)

        self.assertEqual(selector, "article p[class*='Paragraph']")
        self.assertEqual(len(paragraphs), 1)

    def test_split_body_and_source_rejects_sentence_like_parentheses(self) -> None:
        text = (
            "Tottenham are interested in Player A, who has scored 10 goals this season "
            "(he is expected to leave if the club misses Europe.)"
        )

        body, source = split_body_and_source(text)

        self.assertEqual(body, text)
        self.assertIsNone(source)

    def test_parse_diagnostics_includes_selector_counts_and_samples(self) -> None:
        soup = to_soup(
            """
            <html>
              <body>
                <article>
                  <p class="ssrcss-1q0x1qg-Paragraph">
                    A long paragraph with no source, useful for parser diagnostics.
                  </p>
                </article>
              </body>
            </html>
            """
        )

        diagnostics = get_parse_diagnostics(soup)

        self.assertEqual(
            diagnostics["selected_selector"],
            "article p[class*='Paragraph']",
        )
        self.assertEqual(diagnostics["paragraph_count"], 1)
        self.assertEqual(
            diagnostics["selector_counts"]["article p[class*='Paragraph']"],
            1,
        )
        self.assertTrue(diagnostics["sample_paragraphs"])


if __name__ == "__main__":
    unittest.main()
