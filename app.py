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

    # כותרת הדוח
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, 'Masor Investment Report', 0, 1, 'C')
    pdf.ln(10)

    # פרטי ההשקעה
    pdf.set_font('Arial', '', 10)
    pdf.multi_cell(0, 10, f"""
Investment Amount: {investment}
Annual Net Income: {annual_net_income}
Annual Value Increase: {annual_value_increase}
Years: {years}
Equity Invested: {equity_invested}
Financing Percentage: {financing_percentage}%
Annual Interest Rate: {annual_interest_rate}%
Financing Years: {financing_years}
""")
    pdf.ln(10)

    # טבלת תוצאות
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, 'Results Table:', 0, 1)
    pdf.set_font('Arial', '', 10)
    for i in range(len(df)):
        row = df.iloc[i]
        line = ', '.join([f'{col}: {row[col]}' for col in df.columns])
        pdf.cell(0, 10, line, 0, 1)

    # שמירת הפלט לקובץ בזיכרון (BytesIO)
    pdf_output = BytesIO()
    pdf_bytes = pdf.output(dest='S')
    if isinstance(pdf_bytes, str):
        pdf_bytes = pdf_bytes.encode('latin1')
    pdf_output.write(pdf_bytes)
    pdf_output.seek(0)
    
    return pdf_output


# קוד האפליקציה הראשית

st.title("Masor Investment Calculator")

# הצגת הלוגו – אם הקובץ 'Masor_logo.png' נמצא בתיקייה
if os.path.exists("Masor_logo.png"):
    st.image("Masor_logo.png", width=200)
else:
    st.write("Logo file 'Masor_logo.png' not found.")

# קלט מהמשתמש
investment = st.number_input("Enter investment amount:", value=100000)
annual_net_income = st.number_input("Enter annual net income:", value=5000)
annual_value_increase = st.number_input("Enter annual value increase:", value=2000)
years = st.number_input("Enter number of years:", value=10)
equity_invested = st.number_input("Enter equity invested:", value=20000)
financing_percentage = st.number_input("Enter financing percentage:", value=70)
annual_interest_rate = st.number_input("Enter annual interest rate (in %):", value=5.0)
financing_years = st.number_input("Enter financing years:", value=5)

# יצירת DataFrame לדוגמה
data = {
    "Year": list(range(1, years+1)),
    "Value": [investment + i * (annual_net_income + annual_value_increase) for i in range(years)]
}
df = pd.DataFrame(data)

st.write("### Investment Results")
st.dataframe(df)

# הצגת גרף
fig, ax = plt.subplots()
ax.plot(df["Year"], df["Value"], marker='o')
ax.set_xlabel("Year")
ax.set_ylabel("Value")
ax.set_title("Investment Growth")
st.pyplot(fig)

# יצירת דוח PDF והצגת כפתור להורדה
pdf_data = save_to_pdf(df, investment, annual_net_income, annual_value_increase, years, equity_invested, financing_percentage, annual_interest_rate, financing_years)
st.download_button(
    label="Download PDF Report",
    data=pdf_data,
    file_name="investment_report.pdf",
    mime="application/pdf"
)
