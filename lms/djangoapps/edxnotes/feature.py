"""
Registers the "edX Notes" feature for the edX platform.
"""

from django.utils.translation import ugettext as _


class EdxNotesFeature(object):
    """
    The representation of the edX Notes feature.
    """

    title = "edX Notes"

    # Register a course tab
    course_tab = {
        "name": "edxnotes",
        "title": _("Notes"),
        "view_name": "teams_dashboard",
    }

    @staticmethod
    def is_enabled(course, settings, user=None):  # pylint: disable=unused-argument
        """Returns true if the edX Notes feature is enabled.

        Args:
            course (CourseDescriptor): the course using the feature
            settings (dict): a dict of configuration settings
            user (User): the user interacting with the course
        """
        return settings.FEATURES.get('ENABLE_EDXNOTES')
