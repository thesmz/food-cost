"""
Configuration for Purchasing Evaluation System
Defines vendor-ingredient-dish mappings
"""

# Vendor configuration
# Maps vendor names to their products and related dishes
VENDOR_CONFIG = {
    'hirayama': {
        'names': ['ミートショップひら山', 'Meat Shop Hirayama', 'Hirayama'],
        'products': [
            {
                'name': '和牛ヒレ',
                'name_en': 'Wagyu Tenderloin',
                'unit': 'kg',
                'patterns': ['和牛ヒレ', '和牛モレ', '和生ヒレ', '和邊ヒレ', 'wagyu', 'tenderloin'],
            }
        ]
    },
    'french_fnb': {
        'names': ['フレンチ・エフ・アンド・ビー', 'French F&B Japan', 'French FnB'],
        'products': [
            {
                'name': 'KAVIARI キャビア',
                'name_en': 'Caviar',
                'unit': 'pc (100g)',
                'patterns': ['KAVIARI', 'キャビア', 'キャヴィア', 'caviar', 'クリスタル'],
            },
            {
                'name': 'パレット バター',
                'name_en': 'Butter',
                'unit': 'pc (20g)',
                'patterns': ['パレット', 'ﾊﾟﾚｯﾄ', 'バラット', 'ブール', 'butter'],
            },
            {
                'name': 'シャンパン ヴィネガー',
                'name_en': 'Champagne Vinegar',
                'unit': 'bottle (500ml)',
                'patterns': ['シャンパン', 'ヴィネガー', 'vinegar', 'champagne'],
            },
            {
                'name': 'ジロール',
                'name_en': 'Girolles Mushroom',
                'unit': 'kg',
                'patterns': ['ジロール', 'girolles', 'mushroom'],
            }
        ]
    }
}

# Dish to ingredient mapping
# Maps menu items to their primary ingredients and expected usage per serving
DISH_INGREDIENT_MAP = {
    'Beef Tenderloin': {
        'ingredient': '和牛ヒレ',
        'vendor': 'hirayama',
        'usage_per_serving': 180,  # grams
        'unit': 'g',
        'patterns': ['beef tenderloin', 'ビーフ', 'テンダーロイン'],
    },
    'Egg Toast Caviar': {
        'ingredient': 'KAVIARI キャビア',
        'vendor': 'french_fnb',
        'usage_per_serving': 15,  # grams (per serving)
        'unit': 'g',
        'patterns': ['egg toast caviar', 'キャビア', 'エッグトースト'],
    }
}

# Default target ratios for analysis
DEFAULT_TARGETS = {
    'beef': {
        'waste_ratio_target': 15,  # Maximum acceptable waste %
        'cost_ratio_target': 35,   # Target food cost %
    },
    'caviar': {
        'waste_ratio_target': 10,  # Maximum acceptable waste %
        'cost_ratio_target': 25,   # Target food cost %
    }
}

# OCR settings
OCR_CONFIG = {
    'languages': 'jpn+eng',
    'dpi': 300,
}
