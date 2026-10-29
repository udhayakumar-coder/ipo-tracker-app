import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
import pandas as pd
import yfinance as yf
import datetime

st.set_page_config(page_title="IPO & Stock Analyzer", page_icon="📊", layout="wide")

st.title("📊 ஸ்மார்ட் IPO மற்றும் பங்கு ஆய்வு தளம்")
st.caption("நேரலை IPO கண்காணிப்பு • பல வருட வரலாற்றுத் தரவு • எதிர்கால விலைக் கணிப்பு")

# இரண்டு முக்கிய பிரிவுகள் (Tabs)
tab1, tab2 = st.tabs(["🚀 நேரலை Mainboard IPO டிராக்கர்", "📈 பங்குகள் ஆய்வு & எதிர்காலக் கணிப்பு"])

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
}

def clean_number(text):
    if not text:
        return 0.0
    cleaned = re.sub(r"[^\d.]", "", text.strip())
    try:
        return float(cleaned)
    except ValueError:
        return 0.0

# ==========================================
# பிரிவு 1: திருத்தப்பட்ட IPO ஸ்கிராப்பர்
# ==========================================
with tab1:
    st.subheader("நடப்பு Mainboard IPO நிலவரம்")

    @st.cache_data(ttl=600)
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
                        cols = [c.get_text(strip=True) for c in row.find_all("td")]
                        if len(cols) >= 6:
                            name = cols[0]
                            if "SME" in name:
                                continue

                            # தேதி மற்றும் தொகையைத் துல்லியமாகப் பிரித்தல்
                            # வழக்கமாக தேதி வடிவம்: DD-Mon அல்லது DD/MM/YYYY
                            raw_dates = [c for c in cols if re.search(r"\d{1,2}-[A-Za-z]{3}|\d{1,2}/\d{1,2}", c)]
                            close_date = raw_dates[-1] if raw_dates else "அறிவிக்கப்படவில்லை"

                            price = cols[2]
                            gmp = cols[3]
                            est_listing = cols[5] if len(cols) > 5 else "N/A"

                            price_val = clean_number(price)
                            gmp_val = clean_number(gmp)
                            gmp_pct = (gmp_val / price_val * 100) if price_val > 0 else 0

                            if gmp_pct >= 20:
                                verdict = "🟢 Strong Apply (அதிக லாப வாய்ப்பு)"
                            elif gmp_pct >= 10:
                                verdict = "🟡 Watch & Wait (கண்காணிக்கவும்)"
                            elif gmp_val == 0:
                                verdict = "⚪ GMP Not Started (தொடங்கவில்லை)"
                            else:
                                verdict = "🔴 Avoid (அபாயம் அதிகம்)"

                            ipo_list.append({
                                "நிறுவனம்": name,
                                "கடைசி தேதி": close_date,
                                "வெளியீட்டு விலை": f"₹{price}",
                                "தற்போதைய GMP": f"₹{gmp} ({gmp_pct:.1f}%)",
                                "பட்டியல் எதிர்பார்ப்பு": f"₹{est_listing}",
                                "முடிவு": verdict
                            })
        except Exception as e:
            st.error(f"தகவல் பெறுவதில் பிழை: {e}")
        return ipo_list

    if st.button("🔄 IPO தகவல்களைப் புதுப்பி"):
        st.cache_data.clear()
        st.rerun()

    ipo_data = get_live_ipos()
    if ipo_data:
        for item in ipo_data:
            with st.container():
                st.markdown(f"### {item['நிறுவனம்']}")
                c1, c2, c3 = st.columns(3)
                c1.metric("வெளியீட்டு விலை", item["வெளியீட்டு விலை"])
                c2.metric("தற்போதைய GMP", item["தற்போதைய GMP"])
                c3.metric("கடைசி தேதி", item["கடைசி தேதி"])
                st.write(f"🎯 **எதிர்பார்க்கப்படும் பட்டியல் விலை:** {item['பட்டியல் எதிர்பார்ப்பு']}")
                st.markdown(f"**மதிப்பீடு:** `{item['முடிவு']}`")
                st.divider()
    else:
        st.info("தற்போது செயலில் உள்ள Mainboard IPO விவரங்கள் கிடைக்கவில்லை.")

# ==========================================
# பிரிவு 2: பழைய வரலாறு & எதிர்காலக் கணிப்பு
# ==========================================
with tab2:
    st.subheader("பங்குகளின் முழு வரலாறு மற்றும் எதிர்கால இலக்கு")
    st.write("இந்தியப் பங்குகளின் குறியீட்டை (NSE Ticker) உள்ளிட்டு முழுமையான தரவைப் பார்க்கலாம்.")

    col_sym, col_period = st.columns([2, 1])
    ticker_input = col_sym.text_input("பங்கின் NSE குறியீடு (எ.கா: RELIANCE, TCS, TATAMOTORS, INFY):", "RELIANCE")
    period_choice = col_period.selectbox("வரலாற்றுக்காலம்:", ["1y", "3y", "5y", "max"], index=2)

    if ticker_input:
        symbol = f"{ticker_input.strip().upper()}.NS"
        try:
            stock = yf.Ticker(symbol)
            hist = stock.history(period=period_choice)

            if not hist.empty:
                current_price = hist["Close"].iloc[-1]
                prev_price = hist["Close"].iloc[-2] if len(hist) > 1 else current_price
                price_change = current_price - prev_price
                price_change_pct = (price_change / prev_price) * 100

                info = stock.info
                company_name = info.get("longName", ticker_input.upper())
                pe_ratio = info.get("trailingPE", "N/A")
                mkt_cap = info.get("marketCap", 0) / 1e7  # கோடிகளில்

                st.markdown(f"## {company_name}")
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("தற்போதைய சந்தை விலை", f"₹{current_price:.2f}", f"{price_change:+.2f} ({price_change_pct:+.2f}%)")
                m2.metric("52 வார உச்சம்", f"₹{info.get('fiftyTwoWeekHigh', 'N/A')}")
                m3.metric("52 வார குறைவு", f"₹{info.get('fiftyTwoWeekLow', 'N/A')}")
                m4.metric("P/E விகிதம்", f"{pe_ratio if isinstance(pe_ratio, str) else round(pe_ratio, 2)}")

                # விலை வரைபடம்
                st.markdown("#### 📈 பல ஆண்டுகால விலை போக்கு (Price History Chart)")
                st.line_chart(hist["Close"])

                # எதிர்காலக் கணிப்பு மாதிரி (Statistical Trend Projection)
                st.divider()
                st.markdown("### 🔮 எதிர்கால விலைக் கணிப்பு (1 – 3 ஆண்டுகள்)")

                # ஆண்டு வளர்ச்சி வேகம் (Annualized CAGR Calculation)
                years_count = (hist.index[-1] - hist.index[0]).days / 365.25
                if years_count >= 1:
                    total_growth = hist["Close"].iloc[-1] / hist["Close"].iloc[0]
                    cagr = (total_growth ** (1 / years_count)) - 1
                else:
                    cagr = 0.12  # குறைந்தபட்ச இயல்பு வளர்ச்சி 12%

                # மிதமான கணிப்பு (Cap at realistic bands)
                base_cagr = max(0.05, min(cagr, 0.25))

                t1_conservative = current_price * (1 + (base_cagr * 0.75))
                t1_target = current_price * (1 + base_cagr)
                t1_bullish = current_price * (1 + (base_cagr * 1.35))

                t3_target = current_price * ((1 + base_cagr) ** 3)

                st.write(f"நிறுவனத்தின் கடந்த கால வரலாற்று வளர்ச்சி விகிதம்: **{cagr * 100:.1f}% CAGR**")

                f1, f2, f3 = st.columns(3)
                f1.metric("1 ஆண்டு இலக்கு (பாதுகாப்பானது)", f"₹{t1_conservative:.2f}", f"+{(base_cagr*0.75)*100:.1f}%")
                f2.metric("1 ஆண்டு இலக்கு (சராசரி)", f"₹{t1_target:.2f}", f"+{base_cagr*100:.1f}%")
                f3.metric("3 ஆண்டு நீண்டகால இலக்கு", f"₹{t3_target:.2f}", f"+{(((1+base_cagr)**3)-1)*100:.1f}%")

                st.caption("⚠️ குறிப்பு: கணிப்புகள் கடந்த கால விலை நகர்வுகள் மற்றும் வணிக வளர்ச்சி வேகத்தின் அடிப்படையில் கணக்கிடப்படுகின்றன. சந்தை அபாயங்களுக்கு உட்பட்டது.")
            else:
                st.error("இந்த பங்கிற்கான வரலாற்றுத் தரவுகள் கிடைக்கவில்லை. சரியான NSE குறியீட்டை உள்ளிடவும்.")
        except Exception as ex:
            st.error(f"தரவை எடுப்பதில் சிக்கல்: {ex}")