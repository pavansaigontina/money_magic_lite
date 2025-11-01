import streamlit as st
from datetime import datetime
from core.accounts import get_accounts
from core.balances import get_opening, set_opening
from core.utils import MONTHS

def show_balances_view(user):
    st.header("🔧 Balances")
    accounts = get_accounts()
    if not accounts:
        st.info("Add accounts first.")
        return
    with st.expander("Show Balance Form"):
        with st.form("balance_form"):
            sel_month = st.selectbox("Select month", MONTHS, index=datetime.now().month-1)
            sel_account = st.selectbox("Select account", [a['name'] for a in accounts])
            aid = next((a['id'] for a in accounts if a['name']==sel_account), None)
            current = get_opening(sel_month, aid)
            new_opening = st.number_input(f"Opening for {sel_account} in {sel_month}", value=current, min_value=0.0, step=100.0, format="%.2f")
            if st.form_submit_button("Save opening"):
                set_opening(sel_month, aid, new_opening)
                st.success("Saved opening balance")
                st.rerun()
