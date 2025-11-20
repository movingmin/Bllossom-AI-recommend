from typing import List, Type, Optional, Set


def get_slots(cls: Type) -> Optional[Set[str]]:
    ret = set()
    for c in cls.mro():
        if c is object:
            break
        s = c.__dict__.get('__slots__')
        if s is None:
            return None
        ret.update(s)
        if '__dict__' in ret:
            return None
    return ret
