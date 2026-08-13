from pydantic import BaseModel

from hex_sl.datatype import DataType, datatype_to_sqlglot
from hex_sl._vendor.sqlglot import exp


class DataTypeModel(BaseModel):
    data_type: DataType


def test_sqlglot_conversion():
    # Convert SimpleDataType to sqlglot DataType
    data_type_instance = DataType.NUMBER
    sqlglot_data_type = datatype_to_sqlglot(data_type_instance)
    assert isinstance(sqlglot_data_type, exp.DataType)
    assert sqlglot_data_type.this == exp.DataType.Type.DOUBLE


def test_sqlglot_conversion_from_json():
    # Convert SimpleDataType from JSON to sqlglot DataType
    json_data = '{"data_type": "number"}'
    model_instance = DataTypeModel.model_validate_json(json_data)
    sqlglot_data_type = datatype_to_sqlglot(model_instance.data_type)
    assert isinstance(sqlglot_data_type, exp.DataType)
    assert sqlglot_data_type.this == exp.DataType.Type.DOUBLE


def test_all_simple_data_types_to_sqlglot():
    for data_type in DataType:
        model_instance = DataTypeModel(data_type=data_type)
        sqlglot_data_type = datatype_to_sqlglot(model_instance.data_type)
        assert isinstance(sqlglot_data_type, exp.DataType)
