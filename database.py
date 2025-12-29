"""
Database module for Supabase operations
Handles all data persistence for the Purchasing Evaluation System
"""

import streamlit as st
from supabase import create_client, Client
import pandas as pd
import re
from datetime import datetime, date
from typing import Optional, List, Dict, Any


def init_supabase() -> Optional[Client]:
    """Initialize Supabase client from Streamlit secrets"""
    try:
        url = st.secrets["supabase"]["url"]
        key = st.secrets["supabase"]["key"]
        return create_client(url, key)
    except Exception as e:
        st.warning(f"⚠️ Supabase not configured. Using file upload only. Error: {e}")
        return None


def save_invoices(supabase: Client, records: List[Dict[str, Any]]) -> int:
    """
    Save invoice records to Supabase
    Returns number of records saved
    """
    if not supabase or not records:
        return 0
    
    saved_count = 0
    batch_data = []
    
    for record in records:
        try:
            # Convert date string to proper format
            invoice_date = record.get('date', '')
            if isinstance(invoice_date, str):
                # Handle various date formats
                for fmt in ['%Y-%m-%d', '%Y/%m/%d', '%d/%m/%Y']:
                    try:
                        invoice_date = datetime.strptime(invoice_date, fmt).date().isoformat()
                        break
                    except ValueError:
                        continue
            
            # Skip if no valid date
            if not invoice_date:
                continue
            
            data = {
                'vendor': record.get('vendor', ''),
                'invoice_date': invoice_date,
                'item_name': record.get('item_name', ''),
                'quantity': float(record.get('quantity', 0)),
                'unit': record.get('unit', ''),
                'unit_price': float(record.get('unit_price', 0)),
                'amount': float(record.get('amount', 0))
            }
            
            batch_data.append(data)
                
        except Exception as e:
            continue
    
    # Batch insert (much faster than one-by-one)
    if batch_data:
        try:
            # Insert in chunks of 50 to avoid timeout
            chunk_size = 50
            for i in range(0, len(batch_data), chunk_size):
                chunk = batch_data[i:i + chunk_size]
                result = supabase.table('invoices').upsert(
                    chunk,
                    on_conflict='vendor,invoice_date,item_name,amount'
                ).execute()
                saved_count += len(chunk)
        except Exception as e:
            # If upsert fails (no unique constraint), try simple insert
            try:
                for data in batch_data:
                    supabase.table('invoices').insert(data).execute()
                    saved_count += 1
            except Exception as e2:
                st.warning(f"Error batch saving invoices: {e2}")
    
    return saved_count


def save_sales(supabase: Client, df: pd.DataFrame) -> int:
    """
    Save sales records to Supabase
    Returns number of records saved
    """
    if not supabase or df.empty:
        return 0
    
    saved_count = 0
    batch_data = []
    
    for _, row in df.iterrows():
        try:
            # Convert month (YYYY-MM) or date to proper date format
            # Sales CSV has 'month' column like "2025-10"
            sale_date = row.get('date', '') or row.get('month', '')
            
            if isinstance(sale_date, str):
                # Handle YYYY-MM format (from sales CSV)
                if re.match(r'^\d{4}-\d{2}$', sale_date):
                    sale_date = f"{sale_date}-01"  # Add day
                
                # Handle various date formats
                for fmt in ['%Y-%m-%d', '%Y/%m/%d', '%d/%m/%Y']:
                    try:
                        sale_date = datetime.strptime(sale_date, fmt).date().isoformat()
                        break
                    except ValueError:
                        continue
            elif hasattr(sale_date, 'isoformat'):
                sale_date = sale_date.isoformat()
            
            # Skip if no valid date
            if not sale_date or sale_date == '':
                continue
            
            data = {
                'sale_date': sale_date,
                'code': str(row.get('code', '')),
                'item_name': str(row.get('name', '')),
                'category': str(row.get('category', '')),
                'qty': float(row.get('qty', 0)),
                'price': float(row.get('price', 0)) if pd.notna(row.get('price')) else 0,
                'net_total': float(row.get('net_total', 0)) if pd.notna(row.get('net_total')) else 0
            }
            
            batch_data.append(data)
                
        except Exception as e:
            continue
    
    # Batch insert (much faster than one-by-one)
    if batch_data:
        try:
            # Insert in chunks of 100 to avoid timeout
            chunk_size = 100
            for i in range(0, len(batch_data), chunk_size):
                chunk = batch_data[i:i + chunk_size]
                result = supabase.table('sales').insert(chunk).execute()
                saved_count += len(chunk)
        except Exception as e:
            st.warning(f"Error batch saving sales: {e}")
    
    return saved_count


def load_invoices(supabase: Client, start_date: Optional[date] = None, 
                  end_date: Optional[date] = None, vendor: Optional[str] = None) -> pd.DataFrame:
    """
    Load invoices from Supabase with optional filters
    """
    if not supabase:
        return pd.DataFrame()
    
    try:
        query = supabase.table('invoices').select('*')
        
        if start_date:
            query = query.gte('invoice_date', start_date.isoformat())
        if end_date:
            query = query.lte('invoice_date', end_date.isoformat())
        if vendor:
            query = query.ilike('vendor', f'%{vendor}%')
        
        result = query.order('invoice_date', desc=True).execute()
        
        if result.data:
            df = pd.DataFrame(result.data)
            # Rename columns to match expected format
            df = df.rename(columns={
                'invoice_date': 'date',
                'item_name': 'item_name'
            })
            return df
        return pd.DataFrame()
        
    except Exception as e:
        st.error(f"Error loading invoices: {e}")
        return pd.DataFrame()


def load_sales(supabase: Client, start_date: Optional[date] = None,
               end_date: Optional[date] = None, item_filter: Optional[str] = None) -> pd.DataFrame:
    """
    Load sales from Supabase with optional filters
    """
    if not supabase:
        return pd.DataFrame()
    
    try:
        query = supabase.table('sales').select('*')
        
        if start_date:
            query = query.gte('sale_date', start_date.isoformat())
        if end_date:
            query = query.lte('sale_date', end_date.isoformat())
        if item_filter:
            query = query.ilike('item_name', f'%{item_filter}%')
        
        result = query.order('sale_date', desc=True).execute()
        
        if result.data:
            df = pd.DataFrame(result.data)
            # Rename columns to match expected format
            df = df.rename(columns={
                'sale_date': 'date',
                'item_name': 'name'
            })
            return df
        return pd.DataFrame()
        
    except Exception as e:
        st.error(f"Error loading sales: {e}")
        return pd.DataFrame()


def get_date_range(supabase: Client) -> tuple:
    """
    Get the min and max dates from both invoices and sales
    Returns (min_date, max_date)
    """
    if not supabase:
        return None, None
    
    try:
        # Get invoice date range
        inv_min = supabase.table('invoices').select('invoice_date').order('invoice_date', desc=False).limit(1).execute()
        inv_max = supabase.table('invoices').select('invoice_date').order('invoice_date', desc=True).limit(1).execute()
        
        # Get sales date range
        sales_min = supabase.table('sales').select('sale_date').order('sale_date', desc=False).limit(1).execute()
        sales_max = supabase.table('sales').select('sale_date').order('sale_date', desc=True).limit(1).execute()
        
        dates = []
        for result in [inv_min, inv_max, sales_min, sales_max]:
            if result.data:
                date_val = result.data[0].get('invoice_date') or result.data[0].get('sale_date')
                if date_val:
                    dates.append(datetime.fromisoformat(date_val).date())
        
        if dates:
            return min(dates), max(dates)
        return None, None
        
    except Exception as e:
        st.error(f"Error getting date range: {e}")
        return None, None


def get_data_summary(supabase: Client) -> Dict[str, Any]:
    """
    Get summary statistics of stored data
    """
    if not supabase:
        return {}
    
    try:
        # Count invoices
        inv_count = supabase.table('invoices').select('id', count='exact').execute()
        
        # Count sales
        sales_count = supabase.table('sales').select('id', count='exact').execute()
        
        # Get date range
        min_date, max_date = get_date_range(supabase)
        
        return {
            'invoice_count': inv_count.count if inv_count else 0,
            'sales_count': sales_count.count if sales_count else 0,
            'min_date': min_date,
            'max_date': max_date
        }
        
    except Exception as e:
        st.error(f"Error getting summary: {e}")
        return {}


def delete_data_by_date_range(supabase: Client, start_date: date, end_date: date, 
                               table: str = 'both') -> Dict[str, int]:
    """
    Delete data within a date range
    table: 'invoices', 'sales', or 'both'
    Returns count of deleted records
    """
    if not supabase:
        return {'invoices': 0, 'sales': 0}
    
    deleted = {'invoices': 0, 'sales': 0}
    
    try:
        if table in ['invoices', 'both']:
            result = supabase.table('invoices').delete().gte(
                'invoice_date', start_date.isoformat()
            ).lte(
                'invoice_date', end_date.isoformat()
            ).execute()
            deleted['invoices'] = len(result.data) if result.data else 0
        
        if table in ['sales', 'both']:
            result = supabase.table('sales').delete().gte(
                'sale_date', start_date.isoformat()
            ).lte(
                'sale_date', end_date.isoformat()
            ).execute()
            deleted['sales'] = len(result.data) if result.data else 0
            
    except Exception as e:
        st.error(f"Error deleting data: {e}")
    
    return deleted
