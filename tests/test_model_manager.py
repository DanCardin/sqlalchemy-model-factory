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

    bar2s = relationship("Bar2", cascade="all, delete-orphan", passive_deletes=True)


class Bar2(Base):
    __tablename__ = "bar2"

    id = Column(types.Integer(), autoincrement=True, primary_key=True)
    bar_id = Column(
        types.Integer(), ForeignKey("bar.id", ondelete="CASCADE"), nullable=False
    )

    bar = relationship("Bar")


class Baz(Base):
    __tablename__ = "baz"

    id = Column(types.Integer(), autoincrement=True, primary_key=True)
    bar_id = Column(
        types.Integer(), ForeignKey("bar.id", ondelete="CASCADE"), nullable=False
    )

    bar = relationship("Bar")


class TestRegistry:
    def setup(self):
        registry.clear()

    def test_default_function_name(self):
        registry.register_at("thing")(1)
        assert registry.namespaces() == [("thing",)]
        assert registry.methods("thing")["new"].fn == 1

    def test_explicit_function_name(self):
        registry.register_at("thing", name="foo")(1)
        assert registry.namespaces() == [("thing",)]
        assert registry.methods("thing")["foo"].fn == 1

    def test_registration_duplicate(self):
        registry.register_at("thing", name="foo")(1)
        with pytest.raises(ValueError):
            registry.register_at("thing", name="foo")(1)


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

    def test_cascade_delete(self):
        session = get_session(Base)

        @registry.register_at("bar")
        def new_bar():
            return Bar()

        @registry.register_at("baz")
        def new_baz(bar):
            return Baz(bar=bar)

        with ModelFactory(registry, session) as mm:
            bar = mm.bar.new()
            mm.baz.new(bar)

        assert len(session.query(Bar).all()) == 0
        assert len(session.query(Baz).all()) == 0

    def test_cascade_delete_mapping_table(self):
        session = get_session(Base)

        @registry.register_at("bar")
        def new_bar():
            return Bar()

        @registry.register_at("bar2")
        def new_bar2(bar):
            return Bar2(bar=bar)

        with ModelFactory(registry, session) as mm:
            bar = mm.bar.new()
            mm.bar2.new(bar)
            session.delete(bar)

        assert len(session.query(Bar).all()) == 0
        assert len(session.query(Bar2).all()) == 0

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


class TestNamespaceNesting:
    def setup(self):
        registry.clear()

    def test_namespace_nesting(self):
        session = get_session(Base)

        @registry.register_at("name", "space", "nesting", name="new")
        def new_bar():
            return Bar(id=1)

        with ModelFactory(registry, session) as mm:
            bar = mm.name.space.nesting.new()
            assert isinstance(bar, Bar)

    def test_namespace_nesting_at_different_levels(self):
        session = get_session(Base)

        @registry.register_at("name", "space", "nesting", name="new")
        def new_bar():
            return Bar(id=1)

        @registry.register_at("name", "space", name="new")
        def new_foo(bar):
            return Foo(bar=bar)

        with ModelFactory(registry, session) as mm:
            bar = mm.name.space.nesting.new()
            assert isinstance(bar, Bar)

            foo = mm.name.space.new(bar)
            assert isinstance(foo, Foo)

    def test_logical_error_on_namespace_callable(self):
        session = get_session(Base)

        @registry.register_at("name", "space", "nesting", name="new")
        def new_bar():
            return Bar(id=1)

        with ModelFactory(registry, session) as mm:
            with pytest.raises(AttributeError) as e:
                mm.name.space.new()

            assert "Available methods include:" in str(e.value)
            assert "Available nested namespaces include:" in str(e.value)


def test_merge():
    session = get_session(Base)

    @registry.register_at("bar", merge=True)
    def new_bar():
        return Bar(id=1)

    with ModelFactory(registry, session) as mm:
        session.add(Bar(id=1))
        session.commit()

        bar = mm.bar.new()

        session.add(Bar2(bar=bar))
        session.commit()
        assert bar.id == 1
