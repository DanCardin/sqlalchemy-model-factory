"""A pytest plugin as a simplified way to use the ModelFactory.

General usage requires the user to define either a `mf_engine` or a `mf_session` fixture.
Once defined, they can have their tests depend on the exposed `mf` fixture, which should
give them access to any factory functions on which they've called `register_at`.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm.session import sessionmaker
from sqlalchemy_model_factory.base import ModelFactory
from sqlalchemy_model_factory.registry import registry, Registry

try:
    import pytest
except ImportError:

    class pytest:  # type:ignore
        """Guard against pytest not being installed.

        The below function will simply act as a normal function if pytest is not installed.
        """

        def fixture(fn):
            return fn


def create_registry_fixture(factory_or_registry):
    if isinstance(factory_or_registry, Registry):
        registry = factory_or_registry
    else:
        registry = factory_or_registry.registry

    def fixture():
        return registry

    return pytest.fixture(fixture)


@pytest.fixture
def mf_registry():
    """Define a default fixture for the general case where the default registry is used."""
    return registry


@pytest.fixture
def mf_engine():
    """Define a default fixture in for the database engine."""
    return create_engine("sqlite:///")


@pytest.fixture
def mf_session(mf_engine):
    """Define a default fixture in for the session, in case the user defines only `mf_engine`."""
    Session = sessionmaker(mf_engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def mf_config():
    """Define a default fixture in for the model factory configuration."""
    return {}


@pytest.fixture
def mf(mf_registry, mf_session, mf_config):
    """Define a fixture for use of the ModelFactory in tests."""
    with ModelFactory(mf_registry, mf_session, options=mf_config) as model_manager:
        yield model_manager
