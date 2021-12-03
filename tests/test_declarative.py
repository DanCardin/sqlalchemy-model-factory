from sqlalchemy import Column, types
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy_model_factory import base
from sqlalchemy_model_factory.declarative import declarative, DeclarativeMF
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
