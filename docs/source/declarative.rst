Declarative API
===============
There are a few benefits to declaratively specifying the factory function tree:

- The vanilla ``@register_at`` decorator is dynamic and string based, which
  leaves no direct import or path to trace back to the implementing function
  from a ``ModelFactory`` instance.
- There is, perhaps, an alternative declarative implementation which ensures
  the yielded ``ModelFactory`` literally **is** the heirarchy specified.

  - As is, if you're in a context in which you can type annotate the model
    factory, then this enables typical LSP features like "Go to Definition".

    In the most common cases, such as with ``pytest``, you'll be being handed
    an untyped ``mf`` (:ref:`model_factory`) fixture instance. Here, you can
    type annotate the argument as being your ``@declarative`` ly decorated
    class.


.. code-block:: python

   # some_module.py
   class other:
       def new():
           ...

   # factory.py
   from some_module import other

   @declarative
   class ModelFactory:
       other = other

       class namespace:
           def example():
               ...

   # tests.py
   from sqlalchemy_model_factory.pytest import create_registry_fixture
   from factory import ModelFactory

   mf_registry = create_registry_fixture(ModelFactory)

   # `mf` being a sqlalchemy_model_factory-provided fixture.
   def test_factory(mf: ModelFactory):
      ...

Alternatively, a registry can be provided to the decorator directly,
ou have one pre-constructed.

.. code-block:: python

   registry = Registry()
   
   @declarative(registry=registry)
   class ModelFactory:
       def fn():
           ...

.. note::

   interior classes to the decorator, including both the root class, as
   well as any nested class or attributes which are raw types, will be
   instantiated. This is notable, primarily in the event that an `__init__`
   is defined on the class for whatever reason. Each class will be instantiated
   once without arguments.


Conversion from ``@register_at``
--------------------------------
If you have an existing body of model-factory functions registered using the
``@register_at`` pattern, you can incrementally adopt (and therefore incrementally
get viable type hinting support) the declarative api.


If you are importing ``from sqlalchemy_model_factory import register_at``, today,
you can import ``from sqlalchemy_model_factory import registry``, and send that
into the ``@declarative`` decorator:

.. code-block:: python

   from sqlalchemy_model_factory import registry

   @declarative(registry=registry)
   class ModelFactory:
       def example():
           ...

Alternatively, you can switch to manually constructing your own ``Registry``,
though you will need to change your ``@register_at`` calls to use it!

.. code-block:: python

   from sqlalchemy_model_factory import Registry, declarative

   registry = Registry()

   @register_at("path", name="new")
   def new_path():
       ...

   @declarative(registry=registry)
   class Base:
       def example():
           ...

Then once you make use of the annotation, say in some test:

.. code-block:: python

   def test_path(mf: Base):
       mf.example()

you should get go-to-definition and hinting support for the declaratively specified
methods **only**.

.. note::

   You might see mypy type errors like ``Type[...] has no attribute "..."``
   for ``@register_at``. You can either ignore these, or else apply the
   ``compat`` as a superclass to your declarative:

   .. code-block:: python

      from sqlalchemy_model_factory import declarative

      @declarative.declarative
      class Factory(declarative.compat):
          ...
