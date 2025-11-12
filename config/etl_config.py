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
    }
}