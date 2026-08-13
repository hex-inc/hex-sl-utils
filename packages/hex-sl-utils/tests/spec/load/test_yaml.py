from hex_sl_utils.spec.load.yaml import ryml_parse


def test_empty_unquoted_scalar_is_null():
    assert ryml_parse('unquoted:\nquoted: ""\n') == {
        "unquoted": None,
        "quoted": "",
    }
