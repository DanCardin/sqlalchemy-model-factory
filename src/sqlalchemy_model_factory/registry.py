class Registry:
    def __init__(self):
        self._registered_methods = {}

    def namespaces(self):
        return list(self._registered_methods)

    def methods(self, namespace):
        return self._registered_methods[namespace]

    def clear(self):
        self._registered_methods = {}

    def register_at(self, namespace, name="new"):
        def wrapper(fn):
            registry_namespace = self._registered_methods.setdefault(namespace, {})
            if name in registry_namespace:
                raise ValueError(
                    "Name '{}' is already registered in namespace {}".format(
                        name, namespace
                    )
                )

            registry_namespace[name] = fn
            return fn

        return wrapper


registry = Registry()
register_at = registry.register_at
