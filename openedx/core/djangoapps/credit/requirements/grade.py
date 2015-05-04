"""TODO """

from . import BaseCreditRequirementChecker, register_checker


@register_checker("grade")
class GradeCreditRequirementChecker(BaseCreditRequirementChecker):
    """TODO """

    def validate_criteria(self, criteria):
        # Check that criteria has a "min_grade" item
        # that is a float between 0.0 and 1.0
        pass

    def validate_user_status(self, user_status):
        # Check that the user status has a "grade" item
        # that is a float between 0.0 and 1.0
        pass

    def is_satisfied(self, criteria, user_status):
        # Check that the user's grade is > the cutoff.
        pass

    def status_description(self, user_status):
        # X out of Y grade
        pass
