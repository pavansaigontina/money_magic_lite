import streamlit as st
from core.auth import create_user, verify_user, update_user_details, get_user_by_id

def sidebar_user_section():
    st.sidebar.header("👤 User")
    if "user" not in st.session_state:
        st.session_state.user = None
        st.session_state.logged_in = False

    if not st.session_state.logged_in:
        mode = st.sidebar.radio("Select", ["Login", "Register"])
        if mode == "Register":
            with st.sidebar.form("register_form"):
                u = st.text_input("Username")
                dn = st.text_input("Display name (optional)")
                em = st.text_input("Email (optional)")
                p = st.text_input("Password", type="password")
                p2 = st.text_input("Confirm Password", type="password")
                if st.form_submit_button("Register"):
                    if not u or not p:
                        st.error("Username and password are required")
                    elif p != p2:
                        st.error("Passwords do not match")
                    else:
                        ok, info = create_user(u.strip(), p, dn.strip(), em.strip())
                        if ok:
                            st.success("Registered. Please login.")
                            if info:
                                st.info("You are the first user and have been made admin.")
                        else:
                            st.error(f"Registration failed: {info}")
        else:
            with st.sidebar.form("login_form"):
                u = st.text_input("Username")
                p = st.text_input("Password", type="password")
                if st.form_submit_button("Login"):
                    ok, info = verify_user(u.strip(), p)
                    if ok:
                        st.session_state.user = info
                        st.session_state.logged_in = True
                        st.rerun()
                    else:
                        st.error(info)
        return None
    else:
        user = st.session_state.user
        st.sidebar.write(f"Logged in as **{user.get('display_name') or user.get('username')}**")
        if st.sidebar.button("Logout"):
            st.session_state.user = None
            st.session_state.logged_in = False
            st.rerun()
        st.sidebar.markdown("---")
        st.sidebar.subheader("Edit Profile")
        with st.sidebar.form("edit_profile"):
            name = st.text_input("Display name", value=user.get('display_name',''))
            email = st.text_input("Email", value=user.get('email',''))
            new_pw = st.text_input("New password (optional)", type="password")
            if st.form_submit_button("Save"):
                update_user_details(user["id"], name, email, new_pw or None)
                st.success("Profile updated.")
                st.session_state.user = get_user_by_id(user["id"])
        return st.session_state.user
