"""
This module is essentially a broker to xmodule/tabs.py -- it was originally introduced to
perform some LMS-specific tab display gymnastics for the Entrance Exams feature
"""
from django.conf import settings
from django.test.client import RequestFactory
from django.utils.translation import ugettext as _

from courseware.entrance_exams import user_must_complete_entrance_exam
from xmodule.tabs import CourseTabList, CourseTabManager, CourseFeatureTabType


def get_course_tab_list(request, course):
    """
    Retrieves the course tab list from xmodule.tabs and manipulates the set as necessary
    """
    user = request.user
    xmodule_tab_list = CourseTabList.iterate_displayable(course, settings, user=user)

    # Now that we've loaded the tabs for this course, perform the Entrance Exam work
    # If the user has to take an entrance exam, we'll need to hide away all of the tabs
    # except for the Courseware and Instructor tabs (latter is only viewed if applicable)
    # We don't have access to the true request object in this context, but we can use a mock
    course_tab_list = []
    for tab in xmodule_tab_list:
        if user_must_complete_entrance_exam(request, user, course):
            # Hide all of the tabs except for 'Courseware'
            # Rename 'Courseware' tab to 'Entrance Exam'
            if tab.type is not 'courseware':
                continue
            tab.name = _("Entrance Exam")
        course_tab_list.append(tab)

    # Add in any dynamic tabs, i.e. those that are not persisted
    course_tab_list += CourseTabList.get_dynamic_tabs(course, settings, user=user)

    return course_tab_list
