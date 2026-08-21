from typing_extensions import assert_type

from hex_sl_utils.spec.types import Relation, RelationType


def test_relation_without_optional_fields() -> None:
    # should not fail pyright type checking
    relation = Relation(
        id="customers",
        type=RelationType.MANY_TO_ONE,
        join_sql="${customer_id} = ${customers.id}",
    )
    assert_type(relation, Relation)


def test_relation_target_defaults_to_id() -> None:
    relation = Relation.model_validate(
        {
            "id": "customers",
            "type": "many_to_one",
            "join_sql": "${customer_id} = ${customers.id}",
        }
    )

    assert relation.target == "customers"
