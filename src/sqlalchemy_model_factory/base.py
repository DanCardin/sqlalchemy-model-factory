from collections.abc import Iterable


class Options:
    def __init__(self, commit=True, cleanup=True):
        self.commit = commit
        self.cleanup = cleanup


class ModelFactory:
    def __init__(self, registry, session, options=None):
        self.registry = registry
        self.new_models = set()
        self.session = session

        self.options = Options(**options or {})

    def __enter__(self):
        return namespace_from_registry(Namespace, self, self.registry)

    def __exit__(self, *_):
        self.remove_managed_data()
        return False

    def remove_managed_data(self):
        if not self.options.cleanup:
            return

        # Events inside the context manager could have left pending state.
        self.session.rollback()

        if self.session.autocommit:
            self.session.begin()

        while self.session.identity_map:
            model = next(iter(self.session.identity_map.values()))
            self.session.delete(model)
            self.session.flush()

        self.new_models.clear()

        if self.options.commit:
            self.session.commit()

    def add_result(self, result, commit=True):
        # The state of the session is unknown at this point. Ensure it's empty.
        self.session.rollback()

        # When the session is autocommit, it is expected that you start the transaction manually.
        if self.session.autocommit:
            self.session.begin()

        if isinstance(result, Iterable):
            self.session.add_all(result)
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

            if isinstance(result, Iterable):
                for item in result:
                    self.session.refresh(item)
            else:
                self.session.refresh(result)

        return result


class AccessGuard:
    """A descriptor that controls access to managed functions and their return values.
    """

    def __init__(self, manager, obj):
        self.__manager = manager
        self.__obj = obj

    def __getattr__(self, attr):
        return getattr(self.__obj, attr)

    def __call__(self, *args, commit_=True, **kwargs):
        callable = self.__obj
        if hasattr(callable, "for_model"):
            callable = callable.for_model

        result = callable(*args, **kwargs)
        self.__manager.add_result(result, commit=commit_)
        return result


def namespace_from_registry(cls, manager, registry, instance=None):
    if not instance:
        instance = cls(manager)

    for namespace in registry.namespaces():
        methods = registry.methods(*namespace)

        context = instance
        for path_item in namespace:
            if not hasattr(context, path_item):
                setattr(context, path_item, cls(manager))
            context = getattr(context, path_item)

        for name, method in methods.items():
            setattr(context, name, AccessGuard(manager, method))

    return instance


class Namespace:
    def __init__(self, manager, **attrs):
        for attr, method in attrs.items():
            setattr(self, attr, AccessGuard(manager, method))

    def __getattr__(self, attr):
        """Catch unset attribute names to provide a better error message.
        """
        namespaces = []
        methods = []
        for name, item in self.__dict__.items():
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
