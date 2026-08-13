from hex_sl_utils.exception import ColumnNotFoundError


class TestFindCaseInsensitiveMatches:
    def test_case_insensitive_match(self):
        assert ColumnNotFoundError.find_case_insensitive_matches(
            "Origin", ["origin", "dest"]
        ) == ["origin"]

    def test_no_match(self):
        assert (
            ColumnNotFoundError.find_case_insensitive_matches("xyz", ["origin", "dest"])
            == []
        )

    def test_multiple_matches(self):
        assert ColumnNotFoundError.find_case_insensitive_matches(
            "foo", ["FOO", "Foo", "bar"]
        ) == [
            "FOO",
            "Foo",
        ]

    def test_empty_available(self):
        assert ColumnNotFoundError.find_case_insensitive_matches("foo", []) == []
