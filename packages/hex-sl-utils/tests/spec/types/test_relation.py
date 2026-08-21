from hex_sl_utils.spec.types import Relation


def test_relation_target_defaults_to_id() -> None:
    relation = Relation.model_validate(
        {
            "id": "customers",
            "type": "many_to_one",
            "join_sql": "${customer_id} = ${customers.id}",
        }
    )

    assert relation.target == "customers"
