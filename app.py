"""
Purchasing Evaluation System for The Shinmonzen
Analyzes ingredient purchases vs dish sales to evaluate waste and cost efficiency
With Supabase database integration for persistent storage
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import re
from datetime import datetime, date, timedelta
from io import StringIO

# Import our modules
from extractors import extract_sales_data, extract_invoice_data
from config import VENDOR_CONFIG, DISH_INGREDIENT_MAP
from database import (
    init_supabase, save_invoices, save_sales, 
    load_invoices, load_sales, get_date_range, get_data_summary,
    delete_data_by_date_range
)

st.set_page_config(
    page_title="Purchasing Evaluation | The Shinmonzen",
    page_icon="🍽️",
    layout="wide"
)

# Custom CSS for bilingual support
st.markdown("""
<style>
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        margin: 10px 0;
    }
    .vendor-header {
        font-size: 1.2em;
        font-weight: bold;
        padding: 10px;
        background: #f0f2f6;
        border-radius: 5px;
        margin: 10px 0;
    }
    .db-status-connected {
        padding: 10px;
        background: #d4edda;
        border-radius: 5px;
        color: #155724;
        margin: 5px 0;
    }
    .db-status-disconnected {
        padding: 10px;
        background: #f8d7da;
        border-radius: 5px;
        color: #721c24;
        margin: 5px 0;
    }
</style>
""", unsafe_allow_html=True)


def main():
    st.title("🍽️ Purchasing Evaluation System")
    st.markdown("**購買評価システム** | The Shinmonzen")
    
    # Initialize Supabase
    supabase = init_supabase()
    
    # Sidebar
    with st.sidebar:
        # Database status
        st.header("💾 Database / データベース")
        if supabase:
            summary = get_data_summary(supabase)
            st.markdown('<div class="db-status-connected">✅ Connected / 接続中</div>', unsafe_allow_html=True)
            st.caption(f"📊 {summary.get('invoice_count', 0)} invoices, {summary.get('sales_count', 0)} sales records")
            if summary.get('min_date') and summary.get('max_date'):
                st.caption(f"📅 {summary['min_date']} ~ {summary['max_date']}")
        else:
            st.markdown('<div class="db-status-disconnected">❌ Not connected / 未接続</div>', unsafe_allow_html=True)
            st.caption("Using file upload only")
        
        st.divider()
        
        # Date range filter
        st.header("📅 Date Filter / 期間フィルター")
        
        # Get available date range from database
        if supabase:
            db_min_date, db_max_date = get_date_range(supabase)
        else:
            db_min_date, db_max_date = None, None
        
        # Default to last month if no data
        default_end = db_max_date or date.today()
        default_start = db_min_date or (default_end - timedelta(days=30))
        
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input(
                "From / 開始日",
                value=default_start,
                min_value=date(2020, 1, 1),
                max_value=default_end
            )
        with col2:
            end_date = st.date_input(
                "To / 終了日",
                value=default_end,
                min_value=start_date,
                max_value=date.today()
            )
        
        # Quick date presets
        st.caption("Quick select / クイック選択:")
        preset_col1, preset_col2 = st.columns(2)
        with preset_col1:
            if st.button("This Month", use_container_width=True):
                start_date = date.today().replace(day=1)
                end_date = date.today()
                st.rerun()
        with preset_col2:
            if st.button("Last Month", use_container_width=True):
                last_month = date.today().replace(day=1) - timedelta(days=1)
                start_date = last_month.replace(day=1)
                end_date = last_month
                st.rerun()
        
        st.divider()
        
        # File upload section
        st.header("📁 Upload Data / データアップロード")
        
        sales_files = st.file_uploader(
            "Sales Reports (CSV) / 売上レポート",
            type=['csv'],
            accept_multiple_files=True,
            help="Upload Item Sales CSV files from POS system"
        )
        
        invoice_files = st.file_uploader(
            "Invoices (PDF) / 請求書",
            type=['pdf'],
            accept_multiple_files=True,
            help="Upload vendor invoices (PDF)"
        )
        
        # Process and save uploaded files
        if sales_files or invoice_files:
            if st.button("💾 Save to Database / データベースに保存", type="primary", use_container_width=True):
                if not supabase:
                    st.error("Database not connected. Configure Supabase in Streamlit secrets.")
                else:
                    with st.spinner("Processing and saving... / 処理中..."):
                        saved_invoices = 0
                        saved_sales = 0
                        
                        # Process invoices
                        for inv in invoice_files:
                            try:
                                invoice_data = extract_invoice_data(inv)
                                if invoice_data:
                                    saved_invoices += save_invoices(supabase, invoice_data)
                            except Exception as e:
                                st.warning(f"Error processing {inv.name}: {e}")
                        
                        # Process sales
                        for sf in sales_files:
                            try:
                                sales_df = extract_sales_data(sf)
                                if sales_df is not None and not sales_df.empty:
                                    saved_sales += save_sales(supabase, sales_df)
                            except Exception as e:
                                st.warning(f"Error processing {sf.name}: {e}")
                        
                        st.success(f"✅ Saved {saved_invoices} invoices, {saved_sales} sales records")
                        st.rerun()
        
        st.divider()
        
        # Settings
        st.subheader("⚙️ Settings / 設定")
        
        beef_per_serving = st.number_input(
            "Beef per serving (g) / 1人前の牛肉量",
            min_value=50, max_value=500, value=180,
            help="Grams of beef tenderloin per Beef Tenderloin dish"
        )
        
        caviar_per_serving = st.number_input(
            "Caviar per serving (g) / 1人前のキャビア量",
            min_value=5, max_value=50, value=15,
            help="Grams of caviar per Egg Toast Caviar dish"
        )
        
        # Data management (expandable)
        with st.expander("🗑️ Data Management / データ管理"):
            st.warning("⚠️ Danger zone / 危険ゾーン")
            if st.button("Delete data in selected date range", type="secondary"):
                if supabase:
                    deleted = delete_data_by_date_range(supabase, start_date, end_date)
                    st.info(f"Deleted {deleted['invoices']} invoices, {deleted['sales']} sales")
                    st.rerun()
    
    # Main content area - Load data from database or files
    sales_df = pd.DataFrame()
    invoices_df = pd.DataFrame()
    
    if supabase:
        # Load from database with date filter
        with st.spinner("Loading data from database... / データベースから読み込み中..."):
            invoices_df = load_invoices(supabase, start_date, end_date)
            sales_df = load_sales(supabase, start_date, end_date)
    
    # If no database data, try to use uploaded files directly (preview mode)
    if sales_df.empty and invoices_df.empty:
        if sales_files or invoice_files:
            st.info("📤 Preview mode: Showing uploaded file data. Click 'Save to Database' to persist.")
            
            # Process files for preview
            all_sales = []
            for sf in sales_files:
                try:
                    sf.seek(0)  # Reset file pointer
                    temp_sales = extract_sales_data(sf)
                    if temp_sales is not None:
                        all_sales.append(temp_sales)
                except Exception as e:
                    st.warning(f"Error processing {sf.name}: {e}")
            
            all_invoices = []
            for inv in invoice_files:
                try:
                    inv.seek(0)  # Reset file pointer
                    invoice_data = extract_invoice_data(inv)
                    if invoice_data:
                        all_invoices.extend(invoice_data)
                except Exception as e:
                    st.warning(f"Error processing {inv.name}: {e}")
            
            sales_df = pd.concat(all_sales, ignore_index=True) if all_sales else pd.DataFrame()
            invoices_df = pd.DataFrame(all_invoices) if all_invoices else pd.DataFrame()
        else:
            # Show welcome message
            st.info("👆 Please upload sales reports and invoices in the sidebar, or view existing data from the database.")
            st.info("👆 サイドバーから売上レポートと請求書をアップロードするか、データベースの既存データを表示してください。")
            
            with st.expander("📖 How this system works / システムの使い方"):
                st.markdown("""
                ### Analysis Flow / 分析フロー
                
                1. **Upload Data / データアップロード**
                   - Sales CSV from POS system / POSシステムからの売上CSV
                   - Vendor invoices (PDF) / 仕入先請求書 (PDF)
                
                2. **Save to Database / データベースに保存**
                   - Data is stored persistently / データは永続的に保存されます
                   - No need to re-upload each time / 毎回アップロードする必要はありません
                
                3. **Filter by Date / 期間でフィルター**
                   - View specific time periods / 特定の期間を表示
                   - Compare months / 月別比較
                
                4. **Analysis / 分析**
                   - **Waste Ratio**: (Purchased - Expected Usage) / Purchased
                   - **Cost Efficiency**: Ingredient Cost / Dish Revenue
                
                ### Vendor Mapping / 仕入先マッピング
                | Vendor / 仕入先 | Ingredient / 食材 | Dish / 料理 |
                |----------------|-------------------|-------------|
                | Meat Shop Hirayama / ミートショップひら山 | 和牛ヒレ (Wagyu Tenderloin) | Beef Tenderloin |
                | French F&B Japan / フレンチ・エフ・アンド・ビー | KAVIARI キャビア | Egg Toast Caviar |
                """)
            return
    
    # Show current data period
    st.caption(f"📅 Showing data from **{start_date}** to **{end_date}**")
    
    # Display tabs for different analyses
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Overview / 概要",
        "🥩 Beef Analysis / 牛肉分析", 
        "🐟 Caviar Analysis / キャビア分析",
        "📋 Vendor Items / 仕入先品目"
    ])
    
    with tab1:
        display_overview(sales_df, invoices_df, beef_per_serving, caviar_per_serving)
    
    with tab2:
        display_beef_analysis(sales_df, invoices_df, beef_per_serving)
    
    with tab3:
        display_caviar_analysis(sales_df, invoices_df, caviar_per_serving)
    
    with tab4:
        display_vendor_items(invoices_df)


def display_overview(sales_df, invoices_df, beef_per_serving, caviar_per_serving):
    """Display overview dashboard"""
    st.header("📊 Overview / 概要")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🥩 Beef Tenderloin")
        if not sales_df.empty:
            beef_sales = sales_df[sales_df['name'].str.contains('Beef Tenderloin', case=False, na=False)]
            total_beef_qty = beef_sales['qty'].sum()
            
            # Calculate revenue with fixed dinner price ¥5,682
            beef_dinner_price = 5682
            beef_sales_calc = beef_sales.copy()
            beef_sales_calc['calc_price'] = beef_sales_calc.apply(
                lambda row: beef_dinner_price if row['price'] == 0 or pd.isna(row['price']) else row['price'],
                axis=1
            )
            beef_sales_calc['calc_revenue'] = beef_sales_calc.apply(
                lambda row: row['net_total'] if row['net_total'] != 0 else row['qty'] * row['calc_price'],
                axis=1
            )
            total_beef_revenue = beef_sales_calc['calc_revenue'].sum()
            
            expected_beef_kg = (total_beef_qty * beef_per_serving) / 1000
            
            st.metric("Dishes Sold / 販売数", f"{total_beef_qty:.0f}")
            st.metric("Revenue / 売上", f"¥{total_beef_revenue:,.0f}")
            st.metric("Expected Usage / 予想使用量", f"{expected_beef_kg:.2f} kg")
    
    with col2:
        st.subheader("🐟 Egg Toast Caviar")
        if not sales_df.empty:
            caviar_sales = sales_df[sales_df['name'].str.contains('Egg Toast Caviar', case=False, na=False)]
            total_caviar_qty = caviar_sales['qty'].sum()
            
            # Calculate revenue with fixed dinner price (same as lunch price)
            caviar_dinner_price = 3247  # Course item estimate
            caviar_sales_calc = caviar_sales.copy()
            caviar_sales_calc['calc_price'] = caviar_sales_calc.apply(
                lambda row: caviar_dinner_price if row['price'] == 0 or pd.isna(row['price']) else row['price'],
                axis=1
            )
            caviar_sales_calc['calc_revenue'] = caviar_sales_calc.apply(
                lambda row: row['net_total'] if row['net_total'] != 0 else row['qty'] * row['calc_price'],
                axis=1
            )
            total_caviar_revenue = caviar_sales_calc['calc_revenue'].sum()
            
            expected_caviar_g = total_caviar_qty * caviar_per_serving
            
            st.metric("Dishes Sold / 販売数", f"{total_caviar_qty:.0f}")
            st.metric("Revenue / 売上", f"¥{total_caviar_revenue:,.0f}")
            st.metric("Expected Usage / 予想使用量", f"{expected_caviar_g:.0f} g")
    
    # Purchase summary
    st.subheader("💰 Purchase Summary / 仕入概要")
    if not invoices_df.empty:
        # Group by vendor
        vendor_summary = invoices_df.groupby('vendor').agg({
            'amount': 'sum'
        }).reset_index()
        vendor_summary.columns = ['Vendor / 仕入先', 'Total / 合計']
        vendor_summary['Total / 合計'] = vendor_summary['Total / 合計'].apply(lambda x: f"¥{x:,.0f}")
        st.dataframe(vendor_summary, use_container_width=True)
        
        # Total purchases
        total_purchases = invoices_df['amount'].sum()
        st.metric("Total Purchases / 仕入合計", f"¥{total_purchases:,.0f}")
    else:
        st.info("No invoice data in selected period")


def display_beef_analysis(sales_df, invoices_df, beef_per_serving):
    """Detailed beef tenderloin analysis"""
    st.header("🥩 Beef Tenderloin Analysis / 牛肉分析")
    
    # Filter beef data
    beef_sales = sales_df[sales_df['name'].str.contains('Beef Tenderloin', case=False, na=False)] if not sales_df.empty else pd.DataFrame()
    beef_invoices = invoices_df[invoices_df['item_name'].str.contains('ヒレ|フィレ|tenderloin|牛', case=False, na=False)] if not invoices_df.empty else pd.DataFrame()
    
    if beef_sales.empty and beef_invoices.empty:
        st.warning("No beef data available for analysis in selected period")
        return
    
    col1, col2, col3 = st.columns(3)
    
    # Fixed price for Beef Tenderloin Dinner course items
    beef_dinner_price = 5682
    
    # Calculate metrics
    total_sold = beef_sales['qty'].sum() if not beef_sales.empty else 0
    
    # Calculate revenue including estimated revenue for course items
    if not beef_sales.empty:
        beef_sales_calc = beef_sales.copy()
        # Use fixed dinner price where price is 0
        beef_sales_calc['calc_price'] = beef_sales_calc.apply(
            lambda row: beef_dinner_price if row['price'] == 0 or pd.isna(row['price']) else row['price'],
            axis=1
        )
        # Then calculate revenue: use net_total if exists, otherwise qty * price
        beef_sales_calc['calc_revenue'] = beef_sales_calc.apply(
            lambda row: row['net_total'] if row['net_total'] != 0 else row['qty'] * row['calc_price'],
            axis=1
        )
        total_revenue = beef_sales_calc['calc_revenue'].sum()
    else:
        total_revenue = 0
    
    expected_usage_g = total_sold * beef_per_serving
    expected_usage_kg = expected_usage_g / 1000
    
    # Calculate purchases - handle both kg and individual items
    if not beef_invoices.empty:
        total_purchased_kg = beef_invoices['quantity'].sum()
        total_cost = beef_invoices['amount'].sum()
    else:
        total_purchased_kg = 0
        total_cost = 0
    
    with col1:
        st.metric("Total Sold / 販売総数", f"{total_sold:.0f} servings")
        st.metric("Total Revenue / 売上合計", f"¥{total_revenue:,.0f}")
    
    with col2:
        st.metric("Total Purchased / 仕入総量", f"{total_purchased_kg:.2f} kg")
        st.metric("Total Cost / 仕入原価", f"¥{total_cost:,.0f}")
    
    with col3:
        if total_purchased_kg > 0:
            waste_ratio = max(0, (total_purchased_kg - expected_usage_kg) / total_purchased_kg * 100)
            st.metric("Waste Ratio / ロス率", f"{waste_ratio:.1f}%",
                     delta=f"{waste_ratio - 35:.1f}%" if waste_ratio > 35 else None,
                     delta_color="inverse")
        
        if total_revenue > 0:
            cost_ratio = (total_cost / total_revenue) * 100
            st.metric("Cost Ratio / 原価率", f"{cost_ratio:.1f}%",
                     delta=f"{cost_ratio - 30:.1f}%" if cost_ratio > 30 else None,
                     delta_color="inverse")
    
    # Usage comparison chart
    st.subheader("📈 Usage Comparison / 使用量比較")
    
    comparison_data = pd.DataFrame({
        'Category': ['Purchased\n仕入量', 'Expected Usage\n予想使用量', 'Potential Waste\n予想ロス'],
        'Amount (kg)': [total_purchased_kg, expected_usage_kg, max(0, total_purchased_kg - expected_usage_kg)]
    })
    
    fig = px.bar(comparison_data, x='Category', y='Amount (kg)', 
                 color='Category',
                 color_discrete_sequence=['#3366cc', '#109618', '#dc3912'])
    fig.update_layout(showlegend=False)
    st.plotly_chart(fig, use_container_width=True)
    
    # Detailed invoice breakdown
    if not beef_invoices.empty:
        st.subheader("📋 Purchase Details / 仕入明細")
        display_df = beef_invoices[['date', 'item_name', 'quantity', 'unit', 'amount']].copy()
        display_df.columns = ['Date/日付', 'Item/品目', 'Qty/数量', 'Unit/単位', 'Amount/金額']
        display_df['Amount/金額'] = display_df['Amount/金額'].apply(lambda x: f"¥{x:,.0f}")
        st.dataframe(display_df, use_container_width=True)
    
    # Detailed sales breakdown
    if not beef_sales.empty:
        st.subheader("🍽️ Sales Details / 売上明細")
        sales_display = beef_sales[['code', 'name', 'category', 'qty', 'price', 'net_total']].copy()
        
        # Apply fixed price for Dinner items, keep original for others
        sales_display['price'] = sales_display.apply(
            lambda row: beef_dinner_price if (row['price'] == 0 or pd.isna(row['price'])) else row['price'], 
            axis=1
        )
        
        # Calculate revenue: use net_total if exists, otherwise qty * price
        sales_display['net_total'] = sales_display.apply(
            lambda row: row['net_total'] if row['net_total'] != 0 else row['qty'] * row['price'],
            axis=1
        )
        
        sales_display.columns = ['Code/コード', 'Item/品目', 'Category/カテゴリ', 'Qty/数量', 'Price/単価', 'Revenue/売上']
        sales_display['Price/単価'] = sales_display['Price/単価'].apply(lambda x: f"¥{x:,.0f}")
        sales_display['Revenue/売上'] = sales_display['Revenue/売上'].apply(lambda x: f"¥{x:,.0f}")
        
        # Add note about estimated prices
        st.caption("※ Dinner course items: estimated at ¥5,682/dish")
        st.dataframe(sales_display, use_container_width=True)
        
        # Summary by category
        st.subheader("📊 Sales by Category / カテゴリ別売上")
        beef_sales_summary = beef_sales.copy()
        # Use fixed dinner price where price is 0
        beef_sales_summary['calc_price'] = beef_sales_summary.apply(
            lambda row: beef_dinner_price if row['price'] == 0 or pd.isna(row['price']) else row['price'],
            axis=1
        )
        # Then calculate revenue: use net_total if exists, otherwise qty * price
        beef_sales_summary['calc_revenue'] = beef_sales_summary.apply(
            lambda row: row['net_total'] if row['net_total'] != 0 else row['qty'] * row['calc_price'],
            axis=1
        )
        category_summary = beef_sales_summary.groupby('category').agg({
            'qty': 'sum',
            'calc_revenue': 'sum'
        }).reset_index()
        category_summary.columns = ['Category/カテゴリ', 'Qty/数量', 'Revenue/売上']
        category_summary['Revenue/売上'] = category_summary['Revenue/売上'].apply(lambda x: f"¥{x:,.0f}")
        st.dataframe(category_summary, use_container_width=True)


def display_caviar_analysis(sales_df, invoices_df, caviar_per_serving):
    """Detailed caviar analysis"""
    st.header("🐟 Caviar Analysis / キャビア分析")
    
    # Filter caviar data
    caviar_sales = sales_df[sales_df['name'].str.contains('Egg Toast Caviar', case=False, na=False)] if not sales_df.empty else pd.DataFrame()
    caviar_invoices = invoices_df[invoices_df['item_name'].str.contains('キャビア|KAVIARI|caviar', case=False, na=False)] if not invoices_df.empty else pd.DataFrame()
    
    if caviar_sales.empty and caviar_invoices.empty:
        st.warning("No caviar data available for analysis in selected period")
        return
    
    col1, col2, col3 = st.columns(3)
    
    # Course price estimation
    course_price = 19480.44
    num_courses = 6
    estimated_course_item_price = course_price / num_courses
    
    # Calculate metrics
    total_sold = caviar_sales['qty'].sum() if not caviar_sales.empty else 0
    
    # Calculate revenue including estimated revenue for course items
    if not caviar_sales.empty:
        caviar_sales_calc = caviar_sales.copy()
        # First fill in price where missing
        caviar_sales_calc['calc_price'] = caviar_sales_calc.apply(
            lambda row: estimated_course_item_price if row['price'] == 0 or pd.isna(row['price']) else row['price'],
            axis=1
        )
        # Then calculate revenue: use net_total if exists, otherwise qty * price
        caviar_sales_calc['calc_revenue'] = caviar_sales_calc.apply(
            lambda row: row['net_total'] if row['net_total'] != 0 else row['qty'] * row['calc_price'],
            axis=1
        )
        total_revenue = caviar_sales_calc['calc_revenue'].sum()
    else:
        total_revenue = 0
    
    expected_usage_g = total_sold * caviar_per_serving
    
    # Caviar is typically sold in 100g units, but quantity may be in grams or units
    if not caviar_invoices.empty:
        # Check if quantity is in grams (large numbers) or units (small numbers)
        total_qty = caviar_invoices['quantity'].sum()
        if total_qty > 100:  # Likely in grams already
            total_purchased_g = total_qty
        else:  # Likely in units, convert to grams
            total_purchased_g = total_qty * 100
        total_purchased_units = total_purchased_g / 100
        total_cost = caviar_invoices['amount'].sum()
    else:
        total_purchased_g = 0
        total_purchased_units = 0
        total_cost = 0
    
    with col1:
        st.metric("Total Sold / 販売総数", f"{total_sold:.0f} servings")
        st.metric("Total Revenue / 売上合計", f"¥{total_revenue:,.0f}")
    
    with col2:
        st.metric("Total Purchased / 仕入総量", f"{total_purchased_g:.0f} g ({total_purchased_units:.0f} units)")
        st.metric("Total Cost / 仕入原価", f"¥{total_cost:,.0f}")
    
    with col3:
        if total_purchased_g > 0:
            waste_ratio = max(0, (total_purchased_g - expected_usage_g) / total_purchased_g * 100)
            st.metric("Waste Ratio / ロス率", f"{waste_ratio:.1f}%",
                     delta=f"{waste_ratio - 10:.1f}%" if waste_ratio > 10 else None,
                     delta_color="inverse")
        
        if total_revenue > 0:
            cost_ratio = (total_cost / total_revenue) * 100
            st.metric("Cost Ratio / 原価率", f"{cost_ratio:.1f}%",
                     delta=f"{cost_ratio - 25:.1f}%" if cost_ratio > 25 else None,
                     delta_color="inverse")
    
    # Usage comparison chart
    st.subheader("📈 Usage Comparison / 使用量比較")
    
    comparison_data = pd.DataFrame({
        'Category': ['Purchased\n仕入量', 'Expected Usage\n予想使用量', 'Potential Waste\n予想ロス'],
        'Amount (g)': [total_purchased_g, expected_usage_g, max(0, total_purchased_g - expected_usage_g)]
    })
    
    fig = px.bar(comparison_data, x='Category', y='Amount (g)', 
                 color='Category',
                 color_discrete_sequence=['#3366cc', '#109618', '#dc3912'])
    fig.update_layout(showlegend=False)
    st.plotly_chart(fig, use_container_width=True)
    
    # Detailed invoice breakdown
    if not caviar_invoices.empty:
        st.subheader("📋 Purchase Details / 仕入明細")
        display_df = caviar_invoices[['date', 'item_name', 'amount']].copy()
        display_df.columns = ['Date/日付', 'Item/品目', 'Amount/金額']
        display_df['Amount/金額'] = display_df['Amount/金額'].apply(lambda x: f"¥{x:,.0f}")
        st.dataframe(display_df, use_container_width=True)
    
    # Detailed sales breakdown
    if not caviar_sales.empty:
        st.subheader("🍽️ Sales Details / 売上明細")
        sales_display = caviar_sales[['code', 'name', 'category', 'qty', 'price', 'net_total']].copy()
        
        # Calculate estimated price for course items (Dinner category with 0 price)
        # Assume 6-course menu at ¥19,480.44
        course_price = 19480.44
        num_courses = 6
        estimated_course_item_price = course_price / num_courses
        
        # Apply estimated price only where price is 0 or missing
        sales_display['price'] = sales_display.apply(
            lambda row: estimated_course_item_price if row['price'] == 0 or pd.isna(row['price']) else row['price'], 
            axis=1
        )
        
        # Calculate revenue: use net_total if exists, otherwise qty * price
        sales_display['net_total'] = sales_display.apply(
            lambda row: row['net_total'] if row['net_total'] != 0 else row['qty'] * row['price'],
            axis=1
        )
        
        sales_display.columns = ['Code/コード', 'Item/品目', 'Category/カテゴリ', 'Qty/数量', 'Price/単価', 'Revenue/売上']
        sales_display['Price/単価'] = sales_display['Price/単価'].apply(lambda x: f"¥{x:,.0f}")
        sales_display['Revenue/売上'] = sales_display['Revenue/売上'].apply(lambda x: f"¥{x:,.0f}")
        
        # Add note about estimated prices
        st.caption("※ Dinner course items: estimated at ¥19,480 ÷ 6 courses = ¥3,247/dish")
        st.dataframe(sales_display, use_container_width=True)
        
        # Summary by category
        st.subheader("📊 Sales by Category / カテゴリ別売上")
        caviar_sales_summary = caviar_sales.copy()
        # First fill in price where missing
        caviar_sales_summary['calc_price'] = caviar_sales_summary.apply(
            lambda row: estimated_course_item_price if row['price'] == 0 or pd.isna(row['price']) else row['price'],
            axis=1
        )
        # Then calculate revenue: use net_total if exists, otherwise qty * price
        caviar_sales_summary['calc_revenue'] = caviar_sales_summary.apply(
            lambda row: row['net_total'] if row['net_total'] != 0 else row['qty'] * row['calc_price'],
            axis=1
        )
        category_summary = caviar_sales_summary.groupby('category').agg({
            'qty': 'sum',
            'calc_revenue': 'sum'
        }).reset_index()
        category_summary.columns = ['Category/カテゴリ', 'Qty/数量', 'Revenue/売上']
        category_summary['Revenue/売上'] = category_summary['Revenue/売上'].apply(lambda x: f"¥{x:,.0f}")
        st.dataframe(category_summary, use_container_width=True)


def display_vendor_items(invoices_df):
    """Display all items by vendor"""
    st.header("📋 Vendor Items List / 仕入先品目一覧")
    
    if invoices_df.empty:
        st.info("No invoice data available in selected period. Upload PDF invoices to see vendor items.")
        return
    
    # Group by vendor
    vendors = invoices_df['vendor'].unique()
    
    for vendor in vendors:
        st.subheader(f"🏪 {vendor}")
        vendor_items = invoices_df[invoices_df['vendor'] == vendor]
        
        # Summary table
        summary = vendor_items.groupby('item_name').agg({
            'quantity': 'sum',
            'amount': 'sum',
            'date': ['min', 'max', 'count']
        }).reset_index()
        summary.columns = ['Item/品目', 'Total Qty/総数量', 'Total Amount/合計金額', 
                          'First Order/初回', 'Last Order/最終', 'Order Count/注文回数']
        summary['Total Amount/合計金額'] = summary['Total Amount/合計金額'].apply(lambda x: f"¥{x:,.0f}")
        
        st.dataframe(summary, use_container_width=True)
        
        # Detailed view expander
        with st.expander(f"View all transactions / 全取引を表示"):
            detail_df = vendor_items[['date', 'item_name', 'quantity', 'unit', 'unit_price', 'amount']].copy()
            detail_df.columns = ['Date/日付', 'Item/品目', 'Qty/数量', 'Unit/単位', 'Unit Price/単価', 'Amount/金額']
            detail_df['Amount/金額'] = detail_df['Amount/金額'].apply(lambda x: f"¥{x:,.0f}" if pd.notna(x) else "")
            st.dataframe(detail_df, use_container_width=True)
        
        st.divider()


if __name__ == "__main__":
    main()
