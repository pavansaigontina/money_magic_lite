import streamlit as st
from core.database import init_db
from ui.sidebar import sidebar_user_section
from ui.admin import admin_dashboard_button
from ui.accounts_view import show_accounts_view
from ui.balances_view import show_balances_view
from ui.transactions_view import show_transactions_view

st.set_page_config(page_title="💰 Money Magic", layout="wide")
st.title("💰 Money Magic")
st.caption("Lite Version for handling finance transactions v2.0")
# Initialize DB
init_db()

# Sidebar handles authentication
user = sidebar_user_section()
if not user:
    st.info("Please login or register from the sidebar.")
    st.stop()

# Admin button (if admin)
admin_dashboard_button(user)

# Layout
left_col, main_col = st.columns([0.9, 3])
with left_col:
    show_accounts_view(user)
    show_balances_view(user)

with main_col:
    show_transactions_view(user)
