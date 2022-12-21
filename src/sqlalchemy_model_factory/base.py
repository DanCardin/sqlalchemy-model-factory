from typing import Any, Dict, Optional, Set

from sqlalchemy_model_factory.registry import Method, Registry

_ITERABLES = (list, tuple, set)


class Options:
    def __init__(self, commit=True, cleanup=True):
        self.commit = commit
        self.cleanup = cleanup


class ModelFactory:
    def __init__(self, registry: Registry, session, options=None):
        self.registry = registry
        self.new_models: Set = set()
        self.session = session

        self.options = Options(**options or {})

    def __enter__(self):
        return Namespace.from_registry(self.registry, manager=self)

    def __exit__(self, *_):
        self.remove_managed_data()
        return False

    def remove_managed_data(self):
        if not self.options.cleanup:
            return

        # Events inside the context manager could have left pending state.
        self.session.rollback()

        if getattr(self.session, "autocommit", None):
            self.session.begin()

        while self.session.identity_map:
            model = next(iter(self.session.identity_map.values()))
            self.session.delete(model)
            self.session.flush()

        self.new_models.clear()

        if self.options.commit:
            self.session.commit()

    def add_result(self, result, commit=True, merge=False):
        # The state of the session is unknown at this point. Ensure it's empty.
        self.session.rollback()

        # When the session is autocommit, it is expected that you start the transaction manually.
        if getattr(self.session, "autocommit", None):
            self.session.begin()

        if merge:
            if isinstance(result, _ITERABLES):
                items = []
                for item in result:
                    items.append(self.session.merge(item))
                result = items
            else:
                result = self.session.merge(result)
        else:
            if isinstance(result, _ITERABLES):
                for item in result:
                    self.session.add(item)
            else:
                self.session.add(result)

        self.new_models = self.new_models.union(self.session.new)

        self.session.flush()
        if commit:
            # Again, we cannot predict what's happening elsewhere, so we should try to keep models
            # appear to return as they would if freshly queried from the database.
            if self.options.commit:
                self.session.commit()
            else:
                self.session.flush()

            if isinstance(result, _ITERABLES):
                for item in result:
                    self.session.refresh(item)
            else:
                self.session.refresh(result)

        return result


class Namespace:
    """Represent a collection of registered namespaces or callable `Method`s.

    A `Namespace` is a recursive structure used to form the path traversal
    from the root namespace to any registered function.

    A method can be registered at any level, including previously registered path
    names, so long as that exact path + leaf is not yet registered.

    Examples:
        >>> from sqlalchemy_model_factory.registry import Method

        >>> method1 = Method(lambda: 1)
        >>> method2 = Method(lambda: 2)
        >>> namespace = Namespace(method1, foo=Namespace(method2))

        >>> namespace()
        1

        >>> namespace.foo()
        2
    """

    @classmethod
    def from_registry(cls, registry: Registry, manager=None):
        """Produce a `Namespace` tree structure from a flat `Registry` structure.

        Examples:
            >>> registry = Registry()
            >>> @registry.register_at("foo", name='bar')
            ... def foo_bar():
            ...     return 5

            >>> @registry.register_at(name='foo')
            ... def foo_bar():
            ...     return 6

            >>> namespace = Namespace.from_registry(registry)
            >>> namespace.foo()
            6
            >>> namespace.foo.bar()
            5
        """
        tree: Dict[str, Any] = {}

        for namespace in registry.namespaces():
            context = tree
            for path_item in namespace:
                context = context.setdefault(path_item, {})

            methods = registry.methods(*namespace)
            for name, method in methods.items():
                context.setdefault(name, {})["__call__"] = method

        return cls.from_tree(tree, manager=manager)

    @classmethod
    def from_tree(cls, tree, manager=None):
        attrs = {}
        for key, raw_value in tree.items():
            if key == "__call__":
                value = raw_value
            else:
                value = cls.from_tree(raw_value, manager=manager)
            attrs[key] = value

        return cls(_manager=manager, **attrs)

    def __init__(self, __call__: Optional[Method] = None, *, _manager=None, **attrs):
        self.__manager = _manager
        self.__method = __call__

        for attr, value in attrs.items():
            setattr(self, attr, value)

    def __getattr__(self, attr):
        """Catch unset attribute names to provide a better error message."""
        namespaces = []
        methods = []
        for name, item in self.__dict__.items():
            if name.startswith(f"_{self.__class__.__name__}"):
                continue

            if isinstance(item, self.__class__):
                namespaces.append(name)
            else:
                methods.append(name)

        method_names = "N/A"
        if methods:
            method_names = ", ".join(methods)

        namespace_names = "N/A"
        if namespaces:
            namespace_names = ", ".join(namespaces)

        raise AttributeError(
            f"{self.__class__.__name__} has no attribute '{attr}'. Available methods include: {method_names}. Available nested namespaces include: {namespace_names}."
        )

    def __call__(self, *args, commit_=None, merge_=None, **kwargs):
        """Provide an access guarding mechanism around callables.

        Allows for a hook into, for example, the calling of namespace functions
        for the purposes of keeping track of the results of the function calls,
        or otherwise manipulating the input arguments.
        """
        if self.__method is None:
            raise RuntimeError(
                f"{self} has no registered factory function and cannot be called."
            )

        callable = self.__method.fn
        if hasattr(callable, "for_model"):
            callable = callable.for_model

        result = callable(*args, **kwargs)

        if self.__manager:
            commit = (
                commit_
                if commit_ is not None
                else self.__method.commit
                if self.__method.commit is not None
                else True
            )
            merge = (
                merge_
                if merge_ is not None
                else self.__method.merge
                if self.__method.merge is not None
                else False
            )
            result = self.__manager.add_result(result, commit=commit, merge=merge)
        return result

    def __repr__(self):
        cls_name = self.__class__.__name__

        attrs = []
        for key, value in self.__dict__.items():
            if key.endswith("__manager"):
                continue

            if key == f"_{cls_name}__method":
                if value is None:
                    continue

                attrs.append(f"__call__={value}")
            else:
                attrs.append(f"{key}={repr(value)}")

        attrs_str = ", ".join(attrs)
        return f"{cls_name}({attrs_str})"
