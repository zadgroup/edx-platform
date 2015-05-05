"""
Registers the Instructor tab feature for the edX platform.
"""

from django.utils.translation import ugettext as _

from courseware.access import has_access


class InstructorTabFeature(object):
    """
    The representation of the Instructor tab feature.
    """

    title = "Instructor Tab"

    # Register a course tab
    course_tab = {
        "name": "instructor",
        "title": _('Instructor'),
        "view_name": "instructor_dashboard",
        "is_persistent": False,
    }

    @staticmethod
    def is_enabled(course, settings, user=None):  # pylint: disable=unused-argument
        """
        Returns true if the specified user has staff access.
        """
        return user and has_access(user, 'staff', course, course.id)
