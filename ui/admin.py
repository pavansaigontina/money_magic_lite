import streamlit as st
from core.database import query
import pandas as pd

def admin_dashboard_button(user):
    cols = st.columns([1, 0.12])
    with cols[1]:
        if user and user.get("is_admin"):
            if st.button("⚙️ Admin Dashboard"):
                # fallback to expander/modal hybrid for older versions
                with st.expander("🧭 Admin Dashboard", expanded=True):
                    users_count = query("SELECT COUNT(*) as c FROM users", fetchone=True)["c"]
                    tx_count = query("SELECT COUNT(*) as c FROM transactions", fetchone=True)["c"]
                    st.metric("Total users", users_count)
                    st.metric("Total transactions", tx_count)
                    st.markdown("**Recent users**")
                    recent = query(
                        "SELECT username,display_name,email,is_admin,created_at "
                        "FROM users ORDER BY created_at DESC LIMIT 10", fetchall=True)
                    df = pd.DataFrame(recent) if recent else pd.DataFrame(
                        columns=["username","display_name","email","is_admin","created_at"])
                    st.dataframe(df, width=True)
