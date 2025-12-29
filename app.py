"""
Purchasing Evaluation System for The Shinmonzen
Analyzes ingredient purchases vs dish sales to evaluate waste and cost efficiency
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import re
from datetime import datetime
from io import StringIO

# Import our modules
from extractors import extract_sales_data, extract_invoice_data
from config import VENDOR_CONFIG, DISH_INGREDIENT_MAP

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
</style>
""", unsafe_allow_html=True)

def main():
    st.title("🍽️ Purchasing Evaluation System")
    st.markdown("**購買評価システム** | The Shinmonzen")
    
    # Sidebar for file uploads
    with st.sidebar:
        st.header("📁 Data Upload / データアップロード")
        
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
        
        st.divider()
        st.subheader("⚙️ Settings / 設定")
        
        # Ingredient usage settings (can be adjusted based on actual recipes)
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
    
    # Main content area
    if not sales_files or not invoice_files:
        st.info("👆 Please upload sales reports and invoices in the sidebar to begin analysis.")
        st.info("👆 サイドバーから売上レポートと請求書をアップロードしてください。")
        
        # Show demo with sample data explanation
        with st.expander("📖 How this system works / システムの使い方"):
            st.markdown("""
            ### Analysis Flow / 分析フロー
            
            1. **Upload Data / データアップロード**
               - Sales CSV from POS system / POSシステムからの売上CSV
               - Vendor invoices (PDF) / 仕入先請求書 (PDF)
            
            2. **Automatic Extraction / 自動抽出**
               - OCR for scanned invoices / スキャン請求書のOCR
               - Text extraction for digital PDFs / デジタルPDFのテキスト抽出
            
            3. **Analysis / 分析**
               - **Waste Ratio**: (Purchased - Expected Usage) / Purchased
               - **Cost Efficiency**: Ingredient Cost / Dish Revenue
               - **Trend Analysis**: Monthly comparison
            
            ### Vendor Mapping / 仕入先マッピング
            | Vendor / 仕入先 | Ingredient / 食材 | Dish / 料理 |
            |----------------|-------------------|-------------|
            | Meat Shop Hirayama / ミートショップひら山 | 和牛ヒレ (Wagyu Tenderloin) | Beef Tenderloin |
            | French F&B Japan / フレンチ・エフ・アンド・ビー | KAVIARI キャビア | Egg Toast Caviar |
            """)
        return
    
    # Process uploaded files
    with st.spinner("Processing files... / ファイル処理中..."):
        # Extract sales data
        all_sales = []
        for sf in sales_files:
            try:
                sales_df = extract_sales_data(sf)
                if sales_df is not None:
                    all_sales.append(sales_df)
            except Exception as e:
                st.warning(f"Error processing {sf.name}: {e}")
        
        # Extract invoice data
        all_invoices = []
        for inv in invoice_files:
            try:
                invoice_data = extract_invoice_data(inv)
                if invoice_data:
                    all_invoices.extend(invoice_data)
            except Exception as e:
                st.warning(f"Error processing {inv.name}: {e}")
    
    if not all_sales:
        st.error("No valid sales data found. Please check your CSV files.")
        return
    
    # Combine all data
    sales_combined = pd.concat(all_sales, ignore_index=True) if all_sales else pd.DataFrame()
    invoices_df = pd.DataFrame(all_invoices) if all_invoices else pd.DataFrame()
    
    # Display tabs for different analyses
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Overview / 概要",
        "🥩 Beef Analysis / 牛肉分析", 
        "🐟 Caviar Analysis / キャビア分析",
        "📋 Vendor Items / 仕入先品目"
    ])
    
    with tab1:
        display_overview(sales_combined, invoices_df, beef_per_serving, caviar_per_serving)
    
    with tab2:
        display_beef_analysis(sales_combined, invoices_df, beef_per_serving)
    
    with tab3:
        display_caviar_analysis(sales_combined, invoices_df, caviar_per_serving)
    
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
            total_beef_revenue = beef_sales['net_total'].sum()
            expected_beef_kg = (total_beef_qty * beef_per_serving) / 1000
            
            st.metric("Dishes Sold / 販売数", f"{total_beef_qty:.1f}")
            st.metric("Revenue / 売上", f"¥{total_beef_revenue:,.0f}")
            st.metric("Expected Usage / 予想使用量", f"{expected_beef_kg:.2f} kg")
    
    with col2:
        st.subheader("🐟 Egg Toast Caviar")
        if not sales_df.empty:
            caviar_sales = sales_df[sales_df['name'].str.contains('Egg Toast Caviar', case=False, na=False)]
            total_caviar_qty = caviar_sales['qty'].sum()
            total_caviar_revenue = caviar_sales['net_total'].sum()
            expected_caviar_g = total_caviar_qty * caviar_per_serving
            
            st.metric("Dishes Sold / 販売数", f"{total_caviar_qty:.1f}")
            st.metric("Revenue / 売上", f"¥{total_caviar_revenue:,.0f}")
            st.metric("Expected Usage / 予想使用量", f"{expected_caviar_g:.0f} g")
    
    st.divider()
    
    # Invoice summary
    st.subheader("📄 Invoice Summary / 請求書サマリー")
    if not invoices_df.empty:
        # Group by vendor
        vendor_summary = invoices_df.groupby('vendor').agg({
            'amount': 'sum',
            'item_name': 'count'
        }).reset_index()
        vendor_summary.columns = ['Vendor / 仕入先', 'Total Amount / 合計金額', 'Item Count / 品目数']
        vendor_summary['Total Amount / 合計金額'] = vendor_summary['Total Amount / 合計金額'].apply(lambda x: f"¥{x:,.0f}")
        st.dataframe(vendor_summary, use_container_width=True)
    else:
        st.info("No invoice data available")


def display_beef_analysis(sales_df, invoices_df, beef_per_serving):
    """Detailed beef analysis"""
    st.header("🥩 Beef Tenderloin Analysis / 和牛ヒレ分析")
    
    # Manual data entry option for scanned invoices
    with st.expander("📝 Manual Invoice Entry (for scanned PDFs) / 手動入力"):
        st.markdown("If OCR results are inaccurate, enter the totals manually:")
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            manual_beef_kg = st.number_input("Total Beef (kg) / 牛肉総量", min_value=0.0, value=0.0, step=0.5)
        with col_m2:
            manual_beef_cost = st.number_input("Total Cost (¥) / 合計金額", min_value=0, value=0, step=1000)
        use_manual = st.checkbox("Use manual values / 手動入力を使用")
    
    # Filter beef data
    beef_sales = sales_df[sales_df['name'].str.contains('Beef Tenderloin', case=False, na=False)] if not sales_df.empty else pd.DataFrame()
    beef_invoices = invoices_df[invoices_df['item_name'].str.contains('和牛|ヒレ|beef', case=False, na=False)] if not invoices_df.empty else pd.DataFrame()
    
    if beef_sales.empty and beef_invoices.empty and not use_manual:
        st.warning("No beef data available for analysis")
        return
    
    col1, col2, col3 = st.columns(3)
    
    # Calculate metrics
    total_sold = beef_sales['qty'].sum() if not beef_sales.empty else 0
    total_revenue = beef_sales['net_total'].sum() if not beef_sales.empty else 0
    expected_usage_kg = (total_sold * beef_per_serving) / 1000
    
    # Use manual values if specified, otherwise use extracted data
    if use_manual and manual_beef_kg > 0:
        total_purchased_kg = manual_beef_kg
        total_cost = manual_beef_cost
    else:
        total_purchased_kg = beef_invoices['quantity'].sum() if not beef_invoices.empty else 0
        total_cost = beef_invoices['amount'].sum() if not beef_invoices.empty else 0
    
    with col1:
        st.metric("Total Sold / 販売総数", f"{total_sold:.1f} servings")
        st.metric("Total Revenue / 売上合計", f"¥{total_revenue:,.0f}")
    
    with col2:
        st.metric("Total Purchased / 仕入総量", f"{total_purchased_kg:.2f} kg")
        st.metric("Total Cost / 仕入原価", f"¥{total_cost:,.0f}")
    
    with col3:
        if total_purchased_kg > 0:
            waste_ratio = max(0, (total_purchased_kg - expected_usage_kg) / total_purchased_kg * 100)
            st.metric("Waste Ratio / ロス率", f"{waste_ratio:.1f}%", 
                     delta=f"{waste_ratio - 15:.1f}%" if waste_ratio > 15 else None,
                     delta_color="inverse")
        
        if total_revenue > 0:
            cost_ratio = (total_cost / total_revenue) * 100
            st.metric("Cost Ratio / 原価率", f"{cost_ratio:.1f}%",
                     delta=f"{cost_ratio - 35:.1f}%" if cost_ratio > 35 else None,
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
        display_df = beef_invoices[['date', 'item_name', 'quantity', 'unit', 'unit_price', 'amount']].copy()
        display_df.columns = ['Date/日付', 'Item/品目', 'Qty/数量', 'Unit/単位', 'Unit Price/単価', 'Amount/金額']
        display_df['Amount/金額'] = display_df['Amount/金額'].apply(lambda x: f"¥{x:,.0f}")
        st.dataframe(display_df, use_container_width=True)


def display_caviar_analysis(sales_df, invoices_df, caviar_per_serving):
    """Detailed caviar analysis"""
    st.header("🐟 Caviar Analysis / キャビア分析")
    
    # Filter caviar data
    caviar_sales = sales_df[sales_df['name'].str.contains('Egg Toast Caviar', case=False, na=False)] if not sales_df.empty else pd.DataFrame()
    caviar_invoices = invoices_df[invoices_df['item_name'].str.contains('キャビア|KAVIARI|caviar', case=False, na=False)] if not invoices_df.empty else pd.DataFrame()
    
    if caviar_sales.empty and caviar_invoices.empty:
        st.warning("No caviar data available for analysis")
        return
    
    col1, col2, col3 = st.columns(3)
    
    # Calculate metrics
    total_sold = caviar_sales['qty'].sum() if not caviar_sales.empty else 0
    total_revenue = caviar_sales['net_total'].sum() if not caviar_sales.empty else 0
    expected_usage_g = total_sold * caviar_per_serving
    
    # Caviar is typically sold in 100g units
    total_purchased_units = len(caviar_invoices) if not caviar_invoices.empty else 0
    total_purchased_g = total_purchased_units * 100  # Assuming 100g per unit
    total_cost = caviar_invoices['amount'].sum() if not caviar_invoices.empty else 0
    
    with col1:
        st.metric("Total Sold / 販売総数", f"{total_sold:.1f} servings")
        st.metric("Total Revenue / 売上合計", f"¥{total_revenue:,.0f}")
    
    with col2:
        st.metric("Total Purchased / 仕入総量", f"{total_purchased_g:.0f} g ({total_purchased_units} units)")
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


def display_vendor_items(invoices_df):
    """Display all items by vendor"""
    st.header("📋 Vendor Items List / 仕入先品目一覧")
    
    if invoices_df.empty:
        st.info("No invoice data available. Upload PDF invoices to see vendor items.")
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
