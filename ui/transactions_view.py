import streamlit as st
import pandas as pd
from datetime import date, datetime
from core.accounts import get_accounts
from core.transactions import add_transaction, fetch_transactions, update_transaction_by_uuid, delete_transaction_by_uuid
from core.database import query
from core.balances import get_opening
from core.utils import MONTHS
import io
import plotly.express as px
import plotly.io as pio


def show_transactions_view(user):
    st.header("📜 Transactions")
    accounts = get_accounts(user["id"], user.get("is_admin", 0))
    account_names = [a['name'] for a in accounts]

    # Add Transaction
    with st.expander("➕ Add Transaction", expanded=False):
        with st.form("add_tx"):
            t_date = st.date_input("Date", value=date.today())
            if account_names:
                acc_choice = st.selectbox("Account", account_names)
            else:
                st.warning("No accounts — add one first.")
                acc_choice = None
            t_category = st.selectbox(
                "Category",
                [
                    "Food", "Transport", "Bills", "Shopping", "Rent", "Salary",
                    "Payment", "Investment", "Entertainment", "Health",
                    "Education", "Other"
                ],
            )
            t_description = st.text_input("Description", "")
            t_type = st.radio("Type", ["Expense", "Income"], horizontal=True)
            t_amount = st.number_input("Amount (₹)", min_value=0.0, step=10.0, format="%.2f")
            if st.form_submit_button("Add"):
                if not acc_choice:
                    st.error("Please add an account first.")
                elif t_amount <= 0:
                    st.error("Amount must be > 0")
                else:
                    aid = next((a['id'] for a in accounts if a['name'] == acc_choice), None)
                    add_transaction(t_date, aid, t_category, t_description, t_type, t_amount, user['id'])
                    st.success("Transaction added")
                    st.rerun()

    # Filters and listing
    current_month_index = datetime.now().month - 1
    selected_month = st.selectbox("Select Month", MONTHS, index=current_month_index, key="global_month_select")
    with st.expander("🔍 Filters", expanded=False):
        col1, col2, col3 = st.columns(3)
        with col1:
            default_start = date(datetime.now().year, current_month_index + 1, 1)
            min_date = st.date_input("Start date", value=default_start)
        with col2:
            default_end = date.today()
            max_date = st.date_input("End date", value=default_end)
        with col3:
            account_options = ["All"] + account_names
            account_filter = st.multiselect("Account", account_options, default=["All"])
            type_filter = st.multiselect("Type", ["All", "Expense", "Income"], default=["All"])

    account_ids = None
    if account_filter and "All" not in account_filter:
        account_ids = [a['id'] for a in accounts if a['name'] in account_filter]
    types = None
    if type_filter and "All" not in type_filter:
        types = [t for t in type_filter if t != "All"]

    tx_df = fetch_transactions(
        month_filter=selected_month,
        start_date=min_date,
        end_date=max_date,
        account_ids=account_ids,
        types=types,
        user_id=user["id"],
        is_admin=bool(user.get("is_admin")),
    )

    st.write(f"Showing {len(tx_df)} transactions")

    if not tx_df.empty:
        # Convert Date column to datetime.date
        if 'Date' in tx_df.columns:
            tx_df['Date'] = pd.to_datetime(tx_df['Date'], errors='coerce').dt.date

        edited = st.data_editor(
            tx_df,
            num_rows="dynamic",
            use_container_width=True,
            column_config={
                "Date": st.column_config.DateColumn("Date", format="YYYY-MM-DD"),
                "Account": st.column_config.Column("Account", disabled=True),
                "Category": st.column_config.TextColumn("Category"),
                "Description": st.column_config.TextColumn("Description"),
                "Type": st.column_config.SelectboxColumn("Type", options=["Expense", "Income"]),
                "Amount": st.column_config.NumberColumn("Amount", min_value=0.0, format="%.2f"),
                "Transaction_ID": st.column_config.Column("Transaction_ID", disabled=True),
            },
            key="tx_editor",
        )
        # Save edits
        if st.button("💾 Save edits"):
            try:
                new_ids = set(edited["Transaction_ID"].astype(str).tolist())
                old_ids = set(tx_df["Transaction_ID"].astype(str).tolist())
                deleted = old_ids - new_ids
                for did in deleted:
                    delete_transaction_by_uuid(did)

                for _, row in edited.iterrows():
                    txid = str(row.get("Transaction_ID", "") or "")
                    if not txid:
                        acc_name = row.get("Account")
                        aid = next((a['id'] for a in accounts if a['name'] == acc_name), None)
                        add_transaction(
                            pd.to_datetime(row["Date"]).date(),
                            aid,
                            row.get("Category", ""),
                            row.get("Description", ""),
                            row.get("Type", "Expense"),
                            float(row.get("Amount", 0.0)),
                            user['id'],
                        )
                    else:
                        updates = {
                            "date": pd.to_datetime(row["Date"]).date().isoformat(),
                            "amount": float(row.get("Amount", 0.0)),
                            "category": row.get("Category", ""),
                            "description": row.get("Description", ""),
                            "type": row.get("Type", "Expense"),
                        }
                        update_transaction_by_uuid(txid, updates)
                st.success("Saved changes")
                st.rerun()
            except Exception as e:
                st.error(str(e))

    # --- Summaries & charts ---
    # st.markdown("---")
    # st.header(f"💼 Account Summary — {selected_month}")
    # --- Account summary and visuals ---
    st.markdown("---")
    st.subheader(f"💼 Account Summary for {selected_month}")
    top_balance_viewer = st.empty()
    # Rebuild monthly data to include balances
    summary_rows = []
    debit_opening, credit_opening = 0.0, 0.0
    total_income_summary, total_spent_summary = 0.0, 0.0

    # Ensure we have the right columns
    if not tx_df.empty and "Account" in tx_df.columns and "Type" in tx_df.columns:
        for a in accounts:
            acc = a["name"]
            acc_type = a["type"]
            # opening = float(get_opening(selected_month, a["id"]) or 0.0)
            opening = float(get_opening(selected_month, a["id"], user["id"], user.get("is_admin", 0)))
            acc_data = tx_df[tx_df["Account"] == acc]

            # Compute totals
            income = float(acc_data[acc_data["Type"] == "Income"]["Amount"].sum()) if not acc_data.empty else 0.0
            expense = float(acc_data[acc_data["Type"] == "Expense"]["Amount"].sum()) if not acc_data.empty else 0.0

            if acc_type == "Debit":
                remaining = opening + income - expense
                debit_opening += opening
            else:  # Credit
                remaining = opening + expense - income
                credit_opening += opening

            summary_rows.append({
                "Account": acc,
                "Type": acc_type,
                "Opening Balance": opening,
                "Total Incoming (Payments)": income,
                "Total Spent": expense,
                "Remaining Balance": remaining
            })
            total_income_summary += income
            total_spent_summary += expense

    # Totals
    total_opening = debit_opening - credit_opening
    total_remaining = total_opening + total_income_summary - total_spent_summary
    try:
        summary_df = pd.DataFrame(summary_rows)
        debit_df = summary_df[summary_df["Type"] == "Debit"]
        credit_df = summary_df[summary_df["Type"] == "Credit"]

        # --- Debit section ---
        st.markdown("#### 🏦 Debit Accounts")
        if not debit_df.empty:
            st.dataframe(
                debit_df[
                    ["Account", "Type", "Opening Balance", "Total Incoming (Payments)", "Total Spent", "Remaining Balance"]
                ],
                use_container_width=True,
            )
        else:
            st.info("No debit accounts configured for this month.")

        total_debit_opening = float(debit_df["Opening Balance"].sum()) if not debit_df.empty else 0.0
        total_debit_remaining = float(debit_df["Remaining Balance"].sum()) if not debit_df.empty else 0.0
        total_debit_spent = float(debit_df["Total Spent"].sum()) if not debit_df.empty else 0.0
        total_debit_incoming = float(debit_df["Total Incoming (Payments)"].sum()) if not debit_df.empty else 0.0
        st.write(f"**Total Remaining Balance (Debit accounts):** ₹{total_debit_remaining:,.2f}")

        # --- Credit section ---
        st.markdown("#### 💳 Credit Cards")
        if not credit_df.empty:
            st.dataframe(
                credit_df[
                    ["Account", "Type", "Opening Balance", "Total Incoming (Payments)", "Total Spent", "Remaining Balance"]
                ],
                use_container_width=True,
            )
        else:
            st.info("No credit accounts configured for this month.")

        total_credit_opening = float(credit_df["Opening Balance"].sum()) if not credit_df.empty else 0.0
        total_credit_remaining = float(credit_df["Remaining Balance"].sum()) if not credit_df.empty else 0.0
        total_credit_spent = float(credit_df["Total Spent"].sum()) if not credit_df.empty else 0.0
        total_credit_incoming = float(credit_df["Total Incoming (Payments)"].sum()) if not credit_df.empty else 0.0
        st.write(f"**Total Spent (Credit accounts):** ₹{total_credit_spent:,.2f}")

        # --- Overall Totals ---
        st.markdown(f"#### 📊 Total (All Accounts) for {selected_month}")
        total_row = pd.DataFrame([
            {
                "Account": "Total (All Accounts)",
                "Opening Balance": total_opening,
                "Total Spent": total_spent_summary,
                "Total Incoming (Payments)": total_income_summary,
                "Remaining Balance": total_remaining,
            },
            {
                "Account": "Debit Summary",
                "Opening Balance": total_debit_opening,
                "Total Spent": total_debit_spent,
                "Total Incoming (Payments)": total_debit_incoming,
                "Remaining Balance": total_debit_remaining,
            },
            {
                "Account": "Credit Summary",
                "Opening Balance": total_credit_opening,
                "Total Spent": total_credit_spent,
                "Total Incoming (Payments)": total_credit_incoming,
                "Remaining Balance": total_credit_remaining,
            },
        ])
        st.dataframe(total_row, use_container_width=True)

        # --- Top-line balance display ---
        with top_balance_viewer:
            st.write(f"💰 Available Balance ({selected_month}): :green[₹{total_remaining:,.2f}]")
    except Exception as e:
        st.info("Please Add Transactions")
    
    # 🧩 2. ALL-MONTHS TOTAL BALANCE METRICS
    # st.markdown("---")
    # st.subheader("📅 Cumulative Balance (All Months)")

    # try:
    #     # fetch all data directly from DB
    #     all_tx_rows = query("""
    #         SELECT t.date as Date, a.name as Account, a.type as Type,
    #             t.category as Category, t.description as Description,
    #             t.type as TxType, t.amount as Amount
    #         FROM transactions t
    #         LEFT JOIN accounts a ON t.account_id = a.id
    #     """, fetchall=True)
    #     all_df = pd.DataFrame(all_tx_rows) if all_tx_rows else pd.DataFrame(
    #         columns=["Date","Account","Type","Category","Description","TxType","Amount"]
    #     )

    #     all_balances_rows = query("""
    #         SELECT b.month as Month, a.name as Account, a.type as Type, b.opening as Opening
    #         FROM balances b
    #         LEFT JOIN accounts a ON b.account_id = a.id
    #     """, fetchall=True)
    #     all_balances = pd.DataFrame(all_balances_rows) if all_balances_rows else pd.DataFrame(
    #         columns=["Month","Account","Type","Opening"]
    #     )

    #     total_rows = []
    #     for _, row in all_balances.iterrows():
    #         acc = row["Account"]
    #         acc_type = row["Type"]
    #         opening = float(row.get("Opening", 0.0))
    #         acc_data = all_df[all_df["Account"] == acc]
    #         income = float(acc_data[acc_data["TxType"] == "Income"]["Amount"].sum()) if not acc_data.empty else 0.0
    #         expense = float(acc_data[acc_data["TxType"] == "Expense"]["Amount"].sum()) if not acc_data.empty else 0.0
    #         remaining = (opening + income - expense) if acc_type == "Debit" else (opening + expense - income)
    #         total_rows.append({"Account": acc, "Type": acc_type, "Remaining": remaining})

    #     total_df = pd.DataFrame(total_rows)
    #     total_debit = total_df[total_df["Type"] == "Debit"]["Remaining"].sum() if not total_df.empty else 0.0
    #     total_credit = total_df[total_df["Type"] == "Credit"]["Remaining"].sum() if not total_df.empty else 0.0
    #     total_overall = total_debit - total_credit

    #     colA, colB, colC = st.columns(3)
    #     with colA:
    #         st.metric("💼 Total Debit Balance", f"₹{total_debit:,.2f}")
    #     with colB:
    #         st.metric("💳 Total Credit Outstanding", f"₹{total_credit:,.2f}")
    #     with colC:
    #         st.metric(
    #             "🧾 Net Worth (All Months)",
    #             f"₹{total_overall:,.2f}",
    #             delta=total_overall,
    #             delta_color="normal" if total_overall >= 0 else "inverse",
    #         )
    # except Exception as e:
    #     st.warning(f"⚠️ Unable to calculate total balance across all months: {e}")

    # 🧩 3. MONTHLY METRICS
    st.markdown("---")
    st.subheader("📈 Monthly Metrics")

    if not tx_df.empty and "Type" in tx_df.columns:
        total_income = tx_df[tx_df["Type"] == "Income"]["Amount"].sum()
        total_expense = tx_df[tx_df["Type"] == "Expense"]["Amount"].sum()
        net_flow = total_income - total_expense
        total_transactions = int(tx_df.shape[0])

        col_metrics1, col_metrics2, col_metrics3, col_metrics4 = st.columns(4)
        with col_metrics1:
            st.metric("Total Income", f"₹{total_income:,.2f}")
        with col_metrics2:
            st.metric("Total Expenses", f"₹{total_expense:,.2f}")
        with col_metrics3:
            st.metric("Net Flow", f"₹{net_flow:,.2f}", delta=net_flow, delta_color="normal" if net_flow >= 0 else "inverse")
        with col_metrics4:
            st.metric("Total Transactions", total_transactions)
    else:
        st.info("No transaction data to display monthly metrics.")

    st.markdown("### Charts")

    # ---- Safe chart section ----
    if not tx_df.empty and 'Type' in tx_df.columns and 'Amount' in tx_df.columns:
        exp_df = tx_df[tx_df['Type'] == 'Expense']
        if not exp_df.empty and exp_df['Amount'].sum() > 0 and 'Category' in exp_df.columns:
            cat_sums = exp_df.groupby('Category')['Amount'].sum().reset_index()
            fig1 = px.pie(cat_sums, values='Amount', names='Category',
                          title=f'Expenses by Category ({selected_month})', hole=0.4)
            st.plotly_chart(fig1, use_container_width=True)

        inc_total = tx_df[tx_df['Type'] == 'Income']['Amount'].sum() if 'Income' in tx_df['Type'].values else 0
        exp_total = tx_df[tx_df['Type'] == 'Expense']['Amount'].sum() if 'Expense' in tx_df['Type'].values else 0

        fig2 = px.bar(pd.DataFrame({'Type': ['Expense', 'Income'], 'Amount': [exp_total, inc_total]}),
                      x='Type', y='Amount', text='Amount',
                      title=f'Income vs Expense ({selected_month})')
        st.plotly_chart(fig2, use_container_width=True)

        if not summary_df.empty and 'Remaining' in summary_df.columns:
            fig3 = px.bar(summary_df, x='Account', y='Remaining', color='Type',
                          title=f'Account balances ({selected_month})', barmode='group')
            st.plotly_chart(fig3, use_container_width=True)
    else:
        st.info("No transactions to chart.")


    # Downloads
    st.markdown('---')
    st.header('⬇️ Downloads')
    try:
        csv_buf = io.StringIO()
        tx_df.to_csv(csv_buf, index=False)
        st.download_button(
            'Download filtered transactions (CSV)',
            data=csv_buf.getvalue().encode('utf-8'),
            file_name=f'filtered_transactions_{selected_month}.csv',
            mime='text/csv',
        )
        summ_buf = io.StringIO()
        summary_df.to_csv(summ_buf, index=False)
        st.download_button(
            'Download summary (CSV)',
            data=summ_buf.getvalue().encode('utf-8'),
            file_name=f'summary_{selected_month}.csv',
            mime='text/csv',
        )
        can_image = True
        try:
            pio.to_image(px.line(), format='png')
        except Exception:
            can_image = False
        if can_image and not tx_df.empty:
            if not tx_df[tx_df['Type'] == 'Expense'].empty:
                cat_sums = tx_df[tx_df['Type'] == 'Expense'].groupby('Category')['Amount'].sum().reset_index()
                fig = px.pie(cat_sums, values='Amount', names='Category',
                             title=f'Expenses by Category ({selected_month})', hole=0.4)
                png = pio.to_image(fig, format='png', scale=2)
                st.download_button(
                    'Download Expense-by-Category (PNG)',
                    data=png,
                    file_name=f'expenses_by_category_{selected_month}.png',
                    mime='image/png',
                )
            fig = px.bar(pd.DataFrame({'Type': ['Expense', 'Income'], 'Amount': [exp_total, inc_total]}),
                         x='Type', y='Amount', text='Amount',
                         title=f'Income vs Expense ({selected_month})')
            png = pio.to_image(fig, format='png', scale=2)
            st.download_button(
                'Download Income-vs-Expense (PNG)',
                data=png,
                file_name=f'income_vs_expense_{selected_month}.png',
                mime='image/png',
            )
    except Exception as e:
        st.warning(f"Download failed: {e}")
