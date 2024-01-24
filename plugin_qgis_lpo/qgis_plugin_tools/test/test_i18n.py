from ..tools.i18n import tr


def test_tr_formatting():
    string = tr(
        "These are args {} {} and these are kwargs {foo} {bar}", 1, 2, foo=3, bar=4
    )
    assert string == "These are args 1 2 and these are kwargs 3 4"
