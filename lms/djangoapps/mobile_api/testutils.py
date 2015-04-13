"""
Test utilities for mobile API tests:

  MobileAPITestCase - Common base class with helper methods and common functionality.
     No tests are implemented in this base class.

  Test Mixins to be included by concrete test classes and provide implementation of common test methods:
     MobileAuthTestMixin - tests for APIs with mobile_view and is_user=False.
     MobileAuthUserTestMixin - tests for APIs with mobile_view and is_user=True.
     MobileCourseAccessTestMixin - tests for APIs with mobile_course_access and verify_enrolled=False.
     MobileEnrolledCourseAccessTestMixin - tests for APIs with mobile_course_access and verify_enrolled=True.
"""
# pylint: disable=no-member
import ddt
from mock import patch

from django.conf import settings
from django.core.urlresolvers import reverse
from django.db import IntegrityError
from django.test.client import RequestFactory

from rest_framework.test import APITestCase

from courseware.tests.factories import UserFactory
from courseware.model_data import FieldDataCache
from courseware.module_render import get_module
from courseware.entrance_exams import (
    get_entrance_exam_score,
    user_has_passed_entrance_exam,
)
from opaque_keys.edx.keys import CourseKey
from student import auth
from student.models import CourseEnrollment
from util.milestones_helpers import (
    add_milestone,
    add_course_content_milestone,
    add_course_milestone,
    add_prerequisite_course,
    fulfill_course_milestone,
    generate_milestone_namespace,
    get_milestone_relationship_types,
    get_namespace_choices,
    seed_milestone_relationship_types,
)
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory


class MobileAPITestCase(ModuleStoreTestCase, APITestCase):
    """
    Base class for testing Mobile APIs.
    Subclasses are expected to define REVERSE_INFO to be used for django reverse URL, of the form:
       REVERSE_INFO = {'name': <django reverse name>, 'params': [<list of params in the URL>]}
    They may also override any of the methods defined in this class to control the behavior of the TestMixins.
    """
    def setUp(self):
        super(MobileAPITestCase, self).setUp()
        self.course = CourseFactory.create(mobile_available=True, static_asset_path="needed_for_split")
        self.user = UserFactory.create()
        self.password = 'test'
        self.username = self.user.username

        self.prereq_course = CourseFactory.create()

    def tearDown(self):
        super(MobileAPITestCase, self).tearDown()
        self.logout()

    def login(self):
        """Login test user."""
        self.client.login(username=self.username, password=self.password)

    def logout(self):
        """Logout test user."""
        self.client.logout()

    def enroll(self, course_id=None):
        """Enroll test user in test course."""
        CourseEnrollment.enroll(self.user, course_id or self.course.id)

    def unenroll(self, course_id=None):
        """Unenroll test user in test course."""
        CourseEnrollment.unenroll(self.user, course_id or self.course.id)

    def login_and_enroll(self, course_id=None):
        """Shortcut for both login and enrollment of the user."""
        self.login()
        self.enroll(course_id)

    def api_response(self, reverse_args=None, expected_response_code=200, **kwargs):
        """
        Helper method for calling endpoint, verifying and returning response.
        If expected_response_code is None, doesn't verify the response' status_code.
        """
        url = self.reverse_url(reverse_args, **kwargs)
        response = self.url_method(url, **kwargs)
        if expected_response_code is not None:
            self.assertEqual(response.status_code, expected_response_code)
        return response

    def reverse_url(self, reverse_args=None, **kwargs):  # pylint: disable=unused-argument
        """Base implementation that returns URL for endpoint that's being tested."""
        reverse_args = reverse_args or {}
        if 'course_id' in self.REVERSE_INFO['params']:
            reverse_args.update({'course_id': unicode(kwargs.get('course_id', self.course.id))})
        if 'username' in self.REVERSE_INFO['params']:
            reverse_args.update({'username': kwargs.get('username', self.user.username)})
        return reverse(self.REVERSE_INFO['name'], kwargs=reverse_args)

    def url_method(self, url, **kwargs):  # pylint: disable=unused-argument
        """Base implementation that returns response from the GET method of the URL."""
        return self.client.get(url)


class MobileAuthTestMixin(object):
    """
    Test Mixin for testing APIs decorated with mobile_view.
    """
    def test_no_auth(self):
        self.logout()
        self.api_response(expected_response_code=401)


class MobileAuthUserTestMixin(MobileAuthTestMixin):
    """
    Test Mixin for testing APIs related to users: mobile_view with is_user=True.
    """
    def test_invalid_user(self):
        self.login_and_enroll()
        self.api_response(expected_response_code=404, username='no_user')

    def test_other_user(self):
        # login and enroll as the test user
        self.login_and_enroll()
        self.logout()

        # login and enroll as another user
        other = UserFactory.create()
        self.client.login(username=other.username, password='test')
        self.enroll()
        self.logout()

        # now login and call the API as the test user
        self.login()
        self.api_response(expected_response_code=404, username=other.username)


class MobileAPIMilestonesMixin(object):
    """
    Tests the Mobile API decorators for milestones.

    The two milestones supported in these tests are entrance exams and
    pre-requisite courses. If either of these milestones are unfulfilled,
    the mobile api will appropriately block content until the milestone is
    fulfilled.
    """
    MILESTONE_ERROR = {'developer_message': 'Cannot access content with unfulfilled pre-requisites or unpassed entrance exam.'}  # pylint: disable=line-too-long

    # Enrollment list hides enrolled courses, milestone courses are not hidden
    ALLOW_ACCESS_TO_MILESTONE_COURSE = False  # pylint: disable=invalid-name

    def __init__(self):
        self.entrance_exam = None
        self.problem_1 = None
        self.milestone = None
        self.milestone_relationship_types = None
        self.request = None

    def init_course_access(self, course_id=None):
        """Base implementation of initializing the user for each test."""
        self.login_and_enroll(course_id)

    def _add_entrance_exam(self):
        """ Sets up entrance exam """
        try:
            # in case milestone relationship types have already been set
            seed_milestone_relationship_types()
        except IntegrityError:
            pass

        # Set up the extrance exam
        self.course.entrance_exam_enabled = True

        self.entrance_exam = ItemFactory.create(
            parent=self.course,
            category="chapter",
            display_name="Entrance Exam Chapter",
            is_entrance_exam=True,
            in_entrance_exam=True
        )
        self.problem_1 = ItemFactory.create(
            parent=self.entrance_exam,
            category='problem',
            display_name="The Only Exam Problem",
            graded=True,
            in_entrance_exam=True
        )

        namespace_choices = get_namespace_choices()
        milestone_namespace = generate_milestone_namespace(
            namespace_choices.get('ENTRANCE_EXAM'),
            self.course.id
        )
        self.milestone = {
            'name': 'Test Milestone',
            'namespace': milestone_namespace,
            'description': 'Entrance Exam for TestMobileAPIMilestones',
        }
        self.milestone_relationship_types = get_milestone_relationship_types()
        self.milestone = add_milestone(self.milestone)

        self.course.entrance_exam_minimum_score_pct = 0.50
        self.course.entrance_exam_id = unicode(self.entrance_exam.scope_ids.usage_id)
        modulestore().update_item(self.course, self.user.id)

        # set up the request for exam functions
        self.request = RequestFactory()
        self.request.user = self.user
        self.request.COOKIES = {}
        self.request.META = {}
        self.request.is_secure = lambda: True
        self.request.get_host = lambda: "edx.org"
        self.request.method = 'GET'

        # Add the exam
        add_course_milestone(
            unicode(self.course.id),
            self.milestone_relationship_types['REQUIRES'],
            self.milestone
        )
        add_course_content_milestone(
            unicode(self.course.id),
            unicode(self.entrance_exam.location),
            self.milestone_relationship_types['FULFILLS'],
            self.milestone
        )

    def _add_prerequisite_course(self):
        """ Helper method to set up the prerequisite course """
        try:
            # in case milestone relationship types have already been set
            seed_milestone_relationship_types()
        except IntegrityError:
            pass

        add_prerequisite_course(self.course.id, self.prereq_course.id)

    def _pass_entrance_exam(self):
        """ Helper function to pass the entrance exam """
        self.assertEqual(get_entrance_exam_score(self.request, self.course), 0)
        self.assertEqual(user_has_passed_entrance_exam(self.request, self.course), False)
        # pylint: disable=maybe-no-member,no-member
        grade_dict = {'value': 1, 'max_value': 1, 'user_id': self.user.id}
        field_data_cache = FieldDataCache.cache_for_descriptor_descendents(
            self.course.id,
            self.user,
            self.course,
            depth=2
        )
        # pylint: disable=protected-access
        module = get_module(
            self.user,
            self.request,
            self.problem_1.scope_ids.usage_id,
            field_data_cache,
        )._xmodule
        module.system.publish(self.problem_1, 'grade', grade_dict)

        self.assertEqual(get_entrance_exam_score(self.request, self.course), 1.0)
        self.assertEqual(user_has_passed_entrance_exam(self.request, self.course), True)

    @patch.dict('django.conf.settings.FEATURES', {
        'ENABLE_PREREQUISITE_COURSES': True,
        'MILESTONES_APP': True,
        'ENTRANCE_EXAMS': True
    })
    def test_feature_flags(self):
        """
        Tests when feature flags are set/unset, content is gated appropriately
        """
        self._add_prerequisite_course()
        self._add_entrance_exam()
        self.init_course_access()
        response = self.api_response(expected_response_code=None)
        if self.ALLOW_ACCESS_TO_MILESTONE_COURSE:
            self.verify_success(response)
        else:
            self.verify_failure(response)
            self.assertEqual(response.data, self.MILESTONE_ERROR)
        settings.FEATURES["MILESTONES_APP"] = False
        response = self.api_response(expected_response_code=None)
        self.verify_success(response)

    @patch.dict('django.conf.settings.FEATURES', {'ENABLE_PREREQUISITE_COURSES': True, 'MILESTONES_APP': True})
    def test_unfulfilled_prerequisite_course(self):
        """ Tests the case for an unfulfilled pre-requisite course """
        self._add_prerequisite_course()

        self.init_course_access()
        response = self.api_response(expected_response_code=None)
        if self.ALLOW_ACCESS_TO_MILESTONE_COURSE:
            self.verify_success(response)
        else:
            self.verify_failure(response)
            self.assertEqual(response.data, self.MILESTONE_ERROR)

    @patch.dict('django.conf.settings.FEATURES', {'ENABLE_PREREQUISITE_COURSES': True, 'MILESTONES_APP': True})
    def test_unfulfilled_prerequisite_course_for_staff(self):
        self._add_prerequisite_course()

        self.user.is_staff = True
        self.user.save()
        self.init_course_access()
        response = self.api_response(expected_response_code=None)
        self.verify_success(response)

    @patch.dict('django.conf.settings.FEATURES', {'ENABLE_PREREQUISITE_COURSES': True, 'MILESTONES_APP': True})
    def test_fulfilled_prerequisite_course(self):
        """
        Tests the case when a user fulfills existing pre-requisite course
        """
        self._add_prerequisite_course()

        add_prerequisite_course(self.course.id, self.prereq_course.id)
        fulfill_course_milestone(self.prereq_course.id, self.user)
        self.init_course_access()
        response = self.api_response(expected_response_code=None)
        self.verify_success(response)

    @patch.dict('django.conf.settings.FEATURES', {'ENTRANCE_EXAMS': True, 'MILESTONES_APP': True})
    def test_unpassed_entrance_exam(self):
        """
        Tests the case where the user has not passed the entrance exam
        """
        self._add_entrance_exam()

        self.init_course_access()
        response = self.api_response(expected_response_code=None)
        if self.ALLOW_ACCESS_TO_MILESTONE_COURSE:
            self.verify_success(response)
        else:
            self.verify_failure(response)
            self.assertEqual(response.data, self.MILESTONE_ERROR)

    @patch.dict('django.conf.settings.FEATURES', {'ENTRANCE_EXAMS': True, 'MILESTONES_APP': True})
    def test_unpassed_entrance_exam_for_staff(self):
        self._add_entrance_exam()

        self.user.is_staff = True
        self.user.save()
        self.init_course_access()
        response = self.api_response(expected_response_code=None)
        self.verify_success(response)

    @patch.dict('django.conf.settings.FEATURES', {'ENTRANCE_EXAMS': True, 'MILESTONES_APP': True})
    def test_passed_entrance_exam(self):
        """
        Tests access when user has passed the entrance exam
        """
        self._add_entrance_exam()
        self._pass_entrance_exam()

        self.init_course_access()
        response = self.api_response(expected_response_code=None)
        self.verify_success(response)


@ddt.ddt
class MobileCourseAccessTestMixin(MobileAPIMilestonesMixin):
    """
    Test Mixin for testing APIs marked with mobile_course_access.
    (Use MobileEnrolledCourseAccessTestMixin when verify_enrolled is set to True.)
    Subclasses are expected to inherit from MobileAPITestCase.
    Subclasses can override verify_success, verify_failure, and init_course_access methods.
    """
    ALLOW_ACCESS_TO_UNRELEASED_COURSE = False  # pylint: disable=invalid-name

    def verify_success(self, response):
        """Base implementation of verifying a successful response."""
        self.assertEqual(response.status_code, 200)

    def verify_failure(self, response):
        """Base implementation of verifying a failed response."""
        self.assertEqual(response.status_code, 404)

    def init_course_access(self, course_id=None):
        """Base implementation of initializing the user for each test."""
        self.login_and_enroll(course_id)

    def test_success(self):
        self.init_course_access()

        response = self.api_response(expected_response_code=None)
        self.verify_success(response)  # allow subclasses to override verification

    def test_course_not_found(self):
        non_existent_course_id = CourseKey.from_string('a/b/c')
        self.init_course_access(course_id=non_existent_course_id)

        response = self.api_response(expected_response_code=None, course_id=non_existent_course_id)
        self.verify_failure(response)  # allow subclasses to override verification

    @patch.dict('django.conf.settings.FEATURES', {'DISABLE_START_DATES': False})
    def test_unreleased_course(self):
        self.init_course_access()

        response = self.api_response(expected_response_code=None)
        if self.ALLOW_ACCESS_TO_UNRELEASED_COURSE:
            self.verify_success(response)
        else:
            self.verify_failure(response)

    # A tuple of Role Types and Boolean values that indicate whether access should be given to that role.
    @ddt.data(
        (auth.CourseBetaTesterRole, True),
        (auth.CourseStaffRole, True),
        (auth.CourseInstructorRole, True),
        (None, False)
    )
    @ddt.unpack
    def test_non_mobile_available(self, role, should_succeed):
        self.init_course_access()

        # set mobile_available to False for the test course
        self.course.mobile_available = False
        self.store.update_item(self.course, self.user.id)

        # set user's role in the course
        if role:
            role(self.course.id).add_users(self.user)

        # call API and verify response
        response = self.api_response(expected_response_code=None)
        if should_succeed:
            self.verify_success(response)
        else:
            self.verify_failure(response)


class MobileEnrolledCourseAccessTestMixin(MobileCourseAccessTestMixin):
    """
    Test Mixin for testing APIs marked with mobile_course_access with verify_enrolled=True.
    """
    def test_unenrolled_user(self):
        self.login()
        self.unenroll()
        response = self.api_response(expected_response_code=None)
        self.verify_failure(response)
