import functools


def autoincrement(fn=None, *, start=1):  # pragma: no cover
    """Decorate registered callables to provide them with a source of uniqueness.

    Examples:
    >>> @autoincrement
    ... def new(autoincrement=1):
    ...     return autoincrement
    >>> new()
    1
    >>> new()
    2

    >>> @autoincrement(start=4)
    ... def new(autoincrement=1):
    ...     return autoincrement
    >>> new()
    4
    >>> new()
    5
    """

    def wrapper(fn):
        wrapper.initial = start

        @functools.wraps(fn)
        def decorator(*args, **kwargs):
            result = fn(*args, autoincrement=wrapper.initial, **kwargs)
            wrapper.initial += 1
            return result

        return decorator

    if fn:
        return wrapper(fn)
    return wrapper
