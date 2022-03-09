from typing import Callable, Generic, Optional, TypeVar


class Registry:
    def __init__(self):
        self._registered_methods = {}

    def namespaces(self):
        return list(self._registered_methods)

    def methods(self, *namespace_path):
        return self._registered_methods[namespace_path]

    def clear(self):
        self._registered_methods = {}

    def register_at(
        self,
        *namespace_path,
        name="new",
        merge: Optional[bool] = None,
        commit: Optional[bool] = None,
    ):
        def wrapper(fn):
            registry_namespace = self._registered_methods.setdefault(namespace_path, {})
            if name in registry_namespace:
                raise ValueError(
                    "Name '{}' is already registered in namespace {}".format(
                        name, namespace_path
                    )
                )

            method = fn
            if not isinstance(fn, Method):
                method = Method(fn, merge=merge, commit=commit)

            registry_namespace[name] = method
            return fn

        return wrapper


R = TypeVar("R")


class Method(Generic[R]):
    def __init__(
        self,
        fn: Callable[..., R],
        commit: Optional[bool] = None,
        merge: Optional[bool] = None,
    ):
        self.fn = fn
        self.commit = commit
        self.merge = merge

    def __repr__(self):
        result = f"{self.__class__.__name__}({self.fn}"
        if self.commit is not None:
            result += f", commit={self.commit}"

        if self.merge is not None:
            result += f", merge={self.merge}"
        result += ")"
        return result

    def __call__(self, *args, **kwargs) -> R:
        return self.fn(*args, **kwargs)


registry = Registry()
register_at = registry.register_at
