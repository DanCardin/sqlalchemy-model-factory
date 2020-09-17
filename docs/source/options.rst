Options
=======

Factory-level Options
---------------------

Options can be supplied to :code:`register_at` at the factory level to alter
the default behavior when calling a factory.

Factory-level options include:

* commit: :code:`True`/:code:`False` (default :code:`True`)

  Whether the given factory should commit the models it produces.

* merge: :code:`True`/:code:`False` (default :code:`False`)

  Whether the given factory should :code:`Session.add` the models
  it produces, or :code:`Session.merge` them.

  This option can be useful for obtaining a reference to some model you
  **know** is already in the database, but you dont currently have a handle on.

For example:

.. code-block:: python

   @register_at("widget", name="default", merge=True)
   def default_widget():
       return Widget()


Call-level Options
------------------

All options available at the factory-level can also be provided at the call-site
when calling the factories, although their arguments are postfixed with a
trailing :code:`_` to avoid colliding with normal factory arguments.

.. code-block:: python

   def test_widget(mf):
       widget = mf.widget.default(merge_=True, commit_=True)
