from sqlalchemy_model_factory.registry import Registry


def declarative(_cls=None, *, registry=None):
    """Decorate a base object on which factory functions reside.

    The primary benefit of declaratively specifying the factory function tree
    is that it enables references to the factory to be type aware, enabling
    things like "Go to Definition".

    *Note* interior classes to the decorator, including both the root class, as
    well as any nested class or attributes which are raw types, will be
    instantiated. This is notable, primarily in the event that an `__init__`
    is defined on the class for whatever reason. Each class will be instantiated
    once without arguments.

    Examples:
        >>> @declarative
        ... class ModelFactory:
        ...     class namespace:
        ...         def fn():
        ...             ...

        >>> from sqlalchemy_model_factory.pytest import create_registry_fixture
        >>> mf_registry = create_registry_fixture(ModelFactory)

        >>> def test_factory(mf: ModelFactory):
        ...    ...

        Alternatively, a registry can be provided to the decorator directly,
        if you have one pre-constructed.

        >>> registry = Registry()
        >>>
        >>> @declarative(registry=registry)
        ... class ModelFactory:
        ...     def fn():
        ...         ...

    *Note* due to the dynamic nature of fixtures, you must annotate the fixture
    argument to have the type of the root, declarative class.
    """
    registry = registry or Registry()

    def _root_declarative(cls):
        """Perform the declarative mapping to the root class.

        This is distinct from the recursive `_declarative` function in that this:

            - Creates a registry if one was not provided overall.
            - Assigns the registry as a root attribute to the factory itself.
        creates
        """
        _declarative(cls)

        cls.registry = registry
        return cls

    def _declarative(cls, *, context=None):
        """Traverse the heirarchy of objects on the root factory, recursively."""
        context = context or []

        if not hasattr(cls, "__dict__"):
            return

        # Instantiate classes to enable non-`staticmethod`s to work properly.
        if isinstance(cls, type):
            cls = cls()

        for name in dir(cls):
            # Ignore private attributes. These classes are intended to be used as
            # an api, it makes no sense to collect "private" attributes!
            if name != "__call__" and name.startswith("_"):
                continue

            attr = getattr(cls, name)

            # Callables can now be registered to the function registry.
            if name == "__call__":
                *rcontext, rname = context
                registration = registry.register_at(*rcontext, name=rname)
                registration(attr)
                continue

            # Finally, recurse into the object to search for more!
            new_context = [*context, name]
            _declarative(attr, context=new_context)

    if _cls is not None:
        return _root_declarative(_cls)
    return _root_declarative


class DeclarativeMF:
    """Provide an alternative to the class decorator for declarative base factories.

    Today there's no meaningful difference between the decorator and the subclass
    method, except the interface.

    Examples:
        >>> class ModelFactory(DeclarativeMF):
        ...    def default(id: int = None):
        ...        return Foo(id=id)

        or

        >>> registry = Registry()
        >>>
        >>> class ModelFactory(DeclarativeMF, registry=registry):
        ...    def default(id: int = None):
        ...        return Foo(id=id)
    """

    @classmethod
    def __init_subclass__(cls, registry=None):
        declarative(cls, registry=registry)
