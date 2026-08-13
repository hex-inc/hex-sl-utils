from inline_snapshot import snapshot

from hex_sl_utils.spec.load import load_project

from .utils import get_test_project_dir, make_yml


def test_load_pizza_bytes() -> None:
    loaded = load_project(
        project_dir=get_test_project_dir("pizza_bytes"),
        project_name="pizza_bytes",
        dialect_name="duckdb",
    )
    assert loaded.problems == []
    assert len(loaded.project.models) == 4
    assert make_yml(loaded.project) == snapshot(
        """\
name: pizza_bytes
dialect: duckdb
resources:
- id: customers
  type: model
  base_sql_table: pizza_bytes.users
  dimensions:
  - id: id
    type: string
    expr_sql: id
    unique: true
    name: Id
    description: ''
    visibility: internal
  - id: name
    type: string
    expr_sql: name
    unique: false
    name: Name
    description: ''
    visibility: public
  - id: address
    type: string
    expr_sql: address
    unique: false
    name: Address
    description: ''
    visibility: public
  - id: phone_number
    type: string
    expr_sql: phone_number
    unique: false
    name: Phone number
    description: ''
    visibility: public
  measures: []
  relations: []
  name: Valued Customers
  description: Dimensional table of customer information.
  visibility: public
- id: products
  type: model
  base_sql_table: pizza_bytes.products
  dimensions:
  - id: id
    type: string
    expr_sql: id
    unique: true
    name: Id
    description: ''
    visibility: internal
  - id: name
    type: string
    expr_sql: name
    unique: false
    name: Name
    description: ''
    visibility: public
  - id: pizza_size
    type: string
    expr_sql: pizza_size
    unique: false
    name: Pizza size
    description: ''
    visibility: public
  - id: pizza_shape
    type: string
    expr_sql: pizza_shape
    unique: false
    name: Pizza shape
    description: ''
    visibility: public
  - id: pizza_type
    type: string
    expr_sql: pizza_type
    unique: false
    name: Pizza type
    description: ''
    visibility: public
  - id: price
    type: number
    expr_sql: price
    unique: false
    name: Price
    description: ''
    visibility: public
  measures: []
  relations: []
  name: Products
  description: Dimensional table of product information.
  visibility: public
- id: orders
  type: model
  base_sql_table: pizza_bytes.orders
  dimensions:
  - id: timestamp
    type: timestamp_naive
    expr_sql: timestamp
    unique: false
    name: Timestamp
    description: ''
    visibility: public
  - id: payment_method
    type: string
    expr_sql: payment_method
    unique: false
    name: Payment method
    description: ''
    visibility: public
  - id: is_delivery
    type: boolean
    expr_sql: delivery = 'Yes'
    unique: false
    name: Is delivery
    description: ''
    visibility: public
  - id: type
    type: string
    expr_sql: type
    unique: false
    name: Type
    description: ''
    visibility: public
  - id: order_value
    type: number
    expr_sql: order_value
    unique: false
    name: Order value
    description: ''
    visibility: public
  - id: discount_code
    type: string
    expr_sql: discount_code
    unique: false
    name: Discount code
    description: ''
    visibility: public
  - id: feedback_rating
    type: number
    expr_sql: feedback_rating
    unique: false
    name: Feedback rating
    description: ''
    visibility: public
  - id: delivery_time
    type: number
    expr_sql: delivery_time
    unique: false
    name: Delivery time
    description: ''
    visibility: public
  - id: preparation_time
    type: number
    expr_sql: preparation_time
    unique: false
    name: Preparation time
    description: ''
    visibility: public
  - id: special_request
    type: string
    expr_sql: special_request
    unique: false
    name: Special request
    description: ''
    visibility: public
  - id: referral_source
    type: string
    expr_sql: referral_source
    unique: false
    name: Referral source
    description: ''
    visibility: public
  - id: id
    type: number
    expr_sql: id
    unique: true
    name: Id
    description: ''
    visibility: internal
  - id: customer_id
    type: string
    expr_sql: customer_id
    unique: false
    name: Customer id
    description: ''
    visibility: internal
  - id: cook_id
    type: string
    expr_sql: cook_id
    unique: false
    name: Cook id
    description: ''
    visibility: internal
  - id: location_id
    type: string
    expr_sql: location_id
    unique: false
    name: Location id
    description: ''
    visibility: internal
  measures:
  - id: count
    func: count
    type: number
    filters: []
    name: Number of orders
    description: ''
    visibility: public
  - id: total_order_value
    func: sum
    of: order_value
    type: number
    filters: []
    name: Total order value
    description: ''
    visibility: public
  relations:
  - id: customers
    target: customers
    type: many_to_one
    join_sql: ${customer_id} = ${customers.id}
    visibility: public
  - id: sales
    target: sales
    type: one_to_many
    join_sql: ${id} = ${sales.order_id}
    visibility: public
  name: Orders
  description: Fact table of order information.
  visibility: public
- id: sales
  type: model
  base_sql_table: pizza_bytes.sales
  dimensions:
  - id: value
    type: number
    expr_sql: item_price * quantity
    unique: false
    name: Value
    description: The total price paid for the sale.
    visibility: public
  - id: item_price
    type: number
    expr_sql: item_price
    unique: false
    name: Item price
    description: ''
    visibility: public
  - id: quantity
    type: number
    expr_sql: quantity
    unique: false
    name: Quantity
    description: ''
    visibility: public
  - id: timestamp
    type: timestamp_tz
    expr_sql: timestamp
    unique: false
    name: Timestamp
    description: ''
    visibility: public
  - id: id
    type: string
    expr_sql: id
    unique: true
    name: Id
    description: ''
    visibility: internal
  - id: item_id
    type: number
    expr_sql: item_id
    unique: false
    name: Item id
    description: ''
    visibility: internal
  - id: customer_id
    type: string
    expr_sql: customer_id
    unique: false
    name: Customer id
    description: ''
    visibility: internal
  - id: order_id
    type: number
    expr_sql: order_id
    unique: false
    name: Order id
    description: ''
    visibility: internal
  - id: product_id
    type: string
    expr_sql: product_id
    unique: false
    name: Product id
    description: ''
    visibility: internal
  measures:
  - id: revenue
    func: sum
    of: value
    type: number
    filters: []
    name: Revenue
    description: "The total sales of pizza.\\nsynonyms: sales, top line revenue\\n"
    visibility: public
  - id: number_of_customers
    func: count_distinct
    of: customer_id
    type: number
    filters: []
    name: Number of customers
    description: ''
    visibility: public
  - id: number_of_orders
    func: count_distinct
    of: order_id
    type: number
    filters: []
    name: Number of orders
    description: ''
    visibility: public
  - id: revenue_per_customer
    func_calc: revenue / number_of_customers
    type: number
    filters: []
    name: Revenue per customer
    description: ''
    visibility: public
  - id: revenue_per_order
    func_calc: revenue / number_of_orders
    type: number
    filters: []
    name: Revenue per order
    description: ''
    visibility: public
  - id: avg_unit_price
    func_calc: SUM(value) / SUM(quantity)
    type: number
    filters: []
    name: Avg unit price
    description: ''
    visibility: public
  - id: orders_per_customer
    func_calc: number_of_orders / number_of_customers
    type: number
    filters: []
    name: Orders per customer
    description: ''
    visibility: public
  - id: revenue_adjusted_for_delivery_cost
    func: sum
    of:
      type: number
      expr_sql: ${value} * IF(${orders.is_delivery}, 0.8, 1)
    type: number
    filters: []
    name: Revenue adjusted for delivery cost
    description: ''
    visibility: public
  - id: revenue_from_custom_delivery_pizza
    func: sum
    of: value
    type: number
    filters:
    - orders.is_delivery
    - type: boolean
      expr_sql: ${products.pizza_type} = 'Custom'
    name: Revenue from custom delivery pizza
    description: ''
    visibility: public
  relations:
  - id: customers
    target: customers
    type: many_to_one
    join_sql: ${customer_id} = ${customers.id}
    visibility: public
  - id: orders
    target: orders
    type: many_to_one
    join_sql: ${order_id} = ${orders.id}
    visibility: public
  - id: products
    target: products
    type: many_to_one
    join_sql: ${product_id} = ${products.id}
    visibility: public
  name: Sales
  description: Fact table of sales information.
  visibility: public
"""
    )
