import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from PIL import Image
import os
from fpdf import FPDF
from io import BytesIO
import arabic_reshaper
from bidi.algorithm import get_display
import locale

# הגדרת locale לעיצוב מספרים
try:
    locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
except:
    locale.setlocale(locale.LC_ALL, '')

# פונקציות עזר
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

# פונקציה לעיבוד טקסט בעברית (אם נדרש בגרף)
def process_hebrew_text(text):
    reshaped_text = arabic_reshaper.reshape(text)
    bidi_text = get_display(reshaped_text)
    return bidi_text

# פונקציה ליצירת דו"ח PDF משודרג עם תמיכה בעברית
def save_to_pdf(df, params, chart_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # הוספת פונט TrueType התומך בעברית – ודא שקובץ DejaVuSans.ttf נמצא בתיקייה
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

    # כותרת הדוח – ניתן לעבד טקסט בעברית אם נדרש
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
        line = (
            f"שנה: {int(row['Year'])}, "
            f"תשואה: {row['Yield (%)']:.2f}%, "
            f"הכנסה שנתית: {row['Expected Income ($)']:.2f}$, "
            f"ערך מצטבר: {row['Cumulative Value ($)']:.2f}$"
        )
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

# קלט מהמשתמש – באמצעות סרגל צדדי
col1, col2 = st.sidebar.columns(2)
with col1:
    investment_input = st.text_input("סכום השקעה ($):", value="100000")
    annual_net_income_input = st.text_input("הכנסה נטו שנתית ($):", value="5000")
with col2:
    years = st.number_input("מספר שנים:", value=10, step=1)
    annual_value_increase = st.number_input("גידול תשואה שנתי (%):", value=5.0, step=0.5)

# עיצוב קלט מספרי עם פסיקים (לדוגמה, עבור סכום השקעה)
investment = parse_number(investment_input)
annual_net_income = parse_number(annual_net_income_input)

# חישוב תשואה נטו בסיסית כאחוז – הכנסה נטו חלקי השקעה
base_yield = (annual_net_income / investment * 100) if investment > 0 else 0

# עדכון פרמטרים במילון
params = {
    "investment": investment,
    "annual_net_income": annual_net_income,
    "annual_value_increase": annual_value_increase,
    "years": years,
    "base_yield": base_yield
}

# חישוב נתוני ההשקעה – עם צמיחה מצרפית
results = []
cumulative_value = investment
for i in range(1, int(years) + 1):
    current_yield = base_yield * ((1 + annual_value_increase/100) ** (i - 1))
    expected_income = cumulative_value * (current_yield / 100)
    cumulative_value = cumulative_value + expected_income
    results.append({
        "Year": i,
        "Yield (%)": current_yield,
        "Expected Income ($)": expected_income,
        "Cumulative Value ($)": cumulative_value
    })
df = pd.DataFrame(results)

st.markdown("### תוצאות ההשקעה")
st.dataframe(df)

# יצירת גרף – נציג את הערך המצטבר לאורך השנים
fig, ax = plt.subplots(figsize=(8, 4))
ax.plot(df["Year"], df["Cumulative Value ($)"], marker='o', color='blue', linewidth=2)
ax.set_xlabel("שנה")
ax.set_ylabel("ערך מצטבר ($)")
# עיבוד כותרת בעברית באמצעות פונקציה לעיבוד RTL (אם נדרש)
ax.set_title(process_hebrew_text("צמיחת ההשקעה לאורך השנים"))
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
- מחשבון זה מחשב תשואה שנתית בצורה מצרפית כאשר התשואה הבסיסית מחושבת מהכנסה נטו חלקי השקעה.
- בכל שנה, התשואה גדלה לפי אחוז הגידול השנתי שהוזן.
- הדוח ב-PDF כולל פרטי השקעה, גרף וטבלת תוצאות.
""")
