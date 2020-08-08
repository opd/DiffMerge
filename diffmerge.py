import copy
import json

from deepdiff import DeepDiff, Delta

def swap_keys(d, rules):
    # Maybe can use deepcopy
    result = {}
    d = copy.deepcopy(d)
    for from_, to in rules:
        result[to] = d.pop(from_)
        result[from_] = d.pop(to)
    result.update(d)
    return result

REVERSE_RULES = {
    "values_changed": {
        "swap_keys": [
            ('new_value', 'old_value')
        ]
    },
    "iterable_item_removed": {
        "rename": "iterable_item_added",
    },
    "iterable_item_added": {
        "rename": "iterable_item_removed",
    },
    "dictionary_item_added": {
        "rename": "dictionary_item_removed",
    },
    "dictionary_item_removed": {
        "rename": "dictionary_item_added",
    },
}

def reverse_diff(diff):
    result = {}
    for change_type, changes in diff.items():
        rule = REVERSE_RULES[change_type]
        new_changes = {}
        for path, change in changes.items():
            rules = rule.get("swap_keys", None)
            if rules:
                change = swap_keys(change, rules)
            new_changes[path] = change
        rename = rule.get("rename", None)
        if rename:
            change_type = rename
        result[change_type] = new_changes
    return result


class Puppet:
    def __init__(self, parent=None):
        # TODO rename parent to root
        self._parent = parent
        self._items = {}
        self._counter = 0
        self._is_list = False
        self._is_dict = False
        self._index = parent.get_index() if parent else 0

    def __copy__(self):
        raise NotImplementedError

    def _deepcopy(self, parent=None):
        obj = Puppet()
        if parent is None:
            parent = obj
        else:
            obj._parent = parent
        obj._counter = self._counter
        obj._is_list = self._is_list
        obj._is_dict = self._is_dict
        obj._index = self._index
        obj._items = {
            k: v._deepcopy(obj) if isinstance(v, Puppet) else copy.deepcopy(v)
            for k, v in self._items.items()
        }
        return obj

    def __deepcopy__(self, memo):
        return self._deepcopy()

    def get_item(self):
        parent = self._parent or self
        return Puppet(parent=parent)

    def __getitem__(self, key):
        self.apply_list_fix(key)
        if key in self._items:
            return self._items[key]
        child = self.get_item()
        self._items[key] = child
        return child

    def apply_list_fix(self, key):
        if not isinstance(key, int):
            self._is_dict = True
            return
        self._is_list = True
        for i in range(key):
            if i not in self._items:
                self._items[i] = self.get_item()

    def __setitem__(self, key, value):
        self.apply_list_fix(key)
        self._items[key] = value
        return value

    def __delitem__(self, key):
        self._items.pop(key, None)
        if isinstance(key, int):
            keys = sorted([k for k in self._items.keys() if k > key])
            for key in keys:
                self._items[key - 1] = self._items.pop(key)

    def get_index(self):
        self._counter += 1
        return self._counter

    # TODO
    def unique_name(self):
        return f"puppet_{self._index}"

    def _to_dict(self):
        def get_value(obj):
            if isinstance(obj, Puppet):
                return obj._to_dict()
            return obj

        if not self._items:
            if self._is_list:
                return []
            if self._is_dict:
                return {}
            return self.unique_name()

        keys = None
        if self._is_list:
            return [get_value(v) for k, v in sorted(self._items.items(), key=lambda x: x[0])]
        else:
            return {
                key: get_value(value)
                for key, value in self._items.items()
            }

    def to_dict(self):
        return self._to_dict()

    def __str__(self):
        return str(self.to_dict())


def diff_func(t1, t2):
    return DeepDiff(t1, t2, verbose_level=2)


def merge(diffs):
    obj = Puppet()
    for diff in diffs:
        obj = obj + Delta(diff)
    end_dict = copy.deepcopy(obj.to_dict())
    for diff in reversed(diffs):
        obj += Delta(reverse_diff(diff))
    start_dict = obj.to_dict()
    return diff_func(start_dict, end_dict)
