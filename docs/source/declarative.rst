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
