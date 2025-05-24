# coding=utf-8
from apply_transformations import ApplyTransformations
from inkex.tester import ComparisonMixin, TestCase
from inkex.tester.filters import CompareNumericFuzzy, CompareWithPathSpace


class ApplyTransformations(ComparisonMixin, TestCase):
    effect_class = AddNodes
    comparisons = [
        tuple()
    ]
    compare_file = "complextransforms.test.svg"
    compare_filters = [
        CompareWithPathSpace(),
        CompareNumericFuzzy(),
    ]


