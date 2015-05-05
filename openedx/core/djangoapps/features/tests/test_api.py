"""
Tests for the features API
"""

from django.test import TestCase

from ..api import FeatureManager, FeatureError


class TestFeaturesApi(TestCase):
    """
    Unit tests for the features API
    """

    def test_get_feature(self):
        """
        Verify the behavior of get_feature.
        """
        feature = FeatureManager.get_feature("teams")
        self.assertEqual(feature.title, "Teams")

        with self.assertRaises(FeatureError):
            FeatureManager.get_feature("no_such_feature")
