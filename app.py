import streamlit as st
import pandas as pd

st.set_page_config(page_title="AI Cost Optimization Advisor", layout="wide")

st.title("AI Cost Optimization Advisor")
st.write("Upload cloud cost data and get savings recommendations.")

uploaded_file = st.file_uploader("Upload a CSV file", type=["csv"])


def validate_dataframe(df: pd.DataFrame):
    required_columns = [
        "resource_id",
        "service",
        "monthly_cost",
        "cpu_utilization_percent",
        "last_access_days",
    ]

    missing_columns = [col for col in required_columns if col not in df.columns]
    return missing_columns


def analyze_costs(df: pd.DataFrame):
    findings = []

    # Make sure numeric fields are really numeric
    numeric_columns = ["monthly_cost", "cpu_utilization_percent", "last_access_days"]
    for col in numeric_columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Drop rows where critical numeric fields are invalid
    df = df.dropna(subset=numeric_columns)

    total_monthly_cost = df["monthly_cost"].sum()

    # Rule 1: Low CPU + high cost
    low_cpu = df[
        (df["cpu_utilization_percent"] < 15)
        & (df["monthly_cost"] > 100)
        & (df["service"].isin(["EC2", "EKS", "RDS"]))
    ]

    for _, row in low_cpu.iterrows():
        findings.append(
            {
                "resource_id": row["resource_id"],
                "issue": "Low utilization, high cost",
                "recommendation": f"Review rightsizing or shutting down {row['resource_id']}.",
                "monthly_cost": row["monthly_cost"],
                "estimated_savings": round(row["monthly_cost"] * 0.30, 2),
            }
        )

    # Rule 2: Old storage not accessed recently
    stale_storage = df[
        (df["service"].isin(["S3", "EBS"]))
        & (df["last_access_days"] > 90)
        & (df["monthly_cost"] > 50)
    ]

    for _, row in stale_storage.iterrows():
        findings.append(
            {
                "resource_id": row["resource_id"],
                "issue": "Stale storage",
                "recommendation": f"Consider archiving, tiering, or deleting unused data for {row['resource_id']}.",
                "monthly_cost": row["monthly_cost"],
                "estimated_savings": round(row["monthly_cost"] * 0.40, 2),
            }
        )

    findings_df = pd.DataFrame(findings)

    if findings_df.empty:
        total_estimated_savings = 0
    else:
        total_estimated_savings = findings_df["estimated_savings"].sum()

    return findings_df, total_monthly_cost, total_estimated_savings


if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file)

        missing_columns = validate_dataframe(df)
        if missing_columns:
            st.error(
                "Your CSV is missing these required columns: "
                + ", ".join(missing_columns)
            )
        else:
            st.subheader("Uploaded Data")
            st.dataframe(df, use_container_width=True)

            findings_df, total_cost, estimated_savings = analyze_costs(df)

            col1, col2 = st.columns(2)
            col1.metric("Total Monthly Cost", f"${total_cost:,.2f}")
            col2.metric("Estimated Savings Opportunity", f"${estimated_savings:,.2f}")

            st.subheader("Optimization Findings")

            if findings_df.empty:
                st.success("No major optimization issues found.")
            else:
                st.dataframe(findings_df, use_container_width=True)

                st.subheader("Executive Summary")

                summary = f"""
Total monthly cloud spend is approximately ${total_cost:,.2f}.

The analysis identified {len(findings_df)} optimization opportunities with an estimated monthly savings of ${estimated_savings:,.2f}.

The biggest opportunities are related to:
- underutilized compute resources
- stale storage with ongoing cost
- development or QA resources that may be oversized
"""
                st.write(summary)

    except Exception as e:
        st.error(f"Error reading or analyzing the CSV: {e}")

else:
    st.info("Upload the sample_cost_data.csv file to get started.")