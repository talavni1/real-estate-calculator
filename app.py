import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from PIL import Image
import os
from fpdf import FPDF
from io import BytesIO

# פונקציות עזר
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

# פונקציה מתקדמת ליצירת דו"ח PDF
def save_to_pdf(df, params, chart_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # הוספת פונט TrueType התומך בעברית
    font_path = "DejaVuSans.ttf"
    if os.path.exists(font_path):
        pdf.add_font('DejaVu', '', font_path, uni=True)
        header_font = ('DejaVu', 'B', 16)
        normal_font = ('DejaVu', '', 10)
        table_header_font = ('DejaVu', 'B', 12)
    else:
        st.error("קובץ הפונט DejaVuSans.ttf לא נמצא. יש להוריד אותו ולהניחו באותה תיקייה.")
        header_font = ('Arial', 'B', 16)
        normal_font = ('Arial', '', 10)
        table_header_font = ('Arial', 'B', 12)

    # כותרת הדוח
    pdf.set_font(*header_font)
    pdf.cell(0, 10, 'דוח השקעות – Masor Investment Report', 0, 1, 'C')
    pdf.ln(5)

    # פרטי ההשקעה
    pdf.set_font(*normal_font)
    details = (
        f"סכום השקעה: {params['investment']}$\n"
        f"תשואה נטו בסיסית: {params['base_yield']:.2f}%\n"
        f"גידול תשואה שנתי: {params['annual_value_increase']}%\n"
        f"שנים: {params['years']}\n"
    )
    pdf.multi_cell(0, 8, details)
    pdf.ln(5)

    # הוספת גרף מהדו"ח (תמונה)
    if os.path.exists(chart_path):
        pdf.image(chart_path, x=10, w=pdf.w - 20)
        pdf.ln(10)

    # הוספת טבלת תוצאות
    pdf.set_font(*table_header_font)
    pdf.cell(0, 10, 'טבלת תוצאות:', 0, 1)
    pdf.set_font(*normal_font)
    for _, row in df.iterrows():
        line = f"שנה: {int(row['Year'])}, תשואה: {row['Yield (%)']:.2f}%, הכנסה שנתית: {row['Expected Income ($)']:.2f}$, ערך מצטבר: {row['Cumulative Value ($)']:.2f}$"
        pdf.cell(0, 8, line, 0, 1)

    # שמירת הדו"ח בזיכרון (BytesIO)
    pdf_output = BytesIO()
    pdf_bytes = pdf.output(dest='S')
    if isinstance(pdf_bytes, str):
        pdf_bytes = pdf_bytes.encode('latin1')
    pdf_output.write(pdf_bytes)
    pdf_output.seek(0)
    return pdf_output

# קביעת הגדרות העמוד
st.set_page_config(page_title="Masor Investment Calculator", layout="wide")
st.title("מחשבון השקעות – Masor Investment Calculator")
st.markdown("### מערכת השקעות מתקדמת עם דוחות PDF, גרפים וטבלאות")

# הצגת הלוגו בסרגל הצדדי
if os.path.exists("Masor_logo.png"):
    st.sidebar.image("Masor_logo.png", width=200)
else:
    st.sidebar.write("קובץ הלוגו 'Masor_logo.png' לא נמצא.")

st.sidebar.markdown("### הזן את פרטי ההשקעה")

# חלוקה לעמודות לקבלת קלט מהמשתמש בסרגל הצדדי
col1, col2 = st.sidebar.columns(2)
with col1:
    investment = st.number_input("סכום השקעה ($):", value=100000, step=1000)
    annual_net_income = st.number_input("תשואה נטו שנתית ($):", value=5000, step=100)
    annual_value_increase = st.number_input("גידול ערך שנתי ($):", value=2000, step=100)
with col2:
    years = st.number_input("מספר שנים:", value=10, step=1)
    equity_invested = st.number_input("הון מושקע ($):", value=20000, step=1000)
    financing_percentage = st.number_input("אחוז מימון (%):", value=70, step=1)

annual_interest_rate = st.number_input("ריבית שנתית (%):", value=5.0, step=0.5)
financing_years = st.number_input("מספר שנות מימון:", value=5, step=1)

params = {
    "investment": investment,
    "annual_net_income": annual_net_income,
    "annual_value_increase": annual_value_increase,
    "years": years,
    "equity_invested": equity_invested,
    "financing_percentage": financing_percentage,
    "annual_interest_rate": annual_interest_rate,
    "financing_years": financing_years
}

# חישוב נתוני ההשקעה – דוגמה פשוטה
results = []
for i in range(1, int(years) + 1):
    value = investment + i * (annual_net_income + annual_value_increase)
    results.append({"Year": i, "Value": value})
df = pd.DataFrame(results)

st.markdown("### תוצאות ההשקעה")
st.dataframe(df)

# יצירת גרף ההשקעה
fig, ax = plt.subplots(figsize=(8, 4))
ax.plot(df["Year"], df["Value"], marker='o', color='blue', linewidth=2)
ax.set_xlabel("שנה")
ax.set_ylabel("ערך ההשקעה ($)")
ax.set_title("צמיחת ההשקעה לאורך השנים")
ax.grid(True)
st.pyplot(fig)

# שמירת הגרף כתמונה זמנית עבור הדוח
chart_path = "temp_chart.png"
fig.savefig(chart_path, bbox_inches="tight")
plt.close(fig)

st.markdown("### הורדת דוחות")
pdf_data = save_to_pdf(df, params, chart_path)
st.download_button(
    label='הורד דו"ח PDF',
    data=pdf_data,
    file_name="investment_report.pdf",
    mime="application/pdf"
)

csv_data = df.to_csv(index=False).encode('utf-8')
st.download_button(
    label="הורד קובץ CSV",
    data=csv_data,
    file_name="investment_results.csv",
    mime="text/csv"
)

st.markdown("### הערות")
st.markdown("""
- המחשבון משתמש בנתונים שהוזנו לצורך חישוב צמיחת ההשקעה.
- ניתן להתאים את הנוסחאות והעיצוב בהתאם לצרכים ספציפיים.
- הדוח ב-PDF כולל את פרטי ההשקעה, גרף וטבלת תוצאות.
""")
