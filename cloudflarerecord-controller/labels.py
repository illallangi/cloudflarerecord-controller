from more_itertools import one
from collections.abc import Mapping


class Labels(Mapping):
    def __init__(self, **kwargs):
        self._dict = kwargs

    def __getitem__(self, *args, **kwargs):
        return self._dict.__getitem__(*args, **kwargs)

    def __iter__(self, *args, **kwargs):
        return self._dict.__iter__(*args, **kwargs)

    def __len__(self, *args, **kwargs):
        return self._dict.__len__(*args, **kwargs)

    def but(self, *exclude):
        return Labels(**{k: v for k, v in self.items() if k not in exclude})

    def with_label(self, key, value):
        result = {k: v for k, v in self.items()}
        result[key] = value
        return Labels(**result)

    @property
    def asdict(self):
        return self._dict

    @property
    def asname(self):
        return "-".join([self[k] for k in self])

    @property
    def selector(self):
        result = ",".join([f"{k}={self[k]}" for k in self])
        return result

    def matches(self, idx, namespace):
        if namespace not in idx.keys():
            return None
        results = idx[namespace]
        for key in self:
            results = [
                o
                for o in results
                if key in o["metadata"]["labels"]
                and o["metadata"]["labels"][key] == self[key]
            ]
        return results

    def match_name(self, idx, namespace):
        if namespace not in idx.keys():
            return None
        matches = self.matches(idx, namespace)
        if len(matches) == 0:
            return None
        return one(matches)["metadata"]["name"]
