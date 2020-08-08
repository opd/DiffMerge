import copy

from deepdiff import DeepDiff, Delta
import pytest

from diffmerge import reverse_diff, swap_keys, Puppet, merge


class Compare:
    def __init__(self, func):
        self._func = func

    def __eq__(self, other):
        try:
            return self._func(other)
        except BaseException:
            return False


DIFF_CHAINS = (
    (
        [1, 2, 3],
        [1, -2, 3],
        [0, -2, 3],
        [0, -2, 3, 4],
        [0, -2, 3, 4, 5, 6],
        [1, -2, 3, 4, 5, 6],
    ),
    (
        {"x": 1},
        {"x": 1, "y": [{"a": [1, 2, 3]}]},
        {"x": 1, "y": [{"a": [1, 2, 3, 4]}]},
        {"x": 1, "y": [{"a": [2, 3, 4]}]},
        {"x": 1, "y": [{"a": [2, 3, 4]}], "z": None},
    ),
)

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

pairs = [
    (x, y) for chain in DIFF_CHAINS for x, y in zip(chain, chain[1:])
]
DIFF_PAIRS = DIFF_PAIRS + tuple(pairs)


def diff_func(t1, t2):
    return DeepDiff(t1, t2, verbose_level=2)


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


def test_diff_reverse_temp():
    plain = {'values_changed': {'root[1]': {'new_value': 3, 'old_value': 2}}, 'iterable_item_removed': {'root[2]': 3}}
    rev = {'values_changed': {'root[1]': {'new_value': 2, 'old_value': 3}}, 'iterable_item_added': {'root[2]': 3}}
    assert reverse_diff(plain) == rev


def test_swap_keys():
    old = {'x': 1, 'y': 2}
    new = {'x': 2, 'y': 1}
    rules = [('x', 'y')]
    assert swap_keys(old, rules) == new

def drop_puppet(items):
    return {
        key: value for key, value in items.items() if not isinstance(value, Puppet)
    }

def test_compare():
    c = Compare(lambda x: isinstance(x, str))
    assert c == "string"
    assert c != 1

def test_puppet():
    obj = Puppet()

    obj["x"] = 3
    assert obj._items["x"] == 3

    obj["x2"]
    assert isinstance(obj["x2"], Puppet)

    obj["y"][0] = 10
    assert obj._items["y"]._items[0] == 10

    obj["y"][10] = 20
    assert drop_puppet(obj._items["y"]._items) == {0: 10, 10: 20}

    del obj["y"][4]
    assert drop_puppet(obj._items["y"]._items) == {0: 10, 9: 20}

    data = obj.to_dict()
    p = Compare(lambda x: x.startswith("puppet_"))
    assert data == {
        'x': 3,
        'x2': p,
        'y': [
            10,
            p,
            p,
            p,
            p,
            p,
            p,
            p,
            p,
            20,
        ],
    }


def test_deep_copy():
    obj = Puppet()
    obj["x"] = 1
    obj_copy = copy.deepcopy(obj)
    assert obj.to_dict() == obj_copy.to_dict()

    obj = Puppet()
    obj["x"] = 3
    obj["y"]
    obj["y"][0] = 0
    obj["y"][4] = 40

    obj_copy = copy.deepcopy(obj)

    del obj["y"][1]
    del obj_copy["y"][1]

    assert obj.to_dict() == obj_copy.to_dict()

    obj["y"][0] = 30
    assert obj.to_dict() != obj_copy.to_dict()


@pytest.mark.parametrize('pair', DIFF_PAIRS)
@pytest.mark.parametrize('rev', [True, False])
def test_apply(pair, rev):
    if rev:
        pair = list(reversed(pair))
    diff = diff_func(pair[0], pair[1])
    obj = Puppet()
    delta = Delta(diff)
    end_state = obj + delta
    end_dict = end_state.to_dict()
    reversed_diff = reverse_diff(diff)
    delta_reversed = Delta(reversed_diff)
    initial_state = end_state + delta_reversed

    initial_dict = initial_state.to_dict()
    result_diff = diff_func(initial_dict, end_dict)
    assert result_diff == diff

@pytest.mark.parametrize('chain', DIFF_CHAINS)
@pytest.mark.parametrize('rev', [False, True])
def test_merge_diffs(chain, rev):
    if rev:
        chain = list(reversed(chain))
    diffs = []
    for prev, new in zip(chain, chain[1:]):
        diffs.append(diff_func(prev, new))

    result_diff = merge(diffs)
    sample_diff = diff_func(chain[0], chain[-1])
    assert result_diff == sample_diff
