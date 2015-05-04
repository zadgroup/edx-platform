"""TODO """

from . import BaseCreditRequirementChecker, register_checker


@register_checker("verification")
class VerificationCreditRequirement(BaseCreditRequirementChecker):
    """TODO """

    def validate_criteria(self, criteria):
        # Check that the criteria says the checkpoint name
        pass

    def validate_user_status(self, user_status):
        # Check that the user's status has the verification status
        # for each checkpoint.
        pass

    def is_satisfied(self, user_status):
        # Check that the user has a status of "approved" for the checkpoint
        pass

    def status_description(self, user_status):
        # String describing the checkpoint name and user's status
        pass
