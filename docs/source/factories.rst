Factories
=========

Basic
-----

So the most basic factories that you can write are just functions which return models.

.. code-block:: python

    from sqlalchemy_model_factory import register_at

    @register_at('foo')
    def new_foo():
        return Foo()

    def test_foo(mf):
        foo = mf.foo.new()
        assert isinstance(foo, Foo)


Nested
~~~~~~

Note, you can also create nested models through relationships and whatnot; and that will all work
normally.

.. code-block:: python

    from sqlalchemy_model_factory import register_at

    class Foo(Base):
        ...

        bar = relationship('Bar')

    class Bar(Base):
        ...

        baz = relationship('Baz')

    @register_at('foo')
    def new_foo():
        ...


General Use Functions
---------------------

In some cases, you'll have a a function already handy that returns the equivalent signature
of a model (or you just **want** a function that returns the signature).

In this case, your function will act as the originally defined function when called normally,
however when invoked in the context of the :code:`ModelFactory`, it returns the specified model
instance.

.. code-block:: python

    from sqlalchemy_model_factory import for_model, register_at

    @register_at('foo')
    @for_model(Foo)
    def new_foo():
        return {'id': 1, 'name': 'bar'}

    def test_foo(mf):
        foo = mf.foo.new()
        assert foo.id == 1
        assert foo.name == 'bar'

        raw_foo = new_foo()
        assert raw_foo == {'id': 1, 'name': 'bar'}


Sources of Uniqueness
---------------------

Suppose you've got a column defined with a constraint, like
`name = Column(types.Integer(), unique=True)`.

Suddenly you'll need to parametrize your factory to accept a :code:`name` param. However if you
**actually** don't care about the specific name values, you have a few options.

Autoincrement
~~~~~~~~~~~~~

Automatically incrementing number values is one option. Your factory will be automatically
supplied with an :code:`autoincrement` parameter, known to not collide with previously
generated values.

.. code-block:: python

    from sqlalchemy_model_factory import autoincrement, register_at

    @register_at('foo')
    @autoincrement
    def new_foo(autoincrement=1):
        return Foo(name=f'name{autoincrement}')

    def test_foo(mf):
        assert mf.foo.new().name == 'name1'
        assert mf.foo.new().name == 'name2'
        assert mf.foo.new().name == 'name3'


Fluency
-------

You've been working along and writing factories and you finally find yourself in a situation like
this.

.. code-block:: python

    @register_at('foo')
    @autoincrement
    def new_foo(name='name', height=2, width=3, depth=3, category='foo', autoincrement=1):
        ...

And in the event your test requires a number of identical parameters across multiple calls, you
might end up with test code that looks like.

.. code-block:: python

    def test_foo(mf):
        width_4 = mf.foo.new(height=3, category='bar', width=4)
        width_5 = mf.foo.new(height=3, category='bar', width=5)
        width_6 = mf.foo.new(height=3, category='bar', width=6)
        width_7 = mf.foo.new(height=3, category='bar', width=7)
        ...

The above (as a dirt simple example, that might be easily solved in different ways) has got **most**
of its information duplicated unnecessarily.

The "fluent" decorator
~~~~~~~~~~~~~~~~~~~~~~

A simple solution to this general problem category is the :code:`fluent` decorator. Which adapts a
given callable to be able to be called in a fluent style.

.. code-block:: python

    def test_foo(mf):
        bar_type_foo = mf.foo.new(3).category('bar')

        width_4 = bar_type_foo.width(4).bind()
        width_5 = bar_type_foo.width(5).bind()
        width_6 = bar_type_foo.width(6).bind()
        width_7 = bar_type_foo.width(7).bind()

Now in this particular case, you could have just done a for-loop over the original set of calls,
or maybe :code:`functools.partial` could have sufficed, but the fluent pattern is more generally
useful than just in cases like this.

Also from the callee's perspective, there's not necessarily any requirement that all the args have
their parameter names supplied, so you might end up reading :code:`foo.new('a', 3, 4, 5, 'ro')`,
which is arguably far less readable.

To note, the :code:`bind` call at the end of each expression above is necessary to let the fluent
calls know that its done being called (because as you might notice, we didn't call all the available
methods we could have called). But this also serves as a convenient point at which to add custom
behaviors. (for example you *could* supply `.bind(call_after=print)` to have it print out the final
result of the function; see the api portion of the docs for the full set of options.)

Class-style factories
~~~~~~~~~~~~~~~~~~~~~

From the perspective of the model factory, all factory "functions" are just callables, so you can
always manually mimic something like the above :code:`fluent` decorator in a class so that you can
implement your own custom behavior for each option.

.. code-block:: python

    @register_at('foo')
    class NewFoo:
        def __init__(self, **kwargs):
            self.kwargs

        def name(self, name):
            self.__class__(**self.kwargs, name=name)

        def width(self, width):
            self.__class__(**self.kwargs, width=width)

        def bind(self):
            return Foo(**self.kwargs)


Albeit, with the above, very naive implementation, your test code would end up looking like

.. code-block:: python

    def test_foo(mf):
        bar_foo = mf.foo.new().name('bar')
        width_4 = bar_fo.width(4).bind()
        width_5 = bar_fo.width(5).bind()
