"""
Registers the CCX feature for the edX platform.
"""

from django.utils.translation import ugettext as _


class CcxFeature(object):
    """
    The representation of the CCX feature.
    """

    title = "CCX"

    # Register a course tab
    course_tab = {
        "name": "ccx_coach",
        "title": _('CCX Coach'),
        "view_name": "ccx_coach_dashboard",
        "is_persistent": False,
    }

    @staticmethod
    def is_enabled(course, settings, user=None):
        """
        Returns true if CCX has been enabled and the specified user is a coach
        """
        if not user or not settings.FEATURES.get('CUSTOM_COURSES_EDX', False):
            return False
        from opaque_keys.edx.locations import SlashSeparatedCourseKey
        from student.roles import CourseCcxCoachRole  # pylint: disable=import-error
        course_id = course.id.to_deprecated_string()
        course_key = SlashSeparatedCourseKey.from_deprecated_string(course_id)
        role = CourseCcxCoachRole(course_key)
        return role.has_user(user)
