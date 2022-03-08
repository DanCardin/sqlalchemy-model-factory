import pytest
from sqlalchemy import Column, types
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy_model_factory.base import ModelFactory, Namespace
from sqlalchemy_model_factory.registry import Method, Registry
from tests import get_session


class TestNamespace:
    def test_empty_namespace_from_registry(self):
        Namespace.from_registry(Registry())

    def test_empty_namespace(self):
        n = Namespace(None)
        with pytest.raises(AttributeError) as e:
            n.foo()

        assert "no attribute 'foo'" in str(e.value)
        assert "methods include: N/A" in str(e.value)

    def test_expose_available_methods_in_error(self):
        n = Namespace(None, foo=None, bar=None)
        with pytest.raises(AttributeError) as e:
            n.wat()

        assert "no attribute 'wat'" in str(e.value)
        assert "methods include: foo, bar" in str(e.value)

    def test_repr(self):
        n = Namespace(None, foo=None, bar=Method(4), baz=Namespace(4))
        result = repr(n)
        assert result == "Namespace(foo=None, bar=Method(4), baz=Namespace(__call__=4))"


class TestModelFactory:
    Base = declarative_base()

    class Foo(Base):
        __tablename__ = "foo"

        id = Column(types.Integer(), autoincrement=True, primary_key=True)

    def test_it_allows_method_and_namespace_to_share_a_name(self):

        session = get_session(self.Base)

        registry = Registry()

        @registry.register_at("foo", "bar", name="baz")
        def baz():
            return self.Foo(id=4)

        @registry.register_at("foo", name="bar")
        def bar():
            return self.Foo(id=10)

        with ModelFactory(registry, session) as mf:
            bar_result = mf.foo.bar()
            assert bar_result.id == 10

            baz_result = mf.foo.bar.baz()
            assert baz_result.id == 4

            foos = session.query(self.Foo).all()
            assert len(foos) == 2

    def test_cannot_call_namespace_with_no_method(self):
        session = get_session(self.Base)

        registry = Registry()

        @registry.register_at("foo", "bar", name="baz")
        def baz():
            return self.Foo(id=4)

        with ModelFactory(registry, session) as mf:
            with pytest.raises(RuntimeError):
                mf.foo()
