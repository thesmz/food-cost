"""
Reference Data for October 2025
Extracted manually from invoices (verified by vision)

This file contains accurate baseline data that can be used to validate
OCR extraction or as manual input when OCR fails.
"""

# ===== BEEF INVOICE - Meat Shop Hirayama =====
# Invoice: 〇202511_-_買掛金計上済Meat_shop_Hirayama.PDF
# Period: October 2025
# Total: ¥1,159,920 (including 8% tax)

BEEF_INVOICE_OCT_2025 = {
    'vendor': 'ミートショップひら山 (Meat Shop Hirayama)',
    'period': '2025-10',
    'item': '和牛ヒレ (Wagyu Tenderloin)',
    'unit_price': 12000,  # yen per kg
    'tax_rate': 0.08,
    'entries': [
        {'date': '2025-10-09', 'slip': '002077', 'qty_kg': 6.30, 'amount': 75600},
        {'date': '2025-10-09', 'slip': '002077', 'qty_kg': 5.90, 'amount': 70800},
        {'date': '2025-10-11', 'slip': '002188', 'qty_kg': 5.80, 'amount': 69600},
        {'date': '2025-10-11', 'slip': '002188', 'qty_kg': 5.70, 'amount': 68400},
        {'date': '2025-10-13', 'slip': '002242', 'qty_kg': 6.10, 'amount': 73200},
        {'date': '2025-10-16', 'slip': '002297', 'qty_kg': 6.00, 'amount': 72000},
        {'date': '2025-10-16', 'slip': '002297', 'qty_kg': 5.50, 'amount': 66000},
        {'date': '2025-10-18', 'slip': '002404', 'qty_kg': 7.30, 'amount': 87600},
        {'date': '2025-10-21', 'slip': '002485', 'qty_kg': 7.10, 'amount': 85200},
        {'date': '2025-10-21', 'slip': '002485', 'qty_kg': 7.30, 'amount': 87600},
        {'date': '2025-10-23', 'slip': '002558', 'qty_kg': 7.90, 'amount': 94800},
        {'date': '2025-10-23', 'slip': '002558', 'qty_kg': 6.00, 'amount': 72000},
        {'date': '2025-10-31', 'slip': '002847', 'qty_kg': 5.70, 'amount': 68400},
        {'date': '2025-10-31', 'slip': '002847', 'qty_kg': 6.90, 'amount': 82800},
    ],
    'totals': {
        'total_kg': 89.50,
        'subtotal': 1074000,
        'tax': 85920,
        'grand_total': 1159920,
    }
}

# ===== CAVIAR INVOICE - French F&B Japan =====
# Invoice: 〇202511_-_買掛金計上済French_FnB__Caviar_etc__.pdf
# Period: October 2025
# Total (all items): ¥898,907 (including 8% tax)

CAVIAR_INVOICE_OCT_2025 = {
    'vendor': 'フレンチ・エフ・アンド・ビー (French F&B Japan)',
    'period': '2025-10',
    'tax_rate': 0.08,
    'caviar_entries': [
        {
            'date': '2025-10-01',
            'slip': '6830',
            'item': 'KAVIARI キャビア クリスタル100g セレクションJG',
            'amount': 117000,
            'estimated_qty_g': 300,  # ~3 × 100g
        },
        {
            'date': '2025-10-28',
            'slip': '7159',
            'item': 'KAVIARI キャビア クリスタル100g セレクションJG',
            'amount': 195000,
            'estimated_qty_g': 500,  # ~5 × 100g
        },
        {
            'date': '2025-10-11',
            'slip': '6976',
            'item': 'キャヴィア クリスタル フレッシュ 100g',
            'amount': 195000,
            'estimated_qty_g': 500,  # ~5 × 100g (Kitchen order)
        },
    ],
    'other_entries': [
        {'date': '2025-10-03', 'item': 'パレット バター 20g', 'amount': 26100},
        {'date': '2025-10-10', 'item': 'パレット バター 20g', 'amount': 18800},
        {'date': '2025-10-16', 'item': '生 スモールジロール 1kg', 'amount': 19400},
        {'date': '2025-10-17', 'item': 'プチ モン ブール バター 20g', 'amount': 36250},
        {'date': '2025-10-18', 'item': 'シャンパン ヴィネガー 500ml', 'amount': 120440},
        {'date': '2025-10-21', 'item': 'シャンパン ヴィネガー 500ml', 'amount': 3320},
        {'date': '2025-10-24', 'item': 'パレット バター 20g', 'amount': 34800},
        {'date': '2025-10-31', 'item': 'パレット バター 20g', 'amount': 69600},
        {'date': '2025-10-31', 'item': 'シャンパン ヴィネガー 500ml', 'amount': -3440},  # Credit
    ],
    'caviar_totals': {
        'total_g': 1300,  # estimated
        'subtotal': 507000,
        'tax': 40560,
        'grand_total': 547560,
    },
    'invoice_totals': {
        'subtotal': 832270,
        'tax': 66637,
        'grand_total': 898907,
    }
}

# ===== SALES DATA - October 2025 =====
SALES_OCT_2025 = {
    'beef_tenderloin': {
        'total_servings': 201,
        'total_revenue': 1594447,
        'categories': ['Lunch', 'Dinner', 'A la carte', 'In Room Dining'],
    },
    'egg_toast_caviar': {
        'total_servings': 252,
        'total_revenue': 463116,
        'categories': ['Dinner', 'A la carte', 'In Room Dining'],
    }
}

# ===== RECIPE ASSUMPTIONS =====
RECIPE_ASSUMPTIONS = {
    'beef_tenderloin': {
        'portion_g': 180,  # grams of cooked tenderloin per serving
        'yield_pct': 0.65,  # ~65% yield after trimming
        'raw_needed_g': 277,  # 180 / 0.65 = ~277g raw per serving
    },
    'egg_toast_caviar': {
        'portion_g': 5,  # grams of caviar per serving (garnish)
    }
}

# ===== ANALYSIS RESULTS =====
def calculate_analysis():
    """Calculate efficiency metrics"""
    
    # Beef Analysis
    beef_purchased = BEEF_INVOICE_OCT_2025['totals']['total_kg']
    beef_cost = BEEF_INVOICE_OCT_2025['totals']['grand_total']
    beef_servings = SALES_OCT_2025['beef_tenderloin']['total_servings']
    beef_revenue = SALES_OCT_2025['beef_tenderloin']['total_revenue']
    
    # Using raw-to-cooked yield
    raw_per_serving = RECIPE_ASSUMPTIONS['beef_tenderloin']['raw_needed_g'] / 1000  # kg
    expected_beef = beef_servings * raw_per_serving
    
    beef_results = {
        'purchased_kg': beef_purchased,
        'expected_kg': round(expected_beef, 2),
        'variance_kg': round(beef_purchased - expected_beef, 2),
        'variance_pct': round((beef_purchased - expected_beef) / beef_purchased * 100, 1),
        'cost': beef_cost,
        'revenue': beef_revenue,
        'cost_ratio_pct': round(beef_cost / beef_revenue * 100, 1),
        'gross_profit': beef_revenue - beef_cost,
    }
    
    # Caviar Analysis
    caviar_purchased = CAVIAR_INVOICE_OCT_2025['caviar_totals']['total_g']
    caviar_cost = CAVIAR_INVOICE_OCT_2025['caviar_totals']['grand_total']
    caviar_servings = SALES_OCT_2025['egg_toast_caviar']['total_servings']
    caviar_revenue = SALES_OCT_2025['egg_toast_caviar']['total_revenue']
    
    portion_g = RECIPE_ASSUMPTIONS['egg_toast_caviar']['portion_g']
    expected_caviar = caviar_servings * portion_g
    
    caviar_results = {
        'purchased_g': caviar_purchased,
        'expected_g': expected_caviar,
        'variance_g': caviar_purchased - expected_caviar,
        'variance_pct': round((caviar_purchased - expected_caviar) / caviar_purchased * 100, 1) if caviar_purchased > 0 else 0,
        'cost': caviar_cost,
        'revenue': caviar_revenue,
        'cost_ratio_pct': round(caviar_cost / caviar_revenue * 100, 1),
        'gross_profit': caviar_revenue - caviar_cost,
        'cost_per_gram': round(caviar_cost / caviar_purchased, 0) if caviar_purchased > 0 else 0,
    }
    
    return {'beef': beef_results, 'caviar': caviar_results}


if __name__ == '__main__':
    results = calculate_analysis()
    
    print("October 2025 Analysis Results")
    print("=" * 50)
    
    print("\n🥩 Beef Tenderloin:")
    for k, v in results['beef'].items():
        print(f"   {k}: {v}")
    
    print("\n🐟 Egg Toast Caviar:")
    for k, v in results['caviar'].items():
        print(f"   {k}: {v}")
