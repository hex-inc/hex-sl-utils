from hex_sl_common.exceptions import SemanticItemNotFoundError


class TestFindCaseInsensitiveMatches:
    def test_case_insensitive_match(self):
        assert SemanticItemNotFoundError.find_case_insensitive_matches(
            "Origin", ["origin", "dest"]
        ) == ["origin"]

    def test_no_match(self):
        assert (
            SemanticItemNotFoundError.find_case_insensitive_matches(
                "xyz", ["origin", "dest"]
            )
            == []
        )

    def test_multiple_matches(self):
        assert SemanticItemNotFoundError.find_case_insensitive_matches(
            "foo", ["FOO", "Foo", "bar"]
        ) == [
            "FOO",
            "Foo",
        ]

    def test_empty_available(self):
        assert SemanticItemNotFoundError.find_case_insensitive_matches("foo", []) == []


class TestSemanticItemNotFoundError:
    def test_error_kwargs_with_matches(self):
        exc = SemanticItemNotFoundError(
            "dimension Origin not found in dataset flights",
            item_name="Origin",
            dataset="flights",
            item_type="dimension",
            case_insensitive_matches=["origin"],
        )
        assert exc.error_kwargs() == {
            "item_name": "Origin",
            "dataset": "flights",
            "item_type": "dimension",
            "case_insensitive_matches": ["origin"],
        }

    def test_empty_matches_preserved(self):
        exc = SemanticItemNotFoundError(
            "dimension foo not found in dataset bar",
            item_name="foo",
            dataset="bar",
            item_type="dimension",
            case_insensitive_matches=[],
        )
        assert exc.error_kwargs() == {
            "item_name": "foo",
            "dataset": "bar",
            "item_type": "dimension",
            "case_insensitive_matches": [],
        }
