import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from PIL import Image
import os
from fpdf import FPDF
from io import BytesIO
import locale

# Set locale for number formatting
try:
    locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
except:
    locale.setlocale(locale.LC_ALL, '')

# Helper functions
def parse_number(number_str):
    try:
        return float(number_str.replace(',', '').replace('$', ''))
    except ValueError:
        return 0

def format_number(value):
    if isinstance(value, (int, float)):
        return locale.format_string("%.0f", value, grouping=True)
    try:
        value = value.replace(',', '')
        return locale.format_string("%.0f", float(value), grouping=True)
    except ValueError:
        return value

# In English we don't need RTL processing, so just return the text as is.
def process_text(text):
    return text

# Function to generate a PDF report with investment details
def save_to_pdf(df, params, chart_path, title="Investment Report"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    font_path = "DejaVuSans.ttf"
    try:
        if os.path.exists(font_path):
            pdf.add_font('DejaVu', '', font_path, uni=True)
            header_font = ('DejaVu', 'B', 16)
            normal_font = ('DejaVu', '', 10)
            table_header_font = ('DejaVu', 'B', 12)
        else:
            st.error("Font file DejaVuSans.ttf not found. Please download it and place it in the same folder.")
            header_font = ('Arial', 'B', 16)
            normal_font = ('Arial', '', 10)
            table_header_font = ('Arial', 'B', 12)
    except Exception as e:
        st.error(f"Error loading DejaVu font: {e}. Using default font.")
        header_font = ('Arial', 'B', 16)
        normal_font = ('Arial', '', 10)
        table_header_font = ('Arial', 'B', 12)

    # Report title
    pdf.set_font(*header_font)
    pdf.cell(0, 10, title, 0, 1, 'C')
    pdf.ln(5)

    # Investment details
    pdf.set_font(*normal_font)
    details = ""
    for key, value in params.items():
        details += f"{key}: {value}\n"
    pdf.multi_cell(0, 8, details)
    pdf.ln(5)

    # Add chart image if exists
    if os.path.exists(chart_path):
        pdf.image(chart_path, x=10, w=pdf.w - 20)
        pdf.ln(10)

    # Add results table
    pdf.set_font(*table_header_font)
    pdf.cell(0, 10, 'Results Table:', 0, 1)
    pdf.set_font(*normal_font)
    for _, row in df.iterrows():
        line = ""
        for col in df.columns:
            line += f"{col}: {row[col]} | "
        pdf.cell(0, 8, line, 0, 1)

    # Save PDF to memory
    pdf_output = BytesIO()
    pdf_bytes = pdf.output(dest='S')
    if isinstance(pdf_bytes, str):
        pdf_bytes = pdf_bytes.encode('latin1')
    pdf_output.write(pdf_bytes)
    pdf_output.seek(0)
    return pdf_output

# Page configuration and title
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

if calc_type == "Basic":
    st.sidebar.markdown("### Basic Investment Details")
    investment_input = st.sidebar.text_input("Investment Amount ($):", value="100000")
    annual_net_income_input = st.sidebar.text_input("Annual Net Income ($):", value="5000")
    years = st.sidebar.number_input("Number of Years:", value=10, step=1)
    annual_yield_growth = st.sidebar.number_input("Annual Yield Growth (%):", value=5.0, step=0.5)

    # Convert inputs and calculate base yield
    investment = parse_number(investment_input)
    annual_net_income = parse_number(annual_net_income_input)
    base_yield = (annual_net_income / investment * 100) if investment > 0 else 0

    params = {
        "Investment Amount": f"${investment}",
        "Annual Net Income": f"${annual_net_income}",
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

    # Chart: Cumulative Value over the Years
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

else:  # Advanced calculator
    st.sidebar.markdown("### Advanced Investment Details")
    asset_cost_input = st.sidebar.text_input("Property Cost ($):", value="200000")
    equity_input = st.sidebar.text_input("Equity ($):", value="80000")
    bank_financing_input = st.sidebar.text_input("Bank Financing ($):", value="120000")
    annual_interest_rate_input = st.sidebar.text_input("Annual Interest Rate (%):", value="3.5")
    appreciation_rate_input = st.sidebar.text_input("Annual Appreciation Rate (%):", value="4")
    expected_income_input = st.sidebar.text_input("Expected Annual Income ($):", value="15000")
    investment_period = st.sidebar.number_input("Investment Period (Years):", value=10, step=1)

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
        "Property Cost": f"${asset_cost}",
        "Equity": f"${equity}",
        "Bank Financing": f"${bank_financing}",
        "Annual Interest Rate": f"{annual_interest_rate}%",
        "Annual Appreciation Rate": f"{appreciation_rate}%",
        "Expected Annual Income": f"${expected_income}",
        "Investment Period": period
    }

    results_adv = []
    current_asset_value = asset_cost
    for year in range(1, int(period) + 1):
        # Calculate annual interest cost on bank financing
        interest_cost = bank_financing * annual_interest_rate / 100
        # Calculate property appreciation
        appreciation_value = current_asset_value * appreciation_rate / 100
        current_asset_value += appreciation_value
        # Net cash flow: expected income minus interest cost
        net_cash_flow = expected_income - interest_cost
        # Annual ROI: net cash flow plus appreciation relative to equity
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

st.markdown("### Notes")
if calc_type == "Basic":
    st.markdown("""
    - This calculator computes the compounded annual yield where the base yield is calculated from net income divided by the investment.
    - Each year the yield grows by the specified annual percentage.
    - The PDF report includes investment details, a chart, and a results table.
    """)
else:
    st.markdown("""
    - This advanced calculator includes property cost, equity, bank financing, interest rate, appreciation rate, and expected annual income.
    - Each year, the calculator computes interest cost, property appreciation, and net cash flow.
    - The PDF report includes investment details, a chart, and a results table.
    """)
