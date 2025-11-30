REPORT_CONFIGS = {
    'goods_movement' : {
        'columns' : {
            'SHOP_SKU' : {'type': 'str', 'max_length': 10, 'nullable': False, 'field_name': 'shop_sku'},
            'SHIPMENTS_INCOME' : {'type': 'int', 'default': 0, 'field_name': 'shipments_income'},
            'RETURNS_INCOME' : {'type': 'int', 'default': 0, 'field_name': 'returns_income'},
            'INVENTORY_SURPLUS' : {'type': 'int', 'default': 0, 'field_name': 'inventory_surplus'},
            'ORDERS_OUTCOME' : {'type': 'int', 'default': 0, 'field_name': 'orders_outcome'},
            'WAREHOUSE_WITHDRAWAL' : {'type': 'int', 'default': 0, 'field_name': 'warehouse_withdrawal'},
            'RECYCLING' : {'type': 'int', 'default': 0, 'field_name': 'recycling'},
            'INVENTORY_SHORTAGE' : {'type': 'int', 'default': 0, 'field_name': 'inventory_shortage'},
            'WAREHOUSE_NAME' : {'type': 'str', 'max_length': 255, 'nullable': True, 'field_name': 'warehouse'},
        },
        'model' : 'GoodsMovement'
    },
    'sales_analytics' : {
        'columns' : {
            'DAY' : {'type': 'date', 'nullable': False, 'field_name': 'report_date'},
            'OFFER_ID' : {'type': 'str', 'max_length': 10, 'nullable': False, 'field_name': 'shop_sku'},
            'SHOWS' : {'type': 'int', 'default': 0, 'field_name': 'shows'},
            'TO_CART' : {'type': 'int', 'default': 0, 'field_name': 'to_cart'},
            'ORDER_ITEMS' : {'type': 'int', 'default': 0, 'field_name': 'order_items'},
            'ORDER_ITEMS_TOTAL_AMOUNT' : {'type': 'int', 'default': 0, 'field_name': 'order_items_total_amount'},
            'ORDER_ITEMS_SHARE' : {'type': 'Decimal', 'default': 0, 'field_name': 'order_items_share'},
            'ORDER_ITEMS_DELIVERED_COUNT' : {'type': 'int', 'default': 0, 'field_name': 'order_items_delivered_count'},
            'ORDER_ITEMS_DELIVERED_TOTAL_AMOUNT' : {'type': 'int', 'default': 0, 'field_name': 'order_items_delivered_total_amount'},

        },
        'model' : 'Sales'
    }
}