from functools import update_wrapper
from typing import Callable, Tuple, Hashable, Dict

from member.util import get_slots

_missing = object()


class Member:
    def __init__(self, getter: Callable, attr_name=None):
        self.fget = getter
        self.attr_name: str = attr_name
        self.fon_set = None
        self.fon_del = None
        self.fvalid = None
        update_wrapper(self, getter)

    def __set_name__(self, owner, name):
        self.__name__ = name
        slots = get_slots(owner)
        if self.attr_name is None:
            if slots is None:
                self.attr_name: str = '_' + name
            else:
                l_name = name.lower()
                attr_name_candidates = [s for s in slots if s.strip('_').lower() == l_name]
                if len(attr_name_candidates) != 1:
                    raise NameError(f'cannot find single candidate for attribute name for member {self}'
                                    f' (found {len(attr_name_candidates)}, try setting attribute name explicitly)')
                self.attr_name, = attr_name_candidates
        else:
            self.attr_name = self.attr_name.replace('$', name)

    def __get__(self, instance, owner):
        if instance is None:
            return self
        return BoundMember(self, instance)

    def __delete__(self, instance):
        self.__get__(instance, type(instance)).pop()

    def __str__(self):
        return self.__name__

    def __call__(self, instance, *args, **kwargs):
        return self.__get__(instance, type(instance))(*args, **kwargs)

    def on_explicit_set(self, func):
        self.fon_set = func
        return self

    def on_explicit_del(self, func):
        self.fon_del = func
        return self

    def is_valid(self, func):
        self.fvalid = func
        return self


def args_key(args: Tuple[Hashable], kwargs: Dict[str, Hashable]):
    return args, (frozenset(kwargs.items()) if kwargs else None)


class BoundMember:
    __slots__ = 'member', 'instance'

    def __init__(self, member: Member, instance):
        self.member = member
        self.instance = instance

    def _ensure_dict(self):
        d = getattr(self.instance, self.member.attr_name, _missing)
        if d is _missing:
            d = {}
            setattr(self.instance, self.member.attr_name, d)
        return d

    def __call__(self, *args: Hashable, **kwargs: Hashable):
        d = self._ensure_dict()
        key = args_key(args, kwargs)

        val = d.get(key, _missing)
        if val is _missing \
                or (self.member.fvalid is not None and not self.member.fvalid(self.instance, val)):
            val = self.member.fget(self.instance, *args, **kwargs)
            d[key] = val
        return val

    def no_cache(self, *args, **kwargs):
        return self.member.fget(self.instance, *args, **kwargs)

    def get(self, default, *args: Hashable, **kwargs: Hashable):
        d = self._ensure_dict()
        key = args_key(args, kwargs)
        val = d.get(key, _missing)
        if val is _missing \
                or (self.member.fvalid is not None and not self.member.fvalid(self.instance, val)):
            return default
        return val

    def set(self, value, *args: Hashable, **kwargs: Hashable):
        d = self._ensure_dict()

        key = args_key(args, kwargs)
        d[key] = value
        if self.member.fon_set:
            self.member.fon_set(self.instance, value, *args, **kwargs)

    def setdefault(self, value, *args: Hashable, **kwargs: Hashable):
        d = self._ensure_dict()

        key = args_key(args, kwargs)
        s = key not in d
        ret = d.setdefault(key, value)
        if s and self.member.fon_set:
            self.member.fon_set(self.instance, value, *args, **kwargs)
        return ret

    def pop(self, *args: Hashable, **kwargs: Hashable):
        d = getattr(self.instance, self.member.attr_name, None)
        key = args_key(args, kwargs)
        if not d:
            raise KeyError(key)
        ret = d.pop(key)
        if self.member.fon_del:
            self.member.fon_del(self.instance, ret, *args, **kwargs)
        return ret

    def pop_default(self, default, *args: Hashable, **kwargs: Hashable):
        d = getattr(self.instance, self.member.attr_name, None)
        if not d:
            return default
        key = args_key(args, kwargs)
        s = key in d
        ret = d.pop(key, default)
        if s and self.member.fon_del:
            self.member.fon_del(self.instance, ret, *args, **kwargs)
        return ret

    def clear(self):
        d = getattr(self.instance, self.member.attr_name, None)
        if d:
            if self.member.fon_del:
                c = dict(d)
            else:
                c = None
            d.clear()
            if self.member.fon_del:
                for ((a, kw), v) in c.items():
                    kw = kw or {}
                    self.member.fon_del(self.instance, v, *a, **kw)

    def __getitem__(self, item):
        if not isinstance(item, tuple):
            item = (item,)
        ret = self.get(_missing, *item)
        if ret is _missing:
            raise KeyError(item)
        return ret

    def __setitem__(self, key, value):
        if not isinstance(key, tuple):
            key = (key,)
        self.set(value, *key)

    def __delitem__(self, key):
        if not isinstance(key, tuple):
            key = (key,)
        self.pop(*key)
