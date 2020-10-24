"""
Tests for the basic regexes given in templates.py to use as building blocks (OPTIONAL_TEXT_PRE, OPTIONAL_TEXT_POST, etc)

Run:
    python -m unittest -v chirpy/core/regex/test_basic_regexes.py
"""

import unittest
import re

import chirpy.core.regex.util
from chirpy.core.regex import templates


class TestBasicRegexes(unittest.TestCase):

    def assert_regex_matchinside(self, regex, positive_examples, negative_examples):
        """
        For each positive example p, checks that regex matches something inside p
        For each negative example n, checks that regex does not match anything inside n
        """
        r = re.compile(regex)
        for p in positive_examples:
            self.assertIsNotNone(r.match(p), f'positive example "{p}" did not match regex {regex}')
        for n in negative_examples:
            self.assertIsNone(r.match(n), f'negative example "{n}" matched regex {regex}')

    def assert_regex_matchexact(self, regex, positive_examples, negative_examples):
        """
        For each positive example p, checks that regex matches the whole of p
        For each negative example n, checks that regex does not match the whole of n
        """
        self.assert_regex_matchinside('^{}$'.format(regex), positive_examples, negative_examples)

    def test_optional_text(self):
        self.assert_regex_matchexact(chirpy.core.regex.util.OPTIONAL_TEXT,
                                     positive_examples=['', 'hello', 'hello world'],
                                     negative_examples=[])

    def test_nonempty_text(self):
        self.assert_regex_matchexact(chirpy.core.regex.util.NONEMPTY_TEXT,
                                     positive_examples=['hello', 'hello world'],
                                     negative_examples=[''])

    def test_optional_text_pre(self):
        self.assert_regex_matchexact(chirpy.core.regex.util.OPTIONAL_TEXT_PRE,
                                     positive_examples=['', 'hello ', 'hello  ', 'hello world ', ' hello ', ' '],
                                     negative_examples=['hello', ' hello'])

    def test_optional_text_post(self):
        self.assert_regex_matchexact(chirpy.core.regex.util.OPTIONAL_TEXT_POST,
                                     positive_examples=['', ' hello', '  hello', ' hello world', ' hello ', ' '],
                                     negative_examples=['hello', 'hello '])

    def test_optional_text_mid(self):
        self.assert_regex_matchexact(chirpy.core.regex.util.OPTIONAL_TEXT_MID,
                                     positive_examples=[' ', ' hello ', ' hello world '],
                                     negative_examples=['', 'hello', 'hello ', ' hello', '  hello'])
