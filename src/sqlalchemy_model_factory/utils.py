import functools
import inspect
from types import MappingProxyType
from typing import Any, Callable, Dict, List, Optional, Tuple


def autoincrement(fn: Optional[Callable] = None, *, start: int = 1):  # pragma: no cover
    """Decorate registered callables to provide them with a source of uniqueness.

    Args:
        fn: The callable
        start: The starting number of the sequence to generate

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


def for_model(typ):
    """Decorate a factory that returns a `Mapping` type in order to coerce it into the `typ`.

    This decorator is only invoked in the context of model factory usage. The intent is that
    a factory function could be more generally useful, such as to create API inputs, that
    also happen to correspond to the creation of a model when invoked during a test.

    Examples:
        >>> class Model:
        ...     def __init__(self, **kwargs):
        ...         self.kw = kwargs
        ...
        ...     def __repr__(self):
        ...         return f"Model(a={self.kw['a']}, b={self.kw['b']}, c={self.kw['c']})"

        >>> @for_model(Model)
        ... def new_model(a, b, c):
        ...     return {'a': a, 'b': b, 'c': c}

        >>> new_model(1, 2, 3)
        {'a': 1, 'b': 2, 'c': 3}
        >>> new_model.for_model(1, 2, 3)
        Model(a=1, b=2, c=3)
    """

    def wrapper(fn):
        def for_model(*args, **kwargs):
            result = fn(*args, **kwargs)
            return typ(**result)

        fn.for_model = for_model
        return fn

    return wrapper


class fluent:
    """Decorate a function with `fluent` to enable it to be called in a "fluent" style.

    Examples:
        >>> @fluent
        ... def foo(a, b=None, *args, c=3, **kwargs):
        ...     print(f'(a={a}, b={b}, c={c}, args={args}, kwargs={kwargs})')

        >>> foo.kwargs(much=True, surprise='wow').a(4).bind()
        (a=4, b=None, c=3, args=(), kwargs={'much': True, 'surprise': 'wow'})

        >>> foo.args(True, 'wow').a(5).bind()
        (a=5, b=None, c=3, args=(True, 'wow'), kwargs={})

        >>> partial = foo.a(1)
        >>> partial.b(5).bind()
        (a=1, b=5, c=3, args=(), kwargs={})

        >>> partial.b(6).bind()
        (a=1, b=6, c=3, args=(), kwargs={})
    """

    def __init__(self, fn, signature=None, pending_args=None):
        self.fn = fn

        self.signature = signature or inspect.signature(fn)
        self.pending_args = pending_args or {}

        for parameter in self.signature.parameters.values():
            if parameter.name == self.bind.__name__:
                raise ValueError(
                    f"`fluent` reserves the name {self.bind.__name__}, please choose a different parameter name"
                )

            if parameter.name in self.pending_args:
                continue

            setattr(self, parameter.name, self.__apply(parameter))

    def __apply(self, parameter):
        @functools.wraps(self.fn)
        def wrapper(*args, **kwargs):
            signature = inspect.Signature(parameters=[parameter])
            bound_args = signature.bind(*args, **kwargs)
            bound_args.apply_defaults()
            return self.__class__(
                self.fn,
                self.signature,
                {**self.pending_args, parameter.name: bound_args.arguments},
            )

        return wrapper

    def bind(
        self,
        *,
        call_before: Optional[Callable] = None,
        call_after: Optional[Callable] = None,
    ):
        """Finalize the call chain for a fluently called factory.

        Args:
            call_before: When provided, calls the given callable, supplying the args and kwargs
                being sent into the factory function before actually calling it. If the `call_before`
                function returns anything, the 2-tuple of (args, kwargs) will be replaced with the
                ones passed into the `call_before` function.
            call_after: When provided, calls the given callable, supplying the result of the factory
                function call after having called it. If the `call_after` function returns anything,
                the result of `call_after` will be replaced with the result of the factory function.
        """
        unsupplied_args = set(self.signature.parameters) - set(self.pending_args)

        for arg in unsupplied_args:
            fn = getattr(self, arg)
            self = fn()

        args: List[Any] = []
        kwargs: Dict[Any, Any] = {}

        for parameter in self.signature.parameters.values():
            kind_map: Dict[Any, Tuple[Callable, bool]] = {
                parameter.POSITIONAL_ONLY: (args.append, True),
                parameter.POSITIONAL_OR_KEYWORD: (args.append, True),
                parameter.VAR_POSITIONAL: (args.extend, True),
                parameter.VAR_KEYWORD: (kwargs.update, True),
                parameter.KEYWORD_ONLY: (kwargs.update, False),
            }

            pending_arg = self.pending_args[parameter.name]

            update_fn, key_on_param = kind_map[parameter.kind]
            if key_on_param:
                update_fn(pending_arg[parameter.name])
            else:
                update_fn(pending_arg)

        if call_before:
            call_before_result = call_before(args, MappingProxyType(kwargs))
            if call_before_result:
                args, kwargs = call_before_result

        result = self.fn(*args, **kwargs)

        if call_after:
            call_after_result = call_after(result)
            if call_after_result:
                return call_after_result

        return result
