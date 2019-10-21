import pytest
from sqlalchemy import Column, ForeignKey, types
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

from sqlalchemy_model_factory.base import ModelFactory
from sqlalchemy_model_factory.registry import registry
from sqlalchemy_model_factory.utils import for_model
from tests import get_session

Base = declarative_base()


class Foo(Base):
    __tablename__ = "foo"

    id = Column(types.Integer(), autoincrement=True, primary_key=True)
    bar_id = Column(types.Integer(), ForeignKey("bar.id"), nullable=False)

    bar = relationship("Bar", uselist=False)


class Bar(Base):
    __tablename__ = "bar"

    id = Column(types.Integer(), autoincrement=True, primary_key=True)


class TestRegistry:
    def setup(self):
        registry.clear()

    def test_default_function_name(self):
        registry.register_at("thing")(1)
        assert registry.namespaces() == ["thing"]
        assert registry.methods("thing") == {"new": 1}

    def test_explicit_function_name(self):
        registry.register_at("thing", "foo")(1)
        assert registry.namespaces() == ["thing"]
        assert registry.methods("thing") == {"foo": 1}

    def test_registration_duplicate(self):
        registry.register_at("thing", "foo")(1)
        with pytest.raises(ValueError):
            registry.register_at("thing", "foo")(1)


class TestModelFactory:
    def setup(self):
        registry.clear()

    def test_exit_removal(self):
        session = get_session(Base)

        @registry.register_at("thing")
        def new_thing():
            return [Bar(), Bar()]

        @registry.register_at("thing", name="foo")
        def new_thing_foo(arg1):
            return Foo(bar=Bar())

        with ModelFactory(registry, session) as mm:
            mm.thing.new()
            mm.thing.foo(1)

            assert len(session.query(Foo).all()) == 1
            assert len(session.query(Bar).all()) == 3

        assert len(session.query(Foo).all()) == 0
        assert len(session.query(Bar).all()) == 0

    def test_mid_session_delete(self):
        session = get_session(Base)

        @registry.register_at("thing")
        def new_thing():
            return [Bar(), Bar()]

        @registry.register_at("thing", name="foo")
        def new_thing_foo(arg1):
            return Foo(bar=Bar())

        with ModelFactory(registry, session) as mm:
            bar1, bar2 = mm.thing.new()
            foo = mm.thing.foo(1)

            assert len(session.query(Foo).all()) == 1
            assert len(session.query(Bar).all()) == 3

            session.delete(bar1)
            assert len(session.query(Bar).all()) == 2

            session.delete(foo)
            assert len(session.query(Foo).all()) == 0
            assert len(session.query(Bar).all()) == 2

        assert len(session.query(Foo).all()) == 0
        assert len(session.query(Bar).all()) == 0

    def test_for_model(self):
        session = get_session(Base)

        @registry.register_at("thing")
        @for_model(Foo)
        def new_thing():
            bar = Bar(id=1)
            return {"bar_id": bar.id}

        with ModelFactory(registry, session) as mm:
            foo = mm.thing.new()
            assert isinstance(foo, Foo)
