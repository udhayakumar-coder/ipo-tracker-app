import streamlit as st
import requests
from bs4 import BeautifulSoup
import re

st.set_page_config(page_title="Live IPO Tracker", page_icon="📈", layout="centered")

# மொபைல் தலைப்பு & வடிவமைப்பு
st.title("📈 நேரலை IPO & GMP கண்காணிப்பாளர்")
st.caption("Groww முதலீட்டாளர்களுக்கான நிகழ்நேர ஆய்வு மையம்")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

def clean_number(text):
    if not text:
        return 0.0
    cleaned = re.sub(r"[^\d.]", "", text.strip())
    try:
        return float(cleaned)
    except ValueError:
        return 0.0

@st.cache_data(ttl=900)  # 15 நிமிடங்களுக்கு ஒருமுறை புதிய டேட்டா எடுக்கும்
def get_live_ipos():
    url = "https://www.investorgain.com/report/live-ipo-gmp/331/"
    ipo_list = []
    try:
        res = requests.get(url, headers=HEADERS, timeout=12)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            table = soup.find("table")
            if table:
                rows = table.find_all("tr")[1:]
                for row in rows:
                    cols = row.find_all("td")
                    if len(cols) >= 6:
                        name = cols[0].get_text(strip=True)
                        close_date = cols[1].get_text(strip=True)
                        price = cols[2].get_text(strip=True)
                        gmp = cols[3].get_text(strip=True)
                        est_listing = cols[5].get_text(strip=True)

                        if "SME" in name:
                            continue

                        price_val = clean_number(price)
                        gmp_val = clean_number(gmp)
                        gmp_pct = (gmp_val / price_val * 100) if price_val > 0 else 0

                        if gmp_pct >= 20:
                            badge = "🟢 Strong Apply"
                        elif gmp_pct >= 10:
                            badge = "🟡 Watch & Wait"
                        elif gmp_val == 0:
                            badge = "⚪ GMP Not Started"
                        else:
                            badge = "🔴 Avoid / High Risk"

                        ipo_list.append({
                            "name": name,
                            "close_date": close_date,
                            "price": price,
                            "gmp": gmp,
                            "gmp_pct": f"{gmp_pct:.1f}%",
                            "est_listing": est_listing,
                            "badge": badge
                        })
    except Exception as e:
        st.error(f"தகவல் பெறுவதில் பிழை: {e}")
    return ipo_list

# தரவை ஏற்றுதல்
data = get_live_ipos()

if st.button("🔄 நேரலைத் தரவைப் புதுப்பி (Refresh)"):
    st.cache_data.clear()
    st.rerun()

st.divider()

if not data:
    st.info("தற்போது Mainboard IPO விவரங்கள் எதுவும் கிடைக்கவில்லை.")
else:
    for ipo in data:
        with st.container():
            st.subheader(ipo["name"])
            c1, c2 = st.columns(2)
            c1.metric("வெளியீட்டு விலை", f"₹{ipo['price']}")
            c2.metric("தற்போதைய GMP", f"₹{ipo['gmp']} ({ipo['gmp_pct']})")
            
            st.write(f"📅 *கடைசி தேதி:* {ipo['close_date']} | 🎯 *பட்டியல்:* ₹{ipo['est_listing']}")
            st.markdown(f"*மதிப்பீடு:* {ipo['badge']}")
            st.divider()
