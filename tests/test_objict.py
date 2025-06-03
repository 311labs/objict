from collections.abc import Mapping
from functools import partial
import sys
import os
import datetime

import pytest

from objict import _descend, _get, objict, merge_dicts, parse_date

current_dir = os.path.dirname(__file__)


try:
    import cPickle as pickle
except ImportError:
    import pickle

try:
    import mock
except ImportError:
    from unittest import mock


from collections import namedtuple

version_info = namedtuple('version_info',
                          'major,minor,micro,releaselevel,serial')

if sys.version_info[0] < 3:
    def b(s):
        return s.encode('utf8') if not isinstance(s, str) else s

    def u(s):
        return s.decode('utf8') if isinstance(s, str) else s
else:
    def b(s):
        return s.encode('utf8') if not isinstance(s, bytes) else s

    def u(s):
        return s.decode('utf8') if isinstance(s, bytes) else s


class DefaultDict(objict):

    def __init__(self, default_factory, *args, **kwargs):
        assert callable(default_factory)
        self.default_factory = default_factory
        objict.__init__(self, *args, **kwargs)

    def __missing__(self, key):
        return self.default_factory()


def fail_factory(*args, **kwargs):
    pytest.fail()


# test utility for getting at the "real" mappings of a dict
def items(d):
    """
    Get the items of `d` (a dict/objict) in sorted order as
    they would be returned if `d` were a plain dict.
    """
    try:
        elems = dict.iteritems(d)
    except AttributeError:
        elems = dict.items(d)
    return sorted(elems)


def mkdict(cls, *args, **kwargs):
    # defaultdict needs type as first arg; we use None for testing
    if cls is DefaultDict:
        cls = partial(cls, type(None))
    return cls(*args, **kwargs)


@pytest.fixture
def dict_():
    return {
        'a': {'b': 'a->b'},
        '1': {'2': {'3': '1->2->3'}},
        'a.b': 'a.b',
        'c': 'c',
    }


@pytest.fixture(params=[dict, objict, DefaultDict])
def alldictfactory(request):
    return request.param


@pytest.fixture(params=[objict, DefaultDict])
def customdictfactory(request):
    return request.param


@pytest.fixture
def objict_(dict_):
    return objict.fromdict(dict_)


@pytest.fixture
def defaultdict_(dict_):
    return DefaultDict(lambda: None, dict_)


def test_get_bad_type(customdictfactory):
    with pytest.raises(TypeError):
        _get(None, None)
    with pytest.raises(TypeError):
        _get({}, {})


def test_get_present(customdictfactory):
    dct = mkdict(customdictfactory, {'a': 1})
    assert _get(dct, 'a') == 1


def test_get_custom_getitem():

    class C(object):

        def __getitem__(self, key):
            if key == 'sentinel':
                return mock.sentinel
            raise KeyError(key)

    c = C()
    assert _get(c, 'sentinel') is mock.sentinel
    with pytest.raises(KeyError):
        _get(c, 'missing')


def test_descend_top_level(dict_, alldictfactory):
    dct = mkdict(alldictfactory, dict_)
    with pytest.raises(ValueError):
        _descend(dct, 'c')


def test_descend_one_dot_match_all(dict_, alldictfactory):
    dct = mkdict(alldictfactory, dict_)
    val, token = _descend(dct, 'a.b')
    assert val is dct['a']
    assert token == 'b'


def test_descend_one_dot_match_allbutlast(dict_, alldictfactory):
    # matches all but last token
    dct = mkdict(alldictfactory, dict_)
    val, token = _descend(dct, 'a.z')
    assert val is dct['a']
    assert token == 'z'


def test_descend_two_dot_match_all(dict_, alldictfactory):
    dct = mkdict(alldictfactory, dict_)
    val, token = _descend(dct, '1.2.3')
    assert val is dct['1']['2']
    assert token == '3'


def test_descend_two_dot_match_allbutlast(dict_, alldictfactory):
    dct = mkdict(alldictfactory, dict_)
    val, token = _descend(dct, '1.2.X')
    assert val is dct['1']['2']
    assert token == 'X'


def test_descend_two_dot_match_first(dict_, alldictfactory):
    dct = mkdict(alldictfactory, dict_)
    with pytest.raises(KeyError) as err:
        _descend(dct, '1.Z.X')
        assert err.value.args[0] == 'Z'


def test_init_noargs():
    assert items(objict()) == []


def test_init_kwargs():
    ud = objict(one=1, two=2)
    assert items(ud) == [('one', 1), ('two', 2)]


def test_init_iterable_arg():
    lst = [('one', 1), ('two', 2), ('three', 3)]
    ud = objict(iter(lst))
    assert items(ud) == sorted(lst)


def test_init_dict_arg():
    d = {
        'a': 1,
        'b': 2,
        'c': 3
    }
    ud = objict(d)
    assert items(ud) == items(d)


def test_init_type():
    assert isinstance(objict(), objict)
    assert isinstance(objict(), dict)


def test_objict_is_dict_subclass():
    assert issubclass(objict, dict)


def test_objict_is_mapping():
    assert isinstance(objict(), Mapping)


def test_objict_is_mapping_subclass():
    assert issubclass(objict, Mapping)


def test_init_dict_arg_nested_dicts():
    d = {'foo': {'foo': 'bar'}}
    ud = objict(d)
    assert type(ud['foo']) is dict
    assert items(d) == [('foo', objict(foo='bar'))]


def test_init_dict_arg_dotted_key():
    d = {'a.b': 'a.b', 'a': 'a'}
    ud = objict(d)
    assert items(ud) == items(d)


def test_init_dict_arg_dotted_key_and_nested():
    d = {
        'a.b': 'a.b',
        'c': 'cc',
        'a': {'b': 'a->b'}
    }
    ud = objict(d)
    elems = items(ud)
    assert elems == [
        ('a', {'b': 'a->b'}),
        ('a.b', 'a.b'),
        ('c', 'cc')
    ]
    assert type(elems[0][1]) is dict  # not a objict!


def test_init_objict_arg():
    orig = objict({
        'a': {'b': 'a->b'},
        'c': objict({'d': 'c->d'})
    })
    ud = objict(orig)
    elems = items(ud)
    assert elems == [
        ('a', {'b': 'a->b'}),
        ('c', objict(d='c->d'))
    ]
    assert type(elems[0][1]) is dict
    assert type(elems[1][1]) is objict


def test_equality_with_dict():
    assert {} == objict()
    assert objict() == {}
    d = {'foo': {'bar': 'barbar'}}
    ud = objict(foo=objict(bar='barbar'))
    assert d == ud
    assert ud == d
    assert {} != objict(x='x')
    assert {'x': 'x'} != objict()
    assert objict(a=None) != objict(a={})


def test_equality_with_dict_dotted_key():
    d = {'foo.bar': ''}
    ud = objict({'foo.bar': ''})
    assert d == ud
    assert ud == d


def test_equality():
    assert objict() == objict()
    assert objict() != objict(x='')
    assert objict(x='') != objict()

    assert objict(a=0) == objict(a=0)
    assert objict(a=0) == objict(a=0.0)
    assert objict(a=0) != objict(b=0)
    assert objict(a=0) != objict(a='0')
    assert objict(a=0) != objict(a=1)
    assert objict(a=None) != objict(a={})
    assert objict(a={}) == objict(a=objict())

    ud1, ud2 = objict(a=objict()), objict(a=objict(a=None))
    assert ud1 != ud2
    assert ud2 != ud1

    ud1, ud2 = objict({'a.b': ''}), objict(a=objict(b=''))
    assert ud1 != ud2
    assert ud2 != ud1


def test_getitem_nonstring_key():
    ud = objict()
    ud[1] = 'one'
    assert ud[1] == 'one'


def test_getitem_none_key():
    ud = objict()
    ud[None] = 'nope'
    assert ud[None] == 'nope'


# @pytest.mark.skipif('sys.version_info[0] > 2')
def test_getitem_bytes_key():
    ud = objict()
    ud[b('one')] = 1
    assert ud[b('one')] == 1


def test_getitem_unicode_key():
    ud = objict()
    ud[u('one')] = 1
    assert ud[u('one')] == 1


def test_getitem_top_level_returns_value():
    obj = object()
    ud = objict(one=obj)
    assert ud['one'] is obj


def test_getitem_top_level_fail_raises_keyerror():
    ud = objict(one=1)
    with pytest.raises(KeyError):
        ud['two']


def test_getitem_multilevel_returns_value():
    ud = objict.fromdict({
        'one': {
            'two': 'one->two'
        },
        'a': {
            'b': {'c': 'a->b->c'}
        }
    })
    assert ud['one.two'] == 'one->two'
    assert ud['a.b'] == {'c': 'a->b->c'}
    assert ud['a.b.c'] == 'a->b->c'


def test_getitem_multilevel_fail():
    ud = objict.fromdict({
        'one': {
            'two': 'one->two'
        },
        'a': {
            'b': {'c': 'a->b->c'}
        }
    })
    try:
        ud['one.three']
        pytest.fail()
    except KeyError as e:  # success
        # verify args contains first failing token
        assert e.args == ('three',)
    try:
        ud['a.b.x']
        pytest.fail()
    except KeyError as e:
        assert e.args == ('x',)

    with pytest.raises(TypeError):
        # ud['a.b.c'] doesn't support indexing
        ud['a.b.c.d']


def test_getitem_nested_through_non_dict_typeerror():
    """
    TypeError should be raised when trying to traverse through
    an object that doesn't support `__getitem__`.
    """
    ud = objict(one=objict(two=2))
    with pytest.raises(TypeError):
        ud['one.two.three']


class BadDict(object):

    def __init__(self, **kwargs):
        self.d = kwargs

    def __getitem__(self, key):
        return self.d[key]


def test_baddict():
    bd = BadDict(a=BadDict(b='a->b'))
    assert bd['a']['b'] == 'a->b'
    with pytest.raises(KeyError):
        bd['missing']


def test_getitem_nested_through_non_dict_keyerror():
    """
    KeyError should be raised when trying to traverse through
    an object that does support `__getitem__` if the object
    raises KeyError due to no such key.
    """
    ud = objict(
        a=BadDict()
    )
    with pytest.raises(KeyError):
        ud['a.b']


def test_getitem_nested_through_non_dict_success():
    ud = objict(a=BadDict(b=objict(c='a->b->c')))
    assert ud['a.b'] == objict(c='a->b->c')
    assert ud['a.b.c'] == 'a->b->c'


def test_getitem_dotted_key_top_level_miss():
    ud = objict({'a.b': 2})
    with pytest.raises(KeyError):
        ud['a.b']


def test_getitem_subclass_missing():
    ud = DefaultDict(int)
    assert ud['missing'] == 0
    ud = DefaultDict(lambda: None)  # not type(None) for py2 compability
    assert ud['missing'] is None


def test_setitem_int_key():
    ud = objict()
    ud[1] = 'one'
    assert items(ud) == [(1, 'one')]


def test_setitem_none_key():
    ud = objict()
    ud[None] = 'None'
    assert items(ud) == [(None, 'None')]


def test_setitem_top_level():
    ud = objict()
    ud['one'] = 1
    assert items(ud) == [('one', 1)]


def test_setitem_second_level_first_exists():
    ud = objict()
    ud['one'] = objict()
    ud['one.two'] = 2
    assert items(ud) == [('one', objict(two=2))]


def test_setitem_second_level_first_missing():
    ud = objict()
    try:
        ud['one.two'] = 2
        pytest.fail()
    except KeyError as e:
        assert e.args == ('one',)


def test_delitem_top_level_exists():
    ud = objict({'one': 1})
    del ud['one']
    assert items(ud) == []


def test_delitem_top_level_missing():
    ud = objict(one=1)
    try:
        del ud['two']
        pytest.fails()
    except KeyError as e:
        assert e.args == ('two',)


def test_delitem_second_level_first_missing():
    ud = objict(one=1)
    try:
        del ud['two.three']
        pytest.fails()
    except KeyError as e:
        assert e.args == ('two',)


def test_delitem_second_level_first_exists_fail():
    ud = objict.fromdict({
        'one': {
            'two': 'one->two'
        }
    })
    try:
        del ud['one.three']
        pytest.fails()
    except KeyError as e:
        assert e.args == ('three',)


def test_delitem_second_level_success():
    ud = objict.fromdict({
        'one': {
            'two': 2,
            'blah': {
                'three': 3
            }
        }
    })
    del ud['one.blah']
    assert items(ud) == [
        ('one', objict(two=2))
    ]
    del ud['one.two']
    assert items(ud) == [('one', objict())]


def test_delitem_dotted_key():
    d = {'a.b': ''}
    ud = objict(d)
    with pytest.raises(KeyError):
        del ud['a']
    with pytest.raises(KeyError):
        del ud['a.b']


def test_pop_present():
    ud = objict(a='a', b='b')
    val = ud.pop('b')
    assert val == 'b'
    ud == objict(a='a')


def test_pop_missing_toplevel_no_default():
    with pytest.raises(KeyError):
        objict().pop('missing')
    with pytest.raises(KeyError):
        objict(a='aa').pop('aa')


def test_pop_missing_second_level_no_default():
    with pytest.raises(KeyError):
        objict().pop('a.b')


def test_pop_missing_default():
    objict().pop('foo', 'bar') == 'bar'


def test_pop_missing_second_level_default():
    assert objict().pop('a.b', mock.sentinel) is mock.sentinel
    assert objict(a={}).pop('a.b', mock.sentinel) is mock.sentinel


def test_pop_nested():
    d = {
        'a': 'aa',
        'b': 'bb',
        'a': {'b': {'c': 'a->b->c'}},
    }
    ud = objict.fromdict(d)
    assert ud['a.b.c'] == 'a->b->c'
    val = ud.pop('a.b.c')
    assert val == 'a->b->c'


def test_pop_dotted():
    d = {
        'a': objict(b='a->b'),
        'b': 'bb',
        'a.b': 'a.b'
    }
    ud = objict.fromdict(d)
    val = ud.pop('a.b')
    assert val == 'a->b'
    assert ud['a'] == objict()


def test_popitem_empty():
    with pytest.raises(KeyError):
        objict().popitem()


def test_popitem_nonempty():
    ud = objict(a='aa')
    assert ud
    assert ud.popitem() == ('a', 'aa')
    assert not ud


def test_popitem_dotted():
    orig = objict.fromdict({
        'a': {'b': 'a->b'},
        'a.b': 'a.b'
    })
    # popitem removes a random (key, value) pair, so do that enough
    # times to verify that when doing popitem on above, we only
    # ever see the 'a.b' top-level mapping removed or the
    # 'a' top-level mapping removed, never the child ('b', 'a->b') mapping
    for i in range(20):
        ud = objict.fromdict(orig)
        assert ud.popitem() in (
            ('a', objict(b='a->b')),
            ('a.b', 'a.b')
        )


def test_hasattr_top_level_success():
    assert hasattr(objict(one=1), 'one')


def test_hasattr_top_level_fail():
    d = objict(one=1)
    assert hasattr(d, 'two')
    assert getattr(d, 'two') is None


def test_hasattr_nested():
    ud = objict.fromdict({
        'a': {
            'b': 'a->b'
        }
    })
    assert hasattr(ud, 'a.b')
    assert ud.get("a.b") != None
    assert hasattr(ud, 'a')
    assert hasattr(ud['a'], 'b')


def test_hasattr_dotted():
    ud = objict({'a.b': 'a.b'})
    assert hasattr(ud, 'a.b')
    assert hasattr(ud, 'a')

def test_hasattr_nested_dotted():
    ud = objict.fromdict({
        'a': {
            'b': 'a->b',
            'c': 'a->c'
        },
        'a.b': 'a.b'
    })
    assert hasattr(ud, 'a')
    assert hasattr(ud, 'a.b')
    assert hasattr(ud, 'a.c')


def test_getattr_top_level_success():
    ud = objict(one=1)
    assert ud.one == 1


def test_getattr_top_level_fail():
    ud = objict(one=1)
    try:
        ud["two"]
        pytest.fail()
    except KeyError as e:
        pass
    assert ud.two is None


def test_getattr_dotted_key():
    ud = objict.fromdict({
        'a.b': 'abab',
        'a': {'b': 'abab'}
    })
    uda = ud['a']
    assert uda == objict(b='abab')
    assert getattr(ud, 'a.b') == 'abab'
    assert getattr(ud, 'a') == uda
    assert ud.a == uda
    assert ud.a.b == 'abab'


def test_setattr_objectstyle():
    ud = objict()
    ud.one = 1
    assert len(ud) == 1
    ud.one = objict()
    ud.one.two = 2
    assert ud.one.two == 2
    assert ud['one']['two'] == 2


def test_setattr_dotted_key():
    ud = objict(one=objict(two=2))
    setattr(ud, 'one.two', 'onetwo')
    assert ud['one.two'] == 2
    assert getattr(ud, 'one.two') == 'onetwo'
    assert ud['one'] == objict(two=2)
    assert getattr(ud, 'one') == objict(two=2)


def test_delattr_success():
    ud = objict(one=1)
    del ud.one
    assert len(ud) == 0


def test_delattr_fail():
    ud = objict(one=1)
    try:
        del ud.two
        pytest.fail()
    except AttributeError as e:
        assert e.args == ("no attribute 'two'",)


def test_delattr_dotted_key_present():
    d = {
        'one': {'two': 'one->two'}
    }
    ud = objict(d)
    del ud['one.two']
    assert items(ud) == [('one', {})]


def test_delattr_dotted_key_missing():
    d = {
        'one.two': 'one.two'
    }
    ud = objict(d)
    with pytest.raises(KeyError):
        del ud['one.two']
    assert ud == d


def test_delattr_dotted_key_present_dotted_toplevel():
    d = {
        'one.two': 'one.two',
        'one': {
            'two': 'one->two'
        }
    }
    ud = objict.fromdict(d)
    del ud['one.two']
    assert items(ud) == [
        ('one', objict()),
        ('one.two', 'one.two')
    ]


def test_get_missing_nodefault():
    assert objict().get('x') is None


def test_get_missing_default():
    assert objict().get('x', 1) == 1


def test_get_missing_child_nodefault():
    assert objict(one=objict()).get('one.two') is None


def test_get_missing_child_default():
    assert objict(one=objict()).get('one.two', 3) == 3


def test_get_nested_child():
    ud = objict(one=objict(two=2))
    assert ud.get('one.two') == 2


def test_get_none_nodefault():
    assert objict().get(None) is None


def test_get_none_default():
    assert objict().get(None, 3) == 3


def test_fromdict_classmethod():
    ud = objict.fromdict({})
    assert isinstance(ud, objict)
    assert ud == objict()


def test_fromdict_nested_dicts():
    d = {
        'a': {
            'b': {
                'c': 'a->b->c'
            }
        }
    }
    ud = objict.fromdict(d)
    elems = items(ud)
    assert elems == [
        ('a', objict({'b': objict({'c': 'a->b->c'})}))
    ]
    assert type(elems[0][1]) is objict


def test_fromdict_dotted_key():
    d = {
        'a.b': 'a.b',
        'a': {
            'b': 'a->b'
        }
    }
    ud = objict.fromdict(d)
    elems = items(ud)
    assert elems == [
        ('a', objict(b='a->b')),
        ('a.b', 'a.b')
    ]
    assert type(elems[0][1]) is objict


def test_fromdict_objicts():
    d = {
        'one.two': 'one.two',
        'one': {
            'two': 'one->two'
        }
    }
    orig = objict.fromdict(d)
    ud = objict.fromdict(orig)
    assert items(ud) == items(d)


def test_fromkeys_classmethod():
    ud = objict.fromkeys([])
    assert ud == objict()


def test_fromkeys_no_value():
    assert objict.fromkeys([]) == objict()
    assert objict.fromkeys(range(5)) == objict((i, None) for i in range(5))


def test_fromkeys_value():
    ud = objict.fromkeys([], 1)
    assert ud == objict()
    assert ud == dict.fromkeys([], 1)

    ud = objict.fromkeys(range(1), 1)
    assert ud == objict.fromdict({0: 1})
    assert ud == dict.fromkeys(range(1), 1)

    ud = objict.fromkeys(range(10), 0)
    assert ud == objict((i, 0) for i in range(10))
    assert ud == dict.fromkeys(range(10), 0)


def test_fromkeys_dotted_keys():
    elems = ['a.b', 'a', 'b']
    ud = objict.dict_from_keys(elems, objict())
    assert items(ud) == [
        ('a', objict()),
        ('a.b', objict()),
        ('b', objict())
    ]


def test_todict():
    ud = objict(foo='foofoo')
    d = ud.todict()
    assert d == {'foo': 'foofoo'}
    assert isinstance(d, dict)
    assert not isinstance(d, objict)


def test_todict_nested():
    ud = objict(foo=objict(bar='barbar'))
    d = ud.todict()
    assert isinstance(d['foo'], dict)
    assert not isinstance(d['foo'], objict)
    assert items(d) == [
        ('foo', {'bar': 'barbar'})
    ]


def test_todict_dotted_keys():
    orig = {
        'one.two': 'one.two',
        'one': {'two': 'one->two'}
    }
    ud = objict.fromdict(orig)
    assert isinstance(ud['one'], objict)
    d = ud.todict()
    assert items(d) == [
        ('one', {'two': 'one->two'}),
        ('one.two', 'one.two')
    ]
    assert type(items(d)[0][1]) is dict


def test_keys():
    d = dict(foo=dict(bar='barbar'))
    ud = objict.fromdict(d)
    assert ud.keys()
    assert ud.keys() == d.keys()


def test_keys_dotted():
    d = {
        'a.b': 'a.b',
        'a': {'b': 'a->b'}
    }
    ud = objict(d)
    assert sorted(ud.keys()) == sorted(d.keys())


def test_pickle_dumpsloads_simple():
    orig = objict({'one': 1, 'two': 2})
    unpickled = pickle.loads(pickle.dumps(orig))
    assert items(unpickled) == items(orig)
    assert isinstance(unpickled, objict)


def test_pickle_dumpsloads_dotted():
    orig = objict({'one.two': 'one.two'})
    pickled = pickle.dumps(orig)
    unpickled = pickle.loads(pickled)
    assert items(unpickled) == items(orig)


def test_pickle_dumpsloads_nested():
    orig = objict({'one': {'two': 'one->two'}})
    unpickled = pickle.loads(pickle.dumps(orig))
    assert items(unpickled) == items(orig)


def test_pickle_dumpsloads_nested_dotted():
    orig = objict.fromdict({
        'one': {
            'two': 'one->two'
        },
        'one.two': 'one.two'
    })
    unpickled = pickle.loads(pickle.dumps(orig))
    # assert unpickled == orig
    assert items(unpickled) == items(orig)
    assert isinstance(unpickled, objict)
    assert isinstance(unpickled['one'], objict)


def test_copy():
    orig = objict(
        foo=objict(
            bar={'baz': 'bazbaz'},
            boo=objict(boz='bozboz')
        )
    )
    assert isinstance(orig, objict)
    assert isinstance(orig['foo'], objict)
    assert isinstance(orig['foo']['bar'], dict)
    assert isinstance(orig['foo']['boo'], objict)
    copy = orig.copy()
    assert isinstance(copy, objict)
    assert orig == copy
    assert copy == orig
    assert copy.foo is orig.foo
    assert copy.foo.bar is orig.foo.bar
    assert copy.foo.boo is orig.foo.boo


def test_setdefault_value_plain_not_present():
    ud = objict()
    child = objict()
    res = ud.setdefault('child', child)
    assert ud['child'] is res
    assert ud['child'] is child
    assert set(ud.keys()) == set(['child'])


def test_setdefault_value_plain_present():
    child = objict()
    ud = objict(child=child)
    res = ud.setdefault('child', objict())
    assert ud['child'] is child
    assert ud['child'] is res


def test_setdefault_value_dotted_key_not_present():
    ud = objict(a=objict())
    child = objict()
    res = ud.setdefault('a.b', child)
    assert res is child
    assert ud['a.b'] is child


def test_setdefault_value_dotted_key_present():
    ud = objict.fromdict({
        'a': {
            'b': {
                'c1': 'abc'
            }
        }
    })
    res = ud.setdefault('a.b', objict())
    res['c2'] = 'cba'
    assert set(ud.keys()) == set(['a'])
    assert ud.get('a.b.c2') == 'cba'
    assert ud.get('a.b.c1') == 'abc'


def test_contains_plain_not_present():
    ud = objict(foo='bar')
    assert None not in ud
    assert 'foo' in ud
    assert 'bar' not in ud
    ud.pop('foo')
    assert ud == objict()
    assert 'foo' not in ud


def test_contains_plain_present():
    assert 'foo' in objict(foo='bar')
    assert 'bar' not in objict(foo='bar')
    assert None in objict.fromdict({None: ''})
    ud = objict.fromdict({1: 2, 3: 4})
    assert 1 in ud
    assert 2 not in ud
    assert 3 in ud


def test_contains_dotted_not_present():
    assert 'a.b' not in objict()
    assert 'foo.bar' not in objict(foo=objict(notbar='notbar'))


def test_contains_dotted_present_nonleaf():
    assert 'a.b' in objict(a=objict(b=objict(c=objict())))


def test_contains_dotted_present_leaf():
    assert 'a.b.c' in objict(a=objict(b=objict(c=objict())))


def test_contains_dotted_partial():
    assert 'a.b.c' not in objict(a=objict())


def test_len():
    assert len(objict()) == 0
    assert len(objict(a='')) == 1
    assert len(objict(a=objict(a=''))) == 1


def test_clear():
    ud = objict(a='')
    ud.clear()
    assert ud == objict()

    ud = objict({'a.b': ''})
    ud.clear()
    assert ud == objict()


def test_values():
    assert list(objict().values()) == []
    ud = objict(a='aa')
    assert list(ud.values()) == ['aa']
    ud['b'] = 'bb'
    assert sorted(ud.values()) == ['aa', 'bb']
    ud['a'] = objict(b='ab')


def test_values_dotted_keys():
    ud = objict.fromdict({
        'a': dict(b='ab'),
        'b': 'bb',
        'a.b': 'a.ba.b'
    })
    values = ud.values()
    assert 'bb' in values
    assert 'a.ba.b' in values
    assert objict(b='ab') in values
    del ud['a']
    assert sorted(ud.values()) == ['a.ba.b', 'bb']


@pytest.mark.skipif(sys.version_info >= (3,),
                    reason="only tested on python2")
def test_has_key():
    ud = objict()
    assert not ud.has_key('a')  # noqa
    ud['a'] = None
    assert ud.has_key('a')  # noqa
    assert not ud.has_key(None)  # noqa


def test_update():
    orig = {
        'a': {'b': 'a->b'},
        'a.b': 'a.b',
        'c': 'c'
    }
    ud = objict.fromdict(orig)
    ud.update({'a': 'a'})
    assert ud['a'] == 'a'
    assert ud['c'] == orig['c']
    with pytest.raises(TypeError):
        ud['a.b']  # ud['a'] doesn't support __getitem__
    assert getattr(ud, 'a.b') == 'a.b'

    ud = objict.fromdict(orig)
    ud.update(objict({'a.b': 'b.a'}))
    assert ud['a.b'] == 'a->b'
    assert ud['a'] == objict(b='a->b')
    assert ud['c'] == 'c'


def test_dir_includes_dict_methods():
    attrs = set(dir(objict()))
    for attr in dir({}):
        assert attr in attrs


def test_dir_includes_objict_instance_methods():
    assert 'todict' in dir(objict())


def test_dir_includes_class_methods():
    assert 'fromdict' in dir(objict())


def test_dir_includes_keys():
    ud = objict(foo='foofoo', bar='barbar')
    attrs = dir(ud)
    assert 'foo' in attrs
    assert 'bar' in attrs


def test_dir_includes_dotted_keys():
    ud = objict({'a.b.c': 'a.b.c'})
    assert 'a.b.c' in dir(ud)


def test_dir_omits_nested_keys():
    ud = objict.fromdict({
        'a': {
            'b': 'a->b'
        },
        'a.c': 'a.c'
    })
    attrs = dir(ud)
    assert 'a' in attrs
    assert 'a.b' not in attrs
    assert 'a.c' in attrs


def test_subclass_missing_getitem_success():
    ud = DefaultDict(fail_factory, a=3)
    assert ud['a'] == 3


def test_subclass_missing_getitem_fail():
    ud = DefaultDict(int)
    assert ud['b'] == int()


def test_subclass_missing_contains():
    ud = DefaultDict(int, b=1)
    assert 'a' not in ud
    assert 'b' in ud


def test_subclass_missing_get_fail():
    ud = DefaultDict(int)
    assert ud.get('b') is None
    assert ud.get('b', 'foo') == 'foo'


def test_subclass_missing_delitem_success():
    ud = DefaultDict(int, a=1)
    del ud['a']
    assert 'a' not in ud


def test_subclass_missing_delitem_fail():
    ud = DefaultDict(fail_factory)
    with pytest.raises(KeyError):
        del ud['a']


def test_subclass_missing_setdefault_notpresent():
    ud = DefaultDict(fail_factory)
    obj = object()
    res = ud.setdefault('a', obj)
    assert res is obj
    assert ud['a'] is res


def test_subclass_missing_setdefault_present():
    ud = DefaultDict(fail_factory)
    obj = object()
    ud['a'] = obj
    res = ud.setdefault('a', object())
    assert res is obj


def test_subclass_missing_todict():
    # verifying that it doesn't use __missing__ inadvertently
    ud = DefaultDict(fail_factory)
    ud['a'] = 1
    assert ud.copy() == ud


def test_subclass_missing_getattr():
    ud = DefaultDict(fail_factory)
    ud.foo = 'bar'
    assert getattr(ud, 'foo') == 'bar'
    assert ud.moo is None


def test_subclass_missing_instance_variable_ignored():
    class MyDict(objict):
        def __init__(self, *args, **kwargs):
            objict.__init__(self, *args, **kwargs)
            self.__dict__['__missing__'] = fail_factory
    md = MyDict()
    assert md.__missing__ is fail_factory
    with pytest.raises(KeyError):
        md['a']
    assert md.a is None


def test_basic_merge():
    d1 = {"a": 1, "b": 2}
    d2 = {"b": 3, "c": 4}
    result = merge_dicts(d1, d2)
    assert result == {"a": 1, "b": 3, "c": 4}

def test_nested_merge():
    d1 = {"a": {"x": 10, "y": 20}, "b": 2}
    d2 = {"a": {"y": 25, "z": 30}, "b": 3}
    result = merge_dicts(d1, d2)
    assert result == {"a": {"x": 10, "y": 25, "z": 30}, "b": 3}

def test_remove_key_with_none():
    d1 = {"a": 1, "b": {"c": 2}}
    d2 = {"b": {"c": None}}
    result = merge_dicts(d1, d2)
    assert result == {"a": 1}

def test_remove_empty_nested_dict():
    d1 = {"a": {"x": 10}, "b": {"y": 20}}
    d2 = {"a": {"x": None}, "b": {}}
    result = merge_dicts(d1, d2)
    assert result == {"b": {"y": 20}}

def test_remove_none_nested_dict():
    d1 = {"a": {"x": 10}, "b": {"y": 20}}
    d2 = {"a": {"x": None}, "b": None}
    result = merge_dicts(d1, d2)
    assert result == {}

def test_add_new_key():
    d1 = {"a": 1}
    d2 = {"b": 2}
    result = merge_dicts(d1, d2)
    assert result == {"a": 1, "b": 2}

def test_smart_parse_date():
    test_cases = [
        ("12/31/2023", datetime.datetime(2023, 12, 31, 0, 0)),
        ("31/12/2023", datetime.datetime(2023, 12, 31, 0, 0)),
        ("2023-12-31", datetime.datetime(2023, 12, 31, 0, 0)),
        ("31-12-2023", datetime.datetime(2023, 12, 31, 0, 0)),
        ("2023-12-31 23:59:59", datetime.datetime(2023, 12, 31, 23, 59, 59)),
        ("12/31/23 11:59 PM", datetime.datetime(2023, 12, 31, 23, 59)),
        ("20231231", datetime.datetime(2023, 12, 31, 0, 0)),
        ("December 31, 2023", datetime.datetime(2023, 12, 31, 0, 0)),
        ("31 December 2023", datetime.datetime(2023, 12, 31, 0, 0)),
        ("Dec 31, 2023", datetime.datetime(2023, 12, 31, 0, 0)),
        ("31 Dec 2023", datetime.datetime(2023, 12, 31, 0, 0)),
        ("2023-12-31T23:59:59", datetime.datetime(2023, 12, 31, 23, 59, 59))
    ]

    for date_str, expected in test_cases:
        assert parse_date(date_str) == expected



@pytest.fixture
def objict_instance():
    return objict({
        'integer': '42',
        'float': '3.14',
        'bool_true': 'True',
        'bool_false': 'False',
        'list': 'x,y,z',
        'nested_dict': '{"key": "value"}',
        'date_str': '2023-10-01',
        'datetime_str': '2023-10-01T15:30:00',
        'invalid_number': 'invalid',
    })

def test_integer_conversion(objict_instance):
    assert objict_instance.get_typed('integer', typed=int) == 42
    assert objict_instance.get_typed('invalid_number', default=0, typed=int) == 0

def test_float_conversion(objict_instance):
    assert objict_instance.get_typed('float', typed=float) == 3.14
    assert objict_instance.get_typed('invalid_number', default=0.0, typed=float) == 0.0

def test_boolean_conversion(objict_instance):
    assert objict_instance.get_typed('bool_true', typed=bool) is True
    assert objict_instance.get_typed('bool_false', typed=bool) is False
    assert objict_instance.get_typed('invalid_number', default=False, typed=bool) is False

def test_list_conversion(objict_instance):
    assert objict_instance.get_typed('list', typed=list) == ['x', 'y', 'z']
    assert objict_instance.get_typed('invalid_number', default=[], typed=list) == ['invalid']

def test_dict_conversion(objict_instance):
    assert objict_instance.get_typed('nested_dict', typed=dict) == objict({'key': 'value'})
    assert objict_instance.get_typed('invalid_number', default=objict(), typed=dict) == objict()

def test_date_conversion(objict_instance):
    expected_date = datetime.date(2023, 10, 1)
    assert objict_instance.get_typed('date_str', typed=datetime.date) == expected_date

def test_datetime_conversion(objict_instance):
    expected_datetime = datetime.datetime(2023, 10, 1, 15, 30)
    assert objict_instance.get_typed('datetime_str', typed=datetime.datetime) == expected_datetime

def test_default_return_value(objict_instance):
    assert objict_instance.get_typed('non_existent', default='fallback', typed=str) == 'fallback'

def test_load_from_file():
    example_json_path = os.path.join(current_dir, "example.json")
    info = objict.from_file(example_json_path)
    assert "name" in info
    assert info["name"] == "Bob"
    assert info["address"]["street"] == "123 Linda Lane"
