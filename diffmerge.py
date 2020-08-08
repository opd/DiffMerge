import copy

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
    def __copy__(self):
        raise NotImplementedError

    def __deepcopy__(self, memo):
        # TODO
        return Puppet()
