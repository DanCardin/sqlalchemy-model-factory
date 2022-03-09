import pytest
from sqlalchemy import Column, create_engine, types
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm.session import sessionmaker
from sqlalchemy_model_factory import base
from sqlalchemy_model_factory.declarative import (
    compat,
    declarative,
    DeclarativeMF,
    factory,
)
from sqlalchemy_model_factory.pytest import create_registry_fixture
from sqlalchemy_model_factory.registry import Registry
from tests import get_session

Base = declarative_base()


class Foo(Base):
    __tablename__ = "foo"

    id = Column(types.Integer(), autoincrement=True, primary_key=True)


class Bar(Base):
    __tablename__ = "bar"

    pk = Column(types.Integer(), autoincrement=True, primary_key=True)


class bar:
    @staticmethod
    def new(id: int):
        return Bar(pk=id)


@declarative
class ModelFactory:
    some_attribute = 5

    class foo:
        class nest:
            @staticmethod
            def default(id: int):
                return Foo(id=id)

    bar = bar


mf_registry = create_registry_fixture(ModelFactory)


def test_declarative_base(mf: ModelFactory, mf_session):
    session = get_session(Base, session=mf_session)

    foo = mf.foo.nest.default(5)
    assert foo.id == 5

    bar = mf.bar.new(3)
    assert bar.pk == 3

    foo = session.query(Foo).one()
    assert foo.id == 5

    bar = session.query(Bar).one()
    assert bar.pk == 3


def test_declarative_argument():
    registry = Registry()

    @declarative(registry=registry)
    class ModelFactory:
        @staticmethod
        def default(id: int):
            return Foo(id=id)

    session = get_session(Base)

    with base.ModelFactory(registry, session) as mf:
        foo = mf.default(5)

        foo = session.query(Foo).one()
        assert foo.id == 5


def test_metaclass():
    registry = Registry()

    class ModelFactory(DeclarativeMF, registry=registry):
        @staticmethod
        def default(id: int):
            return Foo(id=id)

    session = get_session(Base)

    with base.ModelFactory(registry, session) as mf:
        foo = mf.default(5)

        foo = session.query(Foo).one()
        assert foo.id == 5


def test_non_staticmethods():
    @declarative
    class ModelFactory:
        def default(self, id: int):
            return Foo(id=id)

    session = get_session(Base)

    with base.ModelFactory(ModelFactory.registry, session) as mf:
        foo = mf.default(5)

        foo = session.query(Foo).one()
        assert foo.id == 5


def test_callable_namespace():
    @declarative
    class ModelFactory:
        class ex:
            def __call__(self, id: int):
                return Foo(id=id * -1)

            def default(self, id: int):
                return Foo(id=id)

    session = get_session(Base)

    with base.ModelFactory(ModelFactory.registry, session) as mf:
        mf.ex(5)
        foos = session.query(Foo.id).all()
        assert foos == [(-5,)]

        mf.ex.default(5)

        foos = session.query(Foo.id).all()
        assert foos == [(-5,), (5,)]


# Mixed-dynamic and declarative setup.
mixed_registry = Registry()


@mixed_registry.register_at("ex", name="new")
def new():
    return Foo(id=6)


@declarative(registry=mixed_registry)
class MixedModelFactory(compat):
    class ex(compat):
        @staticmethod
        def default(id: int):
            return Foo(id=id)


@pytest.fixture
def mixed_mf_session(mf_engine):
    mf_engine = create_engine("sqlite:///")
    Base.metadata.create_all(mf_engine)
    Session = sessionmaker(mf_engine)
    return Session()


@pytest.fixture
def mixed_mf(mixed_mf_session):
    with base.ModelFactory(mixed_registry, mixed_mf_session) as model_manager:
        yield model_manager


def test_mixed_dynamic_and_declarative(mixed_mf: MixedModelFactory, mixed_mf_session):
    session = mixed_mf_session

    mixed_mf.ex.new()
    foos = session.query(Foo.id).all()
    assert foos == [(6,)]

    mixed_mf.ex.default(5)

    foos = session.query(Foo.id).all()
    assert foos == [(5,), (6,)]


factory_fn_registry = Registry()


@declarative(registry=factory_fn_registry)
class FactoryFnMF:
    @staticmethod
    @factory(merge=True)
    def default(*, id: int) -> Foo:
        return Foo(id=id)

    class foo:
        @staticmethod
        @factory()
        def bar(*, pk: int) -> Bar:
            return Bar(pk=pk)


@pytest.fixture
def factory_mf(mixed_mf_session):
    with base.ModelFactory(factory_fn_registry, mixed_mf_session) as model_manager:
        yield model_manager


def test_Factory(factory_mf: FactoryFnMF, mixed_mf_session):
    foo = factory_mf.default(id=5)

    # Make a 2nd one, it should merge instead of erroring.
    foo = factory_mf.default(id=5)

    bar = factory_mf.foo.bar(pk=6)

    the_foo = mixed_mf_session.query(Foo).one()
    assert foo.id == 5
    assert foo is the_foo

    the_bar = mixed_mf_session.query(Bar).one()
    assert bar.pk == 6
    assert bar is the_bar
