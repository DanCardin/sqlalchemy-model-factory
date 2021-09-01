import pytest
from sqlalchemy_model_factory.utils import fluent


class Test_fluent:
    def test_no_args(self):
        def foo():
            return 5

        result = fluent(foo).bind()
        assert result == 5

    def test_bind_error(self):
        def foo(bind):
            pass

        with pytest.raises(ValueError):
            fluent(foo)

    def test_duplicate_options_unavailable(self):
        def foo(bar, baz, bay):
            pass

        with pytest.raises(AttributeError):
            fluent(foo).bar(1).bar(4)

    def test_call_before_result(self):
        def foo(bar):
            return bar

        result = fluent(foo).bar(4).bind(call_before=lambda _, __: ((5,), {}))
        assert result == 5

    def test_call_before_no_result(self, capsys):
        def foo(bar):
            return bar

        result = fluent(foo).bar(4).bind(call_before=print)
        assert result == 4
        assert capsys.readouterr().out == "[4] {}\n"

    def test_call_after_result(self):
        def foo(bar):
            return bar

        result = fluent(foo).bar(4).bind(call_after=lambda a: a + 1)
        assert result == 5

    def test_call_after_no_result(self, capsys):
        def foo(bar):
            return bar

        result = fluent(foo).bar(4).bind(call_after=print)
        assert result == 4
        assert capsys.readouterr().out == "4\n"
