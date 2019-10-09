import pytest
from sqlalchemy import Column, types
from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy_model_factory.registry import Registry
from tests import get_session

Base = declarative_base()


class Foo(Base):
    __tablename__ = "foo"

    id = Column(types.Integer(), autoincrement=True, primary_key=True)


registry = Registry()


@registry.register_at("foo")
def new_foo():
    return Foo()


@pytest.fixture
def mf_registry():
    return registry


@pytest.fixture
def mf_session():
    return get_session(Base)


def test_mf_fixture(mf):
    foo = mf.foo.new()
    assert foo.id == 1
