import streamlit as st
import pandas as pd

st.set_page_config(page_title="Deductible + Coinsurance Calculator", layout="wide")

st.title("Deductible + Coinsurance Calculator")

st.markdown("Enter the remaining deductible, coinsurance, and service lines.")

# Sidebar inputs
with st.sidebar:
    st.header("Settings")
    ded_remaining = st.number_input(
        "Remaining deductible",
        min_value=0.0,
        value=90.0,
        step=1.0,
        format="%.2f",
    )

    coinsurance_pct = st.number_input(
        "Coinsurance %",
        min_value=0.0,
        max_value=100.0,
        value=50.0,
        step=1.0,
        format="%.2f",
    )

    processing_order = st.radio(
        "Processing order",
        options=["Entered order", "Lowest rate first", "Highest rate first"],
        index=0,
    )

# Starter data
default_data = pd.DataFrame(
    [
        {"Date": "2026-03-18", "Service": "Group", "Rate": 125.00},
        {"Date": "2026-03-18", "Service": "IT", "Rate": 260.00},
    ]
)

edited_df = st.data_editor(
    default_data,
    num_rows="dynamic",
    use_container_width=True,
    column_config={
        "Date": st.column_config.TextColumn("Date"),
        "Service": st.column_config.TextColumn("Service"),
        "Rate": st.column_config.NumberColumn("Rate", min_value=0.0, format="%.2f"),
    },
)

def sort_services(df: pd.DataFrame, mode: str) -> pd.DataFrame:
    df = df.copy()
    df["_original_order"] = range(len(df))

    if mode == "Lowest rate first":
        df = df.sort_values(by=["Rate", "_original_order"], ascending=[True, True])
    elif mode == "Highest rate first":
        df = df.sort_values(by=["Rate", "_original_order"], ascending=[False, True])
    else:
        df = df.sort_values(by="_original_order", ascending=True)

    return df.reset_index(drop=True)

def calculate_patient_responsibility(df: pd.DataFrame, deductible_remaining: float, coinsurance_percent: float) -> pd.DataFrame:
    results = []
    current_ded = deductible_remaining
    coinsurance_decimal = coinsurance_percent / 100

    for _, row in df.iterrows():
        rate = float(row["Rate"]) if pd.notna(row["Rate"]) else 0.0
        ded_before = current_ded
        ded_applied = min(current_ded, rate)
        remaining_after_ded = rate - ded_applied
        coinsurance_amount = remaining_after_ded * coinsurance_decimal
        patient_total = ded_applied + coinsurance_amount
        current_ded -= ded_applied

        results.append({
            "Date": row.get("Date", ""),
            "Service": row.get("Service", ""),
            "Rate": round(rate, 2),
            "Ded Before": round(ded_before, 2),
            "Ded Applied": round(ded_applied, 2),
            "Ded After": round(current_ded, 2),
            "Remaining After Ded": round(remaining_after_ded, 2),
            "Coinsurance %": round(coinsurance_percent, 2),
            "Coinsurance Amt": round(coinsurance_amount, 2),
            "Patient Resp": round(patient_total, 2),
        })

    return pd.DataFrame(results)

if st.button("Calculate"):
    clean_df = edited_df.copy()

    # Basic cleanup
    clean_df = clean_df.dropna(subset=["Rate"])
    clean_df = clean_df[clean_df["Rate"] >= 0]

    if clean_df.empty:
        st.warning("Add at least one service line with a valid rate.")
    else:
        sorted_df = sort_services(clean_df, processing_order)
        result_df = calculate_patient_responsibility(
            sorted_df,
            ded_remaining,
            coinsurance_pct,
        )

        st.subheader("Results")
        st.dataframe(result_df, use_container_width=True)

        total_rate = result_df["Rate"].sum()
        total_ded_applied = result_df["Ded Applied"].sum()
        total_coinsurance = result_df["Coinsurance Amt"].sum()
        total_patient_resp = result_df["Patient Resp"].sum()

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Charges", f"${total_rate:,.2f}")
        c2.metric("Total Ded Applied", f"${total_ded_applied:,.2f}")
        c3.metric("Total Coinsurance", f"${total_coinsurance:,.2f}")
        c4.metric("Total Patient Resp", f"${total_patient_resp:,.2f}")

        st.subheader("Line-by-line explanation")
        for _, row in result_df.iterrows():
            st.write(
                f"**{row['Service']}** ({row['Date']}): "
                f"Rate ${row['Rate']:.2f} | "
                f"Ded before ${row['Ded Before']:.2f} | "
                f"Ded applied ${row['Ded Applied']:.2f} | "
                f"Remaining after ded ${row['Remaining After Ded']:.2f} | "
                f"Coinsurance ${row['Coinsurance Amt']:.2f} | "
                f"Patient responsibility **${row['Patient Resp']:.2f}**"
            )
