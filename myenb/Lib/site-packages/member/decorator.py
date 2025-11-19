from functools import partial

from member.member_descriptor import Member


def member(func=None, **kwargs):
    if not func:
        return partial(member, **kwargs)
    return Member(func, **kwargs)
