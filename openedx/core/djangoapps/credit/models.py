"""TODO """
from django.db import models


class CreditProvider(models.Model):
    """TODO """
    # ID
    # name
    # URL end-point
    pass


class CreditRequirement(models.Model):
    """TODO """
    # course_key
    # provider (FK to CreditProvider)
    # requirement_type
    # requirement_id
    # requirement_criteria (JSON)
    # active (bool)
    pass


class CreditRequirementStatus(models.Model):
    """TODO """
    # username
    # requirement (FK to CreditRequirement)
    # status: started | satisfied
    pass


class CreditEligibility(models.Model):
    """TODO """
    # username
    # course_key
    # CreditProvider (FK)
    pass


class CreditRequest(models.Model):
    """ TODO """
    # uuid
    # course_key
    # CreditProvider (FK to CP)
    # username
    # grade
    # full_name
    # email
    # mailing_address
    # country
    pass


class CreditApproval(models.Model):
    """TODO """
    # Request (FK to CreditRequest)
    pass
