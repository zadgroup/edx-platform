"""
Definition of the course team feature.
"""

from django.utils.translation import ugettext as _


class TeamsFeature(object):
    """
    The representation of the Teams feature.
    """

    title = "Teams"

    # Register a course tab
    course_tab = {
        "name": "edx.teams",
        "title": _("Teams"),
        "view_name": "teams_dashboard",
    }
