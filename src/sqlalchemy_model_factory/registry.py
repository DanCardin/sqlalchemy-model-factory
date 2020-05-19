class Registry:
    def __init__(self):
        self._registered_methods = {}

    def namespaces(self):
        return list(self._registered_methods)

    def methods(self, *namespace_path):
        return self._registered_methods[namespace_path]

    def clear(self):
        self._registered_methods = {}

    def register_at(self, *namespace_path, name="new"):
        def wrapper(fn):
            registry_namespace = self._registered_methods.setdefault(namespace_path, {})
            if name in registry_namespace:
                raise ValueError(
                    "Name '{}' is already registered in namespace {}".format(
                        name, namespace_path
                    )
                )

            registry_namespace[name] = fn
            return fn

        return wrapper


registry = Registry()
register_at = registry.register_at
