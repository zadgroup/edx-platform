"""TODO """
import abc

# TODO: dictionary here mapping names to credit requirements
# could have a registration mechanism
_CHECKER_REGISTRY = {}


class RequirementNotSupported(Exception):
    """TODO """
    pass


class CriteriaValidationError(Exception):
    """ TODO """
    pass


# ABC implementation of credit requirement business logic
class BaseCreditRequirementChecker(object):
    """TODO """

    __metaclass__ = abc.ABCMeta

    def __init__(self, criteria):
        """ TODO """
        self.validate_criteria(criteria)
        self._criteria = criteria

    @property
    def criteria(self):
        return self._criteria

    @abc.abstractmethod
    def validate_criteria(self, criteria):
        raise NotImplemented

    @abc.abstractmethod
    def is_satisfied(self, user_status):
        raise NotImplemented

    @abc.abstractmethod
    def status_description(self, user_status):
        raise NotImplemented


def register_checker(clz, requirement):
    """TODO """
    global _CHECKER_REGISTRY
    assert requirement not in _CHECKER_REGISTRY
    _CHECKER_REGISTRY[requirement] = clz
    return clz


def get_checker_for_requirement(requirement, criteria):
    """TODO """
    global _CHECKER_REGISTRY
    clz = _CHECKER_REGISTRY.get(requirement)

    if clz is None:
        raise RequirementNotSupported(requirement)

    # May raise CriteriaValidationError
    return clz(criteria)
