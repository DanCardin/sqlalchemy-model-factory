from collections.abc import Iterable


class ModelFactory:
    def __init__(self, registry, session):
        self.registry = registry
        self.new_models = set()
        self.session = session

    def __enter__(self):
        return namespace_from_registry(Namespace, self, self.registry)

    def __exit__(self, *_):
        self.remove_managed_data()
        return False

    def remove_managed_data(self):
        # Events inside the context manager could have left pending state.
        self.session.rollback()

        if self.session.autocommit:
            self.session.begin()

        for model in self.new_models:
            self.session.delete(model)

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
            self.session.commit()
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
        result = self.__obj(*args, **kwargs)
        self.__manager.add_result(result, commit=commit_)
        return result


def namespace_from_registry(cls, manager, registry):
    attrs = {
        namespace: cls(manager, **registry.methods(namespace))
        for namespace in registry.namespaces()
    }
    return cls(manager, **attrs)


class Namespace:
    def __init__(self, manager, **attrs):
        for attr, method in attrs.items():
            setattr(self, attr, AccessGuard(manager, method))
