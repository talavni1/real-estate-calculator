import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from PIL import Image
import os
from fpdf import FPDF
from io import BytesIO
from streamlit.components.v1 import html

def parse_number(number_str):
    try:
        return float(number_str.replace(',', '').replace('$', ''))
    except ValueError:
        return 0

def format_number(value):
    if isinstance(value, (int, float)):
        return f'{value:,.0f}'
    try:
        value = value.replace(',', '')
        return f'{int(value):,}'
    except ValueError:
        return value

def save_to_pdf(df, investment, annual_net_income, annual_value_increase, years, equity_invested, financing_percentage, annual_interest_rate, financing_years):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, 'Masor Investment Report', 0, 1, 'C')
    pdf.ln(10)

    pdf.set_font('Arial', '', 10)
    pdf.multi_cell(0, 10, f"Total Investment Amount: ${investment:,.0f}\n"
                          f"Annual Net Income: ${annual_net_income:,.0f}\n"
                          f"Annual Property Value Increase: {annual_value_increase}%\n"
                          f"Number of Years: {years}\n"
                          f"Equity Invested: ${equity_invested:,.0f}\n"
                          f"Financing Percentage: {financing_percentage}%\n"
                          f"Annual Interest Rate: {annual_interest_rate}%\n"
                          f"Financing Period (Years): {financing_years}\n")

    pdf.ln(5)

    years_list = df['Year'].astype(int)
    net_roi_values = df['Net ROI (%)'].str.replace('%', '').astype(float)

    plt.figure(figsize=(6, 4))
    plt.plot(years_list, net_roi_values, marker='o', color='blue', linestyle='-', linewidth=2)
    plt.title('Net ROI Over Time')
    plt.xlabel('Year')
    plt.ylabel('Net ROI (%)')
    plt.grid(True)

    temp_image_path = 'temp_graph.png'
    plt.savefig(temp_image_path, bbox_inches='tight')
    plt.close()

    pdf.ln(5)

    if os.path.exists(temp_image_path):
        pdf.image(temp_image_path, x=10, y=90, w=180)
        os.remove(temp_image_path)

    pdf.ln(10)
    pdf.add_page()  # ✅ Moving table to a new page

    pdf.set_font('Arial', 'B', 8)
    headers = ['Year', 'Property Value ($)', 'Total Net Income ($)', 'Total Investment Value ($)', 'Equity Multiple', 'Net ROI (%)']
    col_widths = [15, 35, 35, 35, 30, 25]

    for i, header in enumerate(headers):
        pdf.cell(col_widths[i], 10, header, 1, 0, 'C')
    pdf.ln()

    pdf.set_font('Arial', '', 7)

    for row in df.values.tolist():
        if pdf.get_y() > 250:
            pdf.add_page()
            for i, header in enumerate(headers):
                pdf.cell(col_widths[i], 10, header, 1, 0, 'C')
            pdf.ln()

        for i, item in enumerate(row):
            pdf.cell(col_widths[i], 10, str(item), 1, 0, 'C')
        pdf.ln()

    pdf_file = BytesIO()
    pdf_file.write(pdf.output(dest='S').encode('latin1'))
    pdf_file.seek(0)

    return pdf_file

def calculate_investment(investment, annual_net_income, annual_value_increase, years, equity_invested, financing_percentage, annual_interest_rate, financing_years):
    years_list = np.arange(1, years + 1)
    investment_value = investment
    total_net_income = 0
    financing_amount = investment * (financing_percentage / 100)
    annual_financing_payment = financing_amount * (annual_interest_rate / 100)

    data = []

    for year in years_list:
        annual_value_increase_amount = investment_value * (annual_value_increase / 100)
        investment_value += annual_value_increase_amount
        total_net_income += annual_net_income

        total_payment = annual_financing_payment * min(year, financing_years)
        total_value = investment_value + total_net_income - total_payment
        equity_multiple = total_value / equity_invested if equity_invested > 0 else None
        net_roi = ((total_value - investment) / investment) * 100

        data.append([year, f"${investment_value:,.2f}", f"${total_net_income:,.2f}",
                     f"${total_value:,.2f}", f"{equity_multiple:.2f}" if equity_multiple else 'N/A',
                     f"{net_roi:.2f}%"])

    df = pd.DataFrame(data, columns=[
        'Year', 'Property Value ($)', 'Total Net Income ($)', 'Total Investment Value ($)', 'Equity Multiple', 'Net ROI (%)'
    ])

    return df

st.title('Masor Investment Calculator')

investment = st.number_input('Total Investment Amount ($)', value=500000.0)
annual_net_income = st.number_input('Annual Net Income ($)', value=40000.0)
equity_invested = st.number_input('Equity Invested ($)', value=200000.0)
annual_value_increase = st.number_input('Annual Property Value Increase (%)', value=3.0)
years = st.number_input('Number of Years', value=10)
financing_percentage = st.number_input('Financing Percentage (%)', value=50.0)
annual_interest_rate = st.number_input('Annual Interest Rate (%)', value=5.0)
financing_years = st.number_input('Financing Period (Years)', value=5)

if st.button('Calculate'):
    df = calculate_investment(investment, annual_net_income, annual_value_increase, years, equity_invested, financing_percentage, annual_interest_rate, financing_years)

    if df is not None:
        st.write("### 📊 Investment Growth Table")
        st.write(df)

        pdf_file = save_to_pdf(df, investment, annual_net_income, annual_value_increase, years, equity_invested, financing_percentage, annual_interest_rate, financing_years)

        if pdf_file:
            st.download_button(label="📄 Download PDF Report", data=pdf_file, file_name="Investment_Report.pdf", mime="application/pdf")
