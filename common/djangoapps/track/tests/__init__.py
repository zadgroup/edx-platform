"""Helpers for tests related to emitting events to the tracking logs."""

from datetime import datetime
import json

from django.test import TestCase
from django.test.utils import override_settings
from freezegun import freeze_time
from pytz import UTC

from eventtracking import tracker
from eventtracking.django import DjangoTracker


FROZEN_TIME = datetime(2013, 10, 3, 8, 24, 55, tzinfo=UTC)
IN_MEMORY_BACKEND_CONFIG = {
    'mem': {
        'ENGINE': 'track.tests.InMemoryBackend'
    }
}


class InMemoryBackend(object):
    """A backend that simply stores all events in memory"""

    def __init__(self):
        super(InMemoryBackend, self).__init__()
        self.events = []

    def send(self, event):
        """Store the event in a list"""
        self.events.append(event)


def unicode_flatten(tree):
    """
    Test cases have funny issues where some strings are unicode, and
    some are not. This does not cause test failures, but causes test
    output diffs to show many more difference than actually occur in the
    data. This will convert everything to a common form.
    """
    if isinstance(tree, basestring):
        return unicode(tree)
    elif isinstance(tree, list):
        return map(unicode_flatten, list)
    elif isinstance(tree, dict):
        return dict([(unicode_flatten(key), unicode_flatten(value)) for key, value in tree.iteritems()])
    return tree


@freeze_time(FROZEN_TIME)
@override_settings(
    EVENT_TRACKING_BACKENDS=IN_MEMORY_BACKEND_CONFIG
)
class EventTrackingTestCase(TestCase):
    """
    Supports capturing of emitted events in memory and inspecting them.

    Each test gets a "clean slate" and can retrieve any events emitted during their execution.

    """

    # Make this more robust to the addition of new events that the test doesn't care about.

    def setUp(self):
        super(EventTrackingTestCase, self).setUp()

        self.tracker = DjangoTracker()
        tracker.register_tracker(self.tracker)

    @property
    def backend(self):
        """A reference to the in-memory backend that stores the events."""
        return self.tracker.backends['mem']

    def get_event(self, idx=0):
        """Retrieve an event emitted up to this point in the test."""
        return self.backend.events[idx]

    def assert_no_events_emitted(self):
        """Ensure no events were emitted at this point in the test."""
        self.assertEquals(len(self.backend.events), 0)

    def assert_events_emitted(self):
        """Ensure at least one event has been emitted at this point in the test."""
        self.assertGreaterEqual(len(self.backend.events), 1)

    def assertEqualUnicode(self, tree_a, tree_b):
        """Like assertEqual, but give nicer errors for unicode vs. non-unicode"""
        self.assertEqual(unicode_flatten(tree_a), unicode_flatten(tree_b))

    def assert_event_matches(self, expected, actual, strict=False):
        """
        Compare two event dictionaries.

        Fail if any discrepancies exist, and output the list of all discrepancies. The intent is to produce clearer
        error messages than "{ some massive dict } != { some other massive dict }", instead enumerating the keys that
        differ. Produces period separated "paths" to keys in the output, so "context.foo" refers to the following
        structure:

            {
                'context': {
                    'foo': 'bar'  # this key, value pair
                }
            }

        By default, it only asserts that all fields specified in the first event also exist and have the same value in
        the second event. If the `strict` parameter is passed in it will also ensure that *only* the fields in the first
        event exist in the second event. For example::

            expected = {
                'a': 'b'
            }

            actual = {
                'a': 'b',
                'c': 'd'
            }

            self.assert_event_matches(expected, actual, strict=False)  # This will not raise an AssertionError
            self.assert_event_matches(expected, actual, strict=True)   # This *will* raise an AssertionError
        """
        errors = self._compare_trees(expected, actual, strict, [])
        if len(errors) > 0:
            self.fail('Unexpected event differences found:\n' + '\n'.join(errors))

    def _compare_trees(self, expected, actual, strict, path):
        errors = []

        if not strict and path == ['event'] and isinstance(expected, dict) and isinstance(actual, basestring):
            actual = json.loads(actual)

        if isinstance(expected, dict) and isinstance(actual, dict):
            expected_keys = frozenset(expected.keys())
            actual_keys = frozenset(actual.keys())

            for key in (expected_keys - actual_keys):
                errors.append('Expected key "{0}" not found in actual'.format(self._path_to_string(path + [key])))

            if strict:
                for key in (actual_keys - expected_keys):
                    errors.append('Actual key "{0}" was unexpected and this is a strict comparison'.format(self._path_to_string(path + [key])))

            for key in (expected_keys & actual_keys):
                child_errors = self._compare_trees(expected[key], actual[key], strict, path + [key])
                errors.extend(child_errors)

        elif expected != actual:
            errors.append('Values are not equal at "{path}": expected="{a}" and actual="{b}"'.format(
                path=self._path_to_string(path),
                a=expected,
                b=actual
            ))

        return errors

    def _path_to_string(self, path):
        return '.'.join(path)
