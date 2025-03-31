import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import os
from fpdf import FPDF
from io import BytesIO
import locale

# Set locale for number formatting
try:
    locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
except:
    locale.setlocale(locale.LC_ALL, '')

# Helper function to parse numbers from strings
def parse_number(number_str):
    try:
        return float(number_str.replace(',', '').replace('$', ''))
    except ValueError:
        return 0

# Helper function to format numbers with commas
def format_number(value):
    try:
        if isinstance(value, (int, float)):
            # Format float with 2 decimals and comma separators, or integer with commas.
            return f"{value:,.2f}" if isinstance(value, float) else f"{value:,}"
        else:
            return str(value)
    except Exception:
        return str(value)

# In English no need for RTL processing; just return the text.
def process_text(text):
    return text

# Function to generate a PDF report with a formatted table
def save_to_pdf(df, params, chart_path, title="Investment Report"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Use default font Arial to avoid custom font issues
    header_font = ('Arial', 'B', 16)
    normal_font = ('Arial', '', 10)
    table_header_font = ('Arial', 'B', 12)

    # Report title
    pdf.set_font(*header_font)
    pdf.cell(0, 10, title, 0, 1, 'C')
    pdf.ln(5)

    # Investment details (each on a new line)
    pdf.set_font(*normal_font)
    for key, value in params.items():
        pdf.cell(0, 10, f"{key}: {value}", 0, 1)
    pdf.ln(5)

    # Add chart image if exists
    if os.path.exists(chart_path):
        pdf.image(chart_path, x=10, w=pdf.w - 20)
        pdf.ln(10)

    # Create a table header for the results
    pdf.set_font(*table_header_font)
    col_width = (pdf.w - 20) / len(df.columns)
    for col in df.columns:
        pdf.cell(col_width, 10, str(col), border=1, align='C')
    pdf.ln()

    # Table rows
    pdf.set_font(*normal_font)
    for _, row in df.iterrows():
        for col in df.columns:
            cell_value = row[col]
            if isinstance(cell_value, (int, float)):
                cell_value = format_number(cell_value)
            else:
                cell_value = str(cell_value)
            pdf.cell(col_width, 10, cell_value, border=1, align='C')
        pdf.ln()

    pdf_output = BytesIO()
    pdf_bytes = pdf.output(dest='S')
    if isinstance(pdf_bytes, str):
        pdf_bytes = pdf_bytes.encode('latin1')
    pdf_output.write(pdf_bytes)
    pdf_output.seek(0)
    return pdf_output

# Set up the page
st.set_page_config(page_title="Investment Calculator", layout="wide")
st.title("Investment Calculator")
st.markdown("### Advanced investment system with PDF reports, charts, and tables")

# Sidebar logo
if os.path.exists("Masor_logo.png"):
    st.sidebar.image("Masor_logo.png", width=200)
else:
    st.sidebar.write("Logo file 'Masor_logo.png' not found.")

# Choose calculator type: Basic or Advanced
calc_type = st.sidebar.radio("Select Calculator Type", ["Basic", "Advanced"])

# Use st.form to delay calculations until the user submits the form
with st.sidebar.form(key="input_form"):
    if calc_type == "Basic":
        st.subheader("Basic Investment Details")
        investment_input = st.text_input("Investment Amount ($):", value="100000")
        annual_net_income_input = st.text_input("Annual Net Income ($):", value="5000")
        years = st.number_input("Number of Years:", value=10, step=1)
        annual_yield_growth = st.number_input("Annual Yield Growth (%):", value=5.0, step=0.5)
    else:
        st.subheader("Advanced Investment Details")
        asset_cost_input = st.text_input("Property Cost ($):", value="200000")
        equity_input = st.text_input("Equity ($):", value="80000")
        bank_financing_input = st.text_input("Bank Financing ($):", value="120000")
        annual_interest_rate_input = st.text_input("Annual Interest Rate (%):", value="3.5")
        appreciation_rate_input = st.text_input("Annual Appreciation Rate (%):", value="4")
        expected_income_input = st.text_input("Expected Annual Income ($):", value="15000")
        investment_period = st.number_input("Investment Period (Years):", value=10, step=1)
    submit_button = st.form_submit_button(label="Calculate")

# Only run the calculations if the form is submitted
if submit_button:
    if calc_type == "Basic":
        # Convert inputs to numbers
        investment = parse_number(investment_input)
        annual_net_income = parse_number(annual_net_income_input)
        base_yield = (annual_net_income / investment * 100) if investment > 0 else 0

        # Prepare parameters for display and PDF
        params = {
            "Investment Amount": f"${format_number(investment)}",
            "Annual Net Income": f"${format_number(annual_net_income)}",
            "Annual Yield Growth": f"{annual_yield_growth}%",
            "Number of Years": years,
            "Base Yield": f"{base_yield:.2f}%"
        }

        results = []
        cumulative_value = investment
        for i in range(1, int(years) + 1):
            current_yield = base_yield * ((1 + annual_yield_growth / 100) ** (i - 1))
            expected_income = cumulative_value * (current_yield / 100)
            cumulative_value += expected_income
            results.append({
                "Year": i,
                "Yield (%)": round(current_yield, 2),
                "Expected Income ($)": round(expected_income, 2),
                "Cumulative Value ($)": round(cumulative_value, 2)
            })
        df = pd.DataFrame(results)

        st.markdown("### Basic Investment Results")
        st.dataframe(df)

        # Chart: Cumulative Value over Years
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.plot(df["Year"], df["Cumulative Value ($)"], marker='o', linewidth=2)
        ax.set_xlabel("Year")
        ax.set_ylabel("Cumulative Value ($)")
        ax.set_title(process_text("Investment Growth Over the Years"))
        ax.grid(True)
        st.pyplot(fig)

        chart_path = "temp_chart_basic.png"
        fig.savefig(chart_path, bbox_inches="tight")
        plt.close(fig)

        st.markdown("### Download Reports")
        pdf_data = save_to_pdf(df, params, chart_path, title="Basic Investment Report")
        st.download_button(
            label='Download PDF Report',
            data=pdf_data,
            file_name="investment_report_basic.pdf",
            mime="application/pdf"
        )
        csv_data = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Download CSV File",
            data=csv_data,
            file_name="investment_results_basic.csv",
            mime="text/csv"
        )

    else:
        # Convert inputs to numbers
        asset_cost = parse_number(asset_cost_input)
        equity = parse_number(equity_input)
        bank_financing = parse_number(bank_financing_input)
        try:
            annual_interest_rate = float(annual_interest_rate_input)
        except ValueError:
            annual_interest_rate = 0.0
        try:
            appreciation_rate = float(appreciation_rate_input)
        except ValueError:
            appreciation_rate = 0.0
        expected_income = parse_number(expected_income_input)
        period = investment_period

        params = {
            "Property Cost": f"${format_number(asset_cost)}",
            "Equity": f"${format_number(equity)}",
            "Bank Financing": f"${format_number(bank_financing)}",
            "Annual Interest Rate": f"{annual_interest_rate}%",
            "Annual Appreciation Rate": f"{appreciation_rate}%",
            "Expected Annual Income": f"${format_number(expected_income)}",
            "Investment Period": period
        }

        results_adv = []
        current_asset_value = asset_cost
        for year in range(1, int(period) + 1):
            interest_cost = bank_financing * annual_interest_rate / 100
            appreciation_value = current_asset_value * appreciation_rate / 100
            current_asset_value += appreciation_value
            net_cash_flow = expected_income - interest_cost
            total_return = net_cash_flow + appreciation_value
            roi = (total_return / equity * 100) if equity != 0 else 0

            results_adv.append({
                "Year": year,
                "Property Value ($)": round(current_asset_value, 2),
                "Interest Cost ($)": round(interest_cost, 2),
                "Expected Income ($)": round(expected_income, 2),
                "Appreciation ($)": round(appreciation_value, 2),
                "Annual ROI (%)": round(roi, 2)
            })
        df_adv = pd.DataFrame(results_adv)

        st.markdown("### Advanced Investment Results")
        st.dataframe(df_adv)

        # Chart: Property Value over the Years
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.plot(df_adv["Year"], df_adv["Property Value ($)"], marker='o', linewidth=2)
        ax.set_xlabel("Year")
        ax.set_ylabel("Property Value ($)")
        ax.set_title(process_text("Property Value Over the Years"))
        ax.grid(True)
        st.pyplot(fig)

        chart_path = "temp_chart_advanced.png"
        fig.savefig(chart_path, bbox_inches="tight")
        plt.close(fig)

        st.markdown("### Download Reports")
        pdf_data = save_to_pdf(df_adv, params, chart_path, title="Advanced Investment Report")
        st.download_button(
            label='Download PDF Report',
            data=pdf_data,
            file_name="investment_report_advanced.pdf",
            mime="application/pdf"
        )
        csv_data = df_adv.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Download CSV File",
            data=csv_data,
            file_name="investment_results_advanced.csv",
            mime="text/csv"
        )
