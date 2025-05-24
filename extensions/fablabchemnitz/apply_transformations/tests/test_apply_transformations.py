# coding=utf-8
from apply_transformations.apply_transformations import ApplyTransformations
from inkex.tester import ComparisonMixin, TestCase
from inkex.tester.filters import CompareNumericFuzzy, CompareWithPathSpace


class ApplyTransformations(ComparisonMixin, TestCase):
    effect_class = ApplyTransformations
    comparisons = [
        tuple()
    ]
    compare_file = "svg/complextransform.test.svg"
    compare_filters = [
        CompareWithPathSpace(),
        CompareNumericFuzzy(),
    ]
    stderr_protect = False


