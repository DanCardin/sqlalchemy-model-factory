Testing
=======

A (or maybe **the**) primary usecase for this package is is in writing test tests
concisely, ergonmically, and readably.

To that end, we integrate with the testing framework in order to provide good UX in your
tests.

Pytest
------

We provide default implementations of a couple of pytest fixtures: :code:`mf_engine`,
:code:`mf_session`. However this assumes you're okay running your code as though it's
executed in SQLite, and with default session parameters.

If your system will work under those conditions, great! Simply go on and use the `mf` fixture
which gives you a handle on a :code:`ModelFactory`

.. code-block:: python

    from sqlalchemy_model_factory import registry

    @registry.register_at('foo')
    def new_foo():
        return Foo()

    def test_foo(mf):
        foo = mf.foo.new()
        assert isinstance(foo, Foo)


If, however, you make use of feature not available in SQLite, you may need a handle on a real
database engine. Supposing you've got a postgres database available at :code:`db:5432`, you can
put the following into your :code:`tests/conftest.py`.

.. code-block:: python

    import pytest
    from sqlalchemy import create_engine

    @pytest.fixture
    def mf_engine():
        return create_engine('psycopg2+postgresql://db:5432')

    # now the `mf` fixture should work

Furthermore, if your application works in a context where you assume your :code:`session` has
particular options set, you can similarly plug in your own session.

.. code-block:: python

    import pytest
    from sqlalchemy.orm.session import sessionmaker

    @pytest.fixture
    def mf_session(mf_engine):
        Session = sessionmaker()  # Set your options
        return Session(bind=engine)

    # now the `mf` fixture should work
