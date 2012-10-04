# -*- coding: utf-8 -*-
from clacks.common.utils import N_
from clacks.agent.objects.comparator import ElementComparator


class Equals(ElementComparator):
    """
    Object property validator which checks for a given property value.

    =========== ==================
    Key         Description
    =========== ==================
    match       The value we want to match for.
    case_ignore If True then upper/lower case is ignored.
    =========== ==================
    """

    def __init__(self, obj):
        super(Equals, self).__init__()

    def process(self, all_props, key, value, match, case_ignore=False):

        errors = []

        # Check each property value
        cnt = 0
        for item in value:

            # Depending on the ignore-case parameter we do not match upper/lower-case differences.
            if case_ignore:
                if item.lower() != match.lower():
                    errors.append(dict(index=cnt,
                        detail=N_("item does not match the given value ignoring the case",
                        )))
                    return False, errors
            else:
                if item != match:
                    errors.append(dict(index=cnt,
                        detail=N_("item does not match the given value",
                        )))
                    return False, errors
            cnt += 1
        return True, errors


class Greater(ElementComparator):
    """
    Object property validator which checks if a given property value is
    greater than a given operand.

    =========== ==================
    Key         Description
    =========== ==================
    match       The value we match againt.
    =========== ==================
    """

    def __init__(self, obj):
        super(Greater, self).__init__()

    def process(self, all_props, key, value, match):

        errors = []

        # All items of value have to match.
        cnt = 0
        match = int(match)
        for item in value:
            item = int(item)
            if not (item > match):
                errors.append(dict(index=cnt,
                    detail=N_("item needs to be greater than %(compare)s",
                    compare=match
                    )))
                return False, errors
            cnt += 1
        return True, errors


class Smaller(ElementComparator):

    """
    Object property validator which checks if a given property value is
    smaller than a given operand.

    =========== ==================
    Key         Description
    =========== ==================
    match       The value we match againt.
    =========== ==================
    """
    def __init__(self, obj):
        super(Smaller, self).__init__()

    def process(self, all_props, key, value, match):

        errors = []

        # All items of value have to match.
        match = int(match)
        cnt = 0
        for item in value:
            item = int(item)
            if not (item < match):
                errors.append(dict(index=cnt,
                    detail=N_("item needs to be smaller than %(compare)s",
                    compare=match
                    )))
                return False, errors
            cnt += 1
        return True, errors
