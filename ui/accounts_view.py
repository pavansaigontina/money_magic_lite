import streamlit as st
from core.accounts import get_accounts, add_account, update_account, delete_account

def show_accounts_view(user):
    st.header("🏦 Accounts")
    accounts = get_accounts()

    with st.expander("Add account"):
        with st.form("add_account_form"):
            name = st.text_input("Account name")
            atype = st.selectbox("Type", ["Debit","Credit"])
            notes = st.text_area("Notes (optional)")
            if st.form_submit_button("Add account"):
                if not name:
                    st.error("Name required")
                else:
                    try:
                        add_account(name.strip(), atype, notes.strip())
                        st.success("Account added")
                        st.rerun()
                    except Exception as e:
                        st.error(str(e))

    st.markdown("**Existing accounts**")
    if accounts:
        for a in accounts:
            with st.expander(f"{a['name']} ({a['type']})"):
                st.write(a.get('notes',''))
                c1,c2,c3 = st.columns([2,1,1])
                with c1:
                    new_name = st.text_input(f"name_{a['id']}", value=a['name'])
                with c2:
                    new_type = st.selectbox(f"type_{a['id']}", ["Debit","Credit"], index=0 if a['type']=="Debit" else 1)
                with c3:
                    if st.button("Save", key=f"save_acc_{a['id']}"):
                        update_account(a['id'], name=new_name.strip(), atype=new_type)
                        st.success("Saved")
                        st.rerun()
                if st.button("Delete account", key=f"del_acc_{a['id']}"):
                    try:
                        delete_account(a['id'])
                        st.success("Deleted")
                        st.rerun()
                    except Exception as e:
                        st.error(str(e))
    else:
        st.info("No accounts. Add one above.")
