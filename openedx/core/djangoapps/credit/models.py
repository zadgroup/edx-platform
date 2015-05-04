"""TODO """
from django.db import models


class CreditProvider(models.Model):
    """TODO """
    # ID
    # name
    # URL end-point
    pass


class CreditProviderCourse(models.Model):
    """TODO """
    # FK to CreditProvider (1:m)
    # Course key
    pass


class CreditRequirement(models.Model):
    """TODO """
    # credit_course (1:m)
    # requirement_type
    # active (bool)
    # data
    pass


class CreditRequirementStatus(models.Model):
    """TODO """
    # username
    # requirement (FK to CreditRequirement)
    # status: started | satisfied
    pass


class CreditRequest(models.Model):
    """ TODO """
    # uuid
    # CreditProviderCourse (FK to CPC)
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
