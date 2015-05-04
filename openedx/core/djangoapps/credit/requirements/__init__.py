"""TODO """

# TODO: dictionary here mapping names to credit requirements
# could have a registration mechanism


# ABC implementation of credit requirement business logic
class BaseCreditRequirement(object):
    """TODO """

    req_type = ""

    def validate_criteria(self, criteria):
        pass

    def is_satisfied(self, criteria, user_status):
        pass

    def status_description(self, criteria, user_status):
        pass
