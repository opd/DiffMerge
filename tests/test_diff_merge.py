from deepdiff import DeepDiff, Delta
import pytest

from diffmerge import reverse_diff, swap_keys, Puppet

DIFF_PAIRS = (
    # array
    ([1, 3], [1, 2, 3]),
    ({"x": 1}, {"x": 2, "y": 3}),
    (
        {
            "name": "Alex",
            "options": []
        },
        {
            "name": "Andrew",
            "options": [{
                "min": 100,
                "max": 200,
            }]
        }

    )
)

def diff_func(t1, t2):
    return DeepDiff(t1, t2, verbose_level=2)

# Dont' work with diff reverse. Can't apply diff correctly
# def diff_func_repetition(t1, t2):
#     return DeepDiff(t1, t2, verbose_level=2, ignore_order=True, report_repetition=True)

@pytest.mark.parametrize('pair', DIFF_PAIRS)
@pytest.mark.parametrize('rev', [True, False])
def test_diff_reverse(pair, rev):
    if rev:
        pair = list(reversed(pair))
    diff = diff_func(pair[0], pair[1])
    delta = Delta(diff)
    assert pair[0] + delta == pair[1]
    delta = Delta(reverse_diff(diff))
    assert pair[1] + delta == pair[0]


# utils
def test_diff_reverse_temp():
    plain = {'values_changed': {'root[1]': {'new_value': 3, 'old_value': 2}}, 'iterable_item_removed': {'root[2]': 3}}
    rev = {'values_changed': {'root[1]': {'new_value': 2, 'old_value': 3}}, 'iterable_item_added': {'root[2]': 3}}
    assert reverse_diff(plain) == rev


# utils
def test_swap_keys():
    old = {'x': 1, 'y': 2}
    new = {'x': 2, 'y': 1}
    rules = [('x', 'y')]
    assert swap_keys(old, rules) == new


@pytest.mark.parametrize('pair', DIFF_PAIRS)
@pytest.mark.parametrize('rev', [True, False])
def test_apply(pair, rev):
    if rev:
        pair = list(reversed(pair))
    diff = diff_func(pair[0], pair[1])
    obj = Puppet()
    delta = Delta(diff)
    result = obj + delta
    # pytest -k test_apply -s -x
    # assert False
