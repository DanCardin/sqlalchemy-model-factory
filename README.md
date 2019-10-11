[![Actions Status](https://github.com/dancardin/sqlalchemy-model-factory/workflows/build/badge.svg)](https://github.com/dancardin/sqlalchemy-model-factory/actions) [![codecov](https://codecov.io/gh/DanCardin/sqlalchemy-model-factory/branch/master/graph/badge.svg)](https://codecov.io/gh/DanCardin/sqlalchemy-model-factory) [![Documentation Status](https://readthedocs.org/projects/sqlalchemy-model-factory/badge/?version=latest)](https://sqlalchemy-model-factory.readthedocs.io/en/latest/?badge=latest)

sqlalchemy-model-factory aims to make it easy to write factory functions for sqlalchemy
models, particularly for use in testing.

It should make it easy to define as many factories as you might want, with as little
boilerplate as possible, while remaining as unopinionated as possible about the behavior
going in your factories.

Installation
------------

```python
pip install sqlalchemy-model-factory
```

Usage
-----

Suppose you've defined a `Widget` model, and for example you want to test some API code
that queries for `Widget` instances. Couple of factory functions might look like so:

```python
# tests/test_example_which_uses_pytest
from sqlalchemy_model_factory import autoincrement, register_at
from . import models

@register_at('widget')
def new_widget(name, weight, color, size, **etc):
    """My goal is to allow you to specify *all* the options a widget might require.
    """
    return Widget(name, weight, color, size, **etc)

@register_at('widget', name='default')
@autoincrement
def new_default_widget(autoincrement=1):
    """My goal is to give you a widget with as little input as possible.
    """
    # I'm gonna call the other factory function...because i can!
    return new_widget(
        f'default_name{autoincrement}',
        weight=autoincrement,
        color='rgb({0}, {0}, {0})'.format(autoincrement),
        size=autoincrement,
    )
```

What this does, is register those functions to the registry of factory functions, within
the "widget" namespace, at the `name` (defaults to `new`) location in the namespace.

So when I go to write a test, all I need to do is accept the `mf` fixture (and lets say
a `session` db connection fixture to make assertions against) and I can call all the
factories that have been registered.

```python
def test_example_model(mf, session):
    widget1 = mf.widget.new('name', 1, 'rgb(0, 0, 0)', 1)
    widget2 = mf.widget.default()
    widget3 = mf.widget.default()
    widget4 = mf.widget.default()

    widgets = session.query(Widget).all()
    assert len(widgets) == 4
    assert widgets[0].name == 'name'
    assert widgets[1].id == widget2.id
    assert widgets[2].name == widget3.name
    assert widgets[3].color == 'rgb(3, 3, 3)'
```

In a simple toy example, where you don't gain much on the calls themselves the benefits
are primarily:
* The instances are automatically put into the database and cleaned up after the test.
* You can make assertions without hardcoding the values, because you get back a handle on the object.

But as the graph of models required to set up a particular scenario grows:
* You can define factories as complex as you want
  * They can create related objects and assign them to relationships
  * They can be given sources of randomness or uniqueness to not violate constraints
  * They can compose with eachother (when called normally, they're the same as the original function).
