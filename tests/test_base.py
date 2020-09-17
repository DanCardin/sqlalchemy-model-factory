import pytest

from sqlalchemy_model_factory.base import Namespace


class TestNamespace:
    def test_empty_namespace(self):
        n = Namespace(None)
        with pytest.raises(AttributeError) as e:
            n.foo()

        assert "no attribute 'foo'" in str(e.value)
        assert "methods include: N/A" in str(e.value)

    def test_expose_available_methods_in_error(self):
        n = Namespace(None, foo=None, bar=None)
        with pytest.raises(AttributeError) as e:
            n.wat()

        assert "no attribute 'wat'" in str(e.value)
        assert "methods include: foo, bar" in str(e.value)
