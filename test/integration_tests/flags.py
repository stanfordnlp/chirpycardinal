from unittest import TestCase
from chirpy.core.flags import use_timeouts

class TestFlags(TestCase):
    def test_timeouts_on(self):
        """Check that the use_timeouts flag is on"""
        self.assertTrue(use_timeouts)