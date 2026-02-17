import streamlit as st
import pandas as pd
import numpy as np
import time
import extra_streamlit_components as stx
import requests
import concurrent.futures

# --- 1. ตั้งค่าหน้าเว็บ (Must be first) ---
st.set_page_config(
    page_title="Team Sensor Academy",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# ⚠️ CONFIGURATION
# ==========================================
USER_DB_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vR0XoahMwduVM49_EJjYxMnbU9ABtSZzYPiInXBvSf_LhtAJqhl_5FRw-YrHQ7EIl2wbN27uZv0YTz9/pub?output=csv"
REGISTER_URL = "https://docs.google.com/forms/d/e/1FAIpQLSdx0bamRVPVOfiBXMpbbOSZny9Snr4U0VImflmJwm6KcdYKSA/viewform?usp=publish-editor"
CPN_AYY_CSV_URL = "https://docs.google.com/spreadsheets/d/1pqKDiANufw3J0GXaV2aeU_rAN31FUHMBB8nv_Uh5dFQ/export?format=csv&gid=0"
# ==========================================

cookie_manager = stx.CookieManager()

# --- Functions ---
def load_users():
    try:
        df = pd.read_csv(USER_DB_URL, on_bad_lines='skip')
        if len(df.columns) >= 5:
            df.columns.values[1] = 'username'
            df.columns.values[2] = 'password'
            df.columns.values[3] = 'name'
            df.columns.values[4] = 'role'
        df['password'] = df['password'].astype(str)
        df['role'] = df['role'].fillna('User')
        return df
    except: return pd.DataFrame()

def check_single_sensor(url):
    if pd.isna(url) or str(url).strip() == "" or not str(url).startswith("http"): return "No Link"
    try:
        response = requests.get(str(url), timeout=3)
        return "Good" if (response.status_code == 200 and response.json()) else "Bad"
    except: return "Bad"

def fetch_realtime_data_parallel(df):
    if 'API_URL' not in df.columns: return ["No API_URL Column"] * len(df)
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        return list(executor.map(check_single_sensor, df['API_URL'].tolist()))

def check_cookies():
    try:
        cookie_user = cookie_manager.get(cookie="sensor_user")
        if cookie_user and not st.session_state.get('logged_in', False):
            df = load_users()
            user_match = df[df['username'].astype(str) == str(cookie_user)]
            if not user_match.empty:
                st.session_state['logged_in'] = True
                st.session_state['user'] = user_match.iloc[0]['name']
                st.session_state['role'] = str(user_match.iloc[0]['role']).strip()
    except: pass

# --- PAGE: LOGIN ---
def login_page():
    c1, c2, c3 = st.columns([1, 1, 1])
    with c2:
        try: st.image("logo.png", use_container_width=True)
        except: st.title("🎓 Team Sensor")
    
    st.markdown("<h3 style='text-align: center;'>เข้าสู่ระบบการเรียนรู้</h3>", unsafe_allow_html=True)
    
    t1, t2 = st.tabs(["🔐 เข้าสู่ระบบ", "📝 ลงทะเบียนเรียน"])
    with t1:
        u = st.text_input("Username", key="u")
        p = st.text_input("Password", type="password", key="p")
        if st.button("Login", use_container_width=True):
            df = load_users()
            if not df.empty:
                m = df[(df['username'].astype(str)==u) & (df['password'].astype(str)==p)]
                if not m.empty:
                    st.session_state.update({'logged_in': True, 'user': m.iloc[0]['name'], 'role': str(m.iloc[0]['role']).strip()})
                    cookie_manager.set("sensor_user", u, expires_at=pd.Timestamp.now() + pd.Timedelta(days=7))
                    st.rerun()
                else: st.error("รหัสผ่านไม่ถูกต้อง")
            else: st.error("เชื่อมต่อฐานข้อมูลไม่ได้")
    with t2:
        st.info("กรอกข้อมูลเพื่อลงทะเบียน")
        st.link_button("ไปที่แบบฟอร์ม", REGISTER_URL, use_container_width=True)

# --- PAGE: MAIN ---
def main_app():
    with st.sidebar:
        st.write(f"สวัสดีครับคุณ **{st.session_state['user']}**")
        st.caption(f"สถานะ: {st.session_state['role']}")
        if st.button("ออกจากระบบ"):
            cookie_manager.delete("sensor_user")
            st.session_state['logged_in'] = False
            st.rerun()
    
    st.sidebar.title("📚 เมนูบทเรียน")
    page = st.sidebar.radio("เลือกหัวข้อ:", ["🌏 Overview Dashboard", "🏢 CPN AYY Monitor", "📖 Learning Academy", "✍️ Final Exam"])

    # --- 1. OVERVIEW ---
    if page == "🌏 Overview Dashboard":
        st.title("🌏 Real-time Overview")
        st.info("ภาพรวมโครงการทั้งหมด (Mockup Data)")

    # --- 2. CPN AYY ---
    elif page == "🏢 CPN AYY Monitor":
        st.title("🏢 CPN Ayutthaya Live Monitor")
        try:
            df = pd.read_csv(CPN_AYY_CSV_URL, on_bad_lines='skip')
            df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
            
            c1, c2 = st.columns([3, 1])
            with c1: st.info("กดปุ่มเพื่อตรวจสอบสถานะ Sensor หน้างานจริง")
            if c2.button("🔴 Check Live Status", type="primary"):
                with st.spinner("กำลังเชื่อมต่อ API..."):
                    df['Live_Status'] = fetch_realtime_data_parallel(df)
                    st.session_state['live_cache'] = df
            
            if 'live_cache' in st.session_state: df = st.session_state['live_cache']
            else: df['Live_Status'] = 'Unknown'

            st.dataframe(df[['Position Name', 'Live_Status', 'API_URL']], use_container_width=True)
        except Exception as e: st.error(f"Error: {e}")

    # --- 3. LEARNING ACADEMY (NEW CONTENT) ---
    elif page == "📖 Learning Academy":
        st.title("📖 ห้องเรียนวิศวกรรมงานระบบ")
        st.markdown("### โดย ศาสตราจารย์ฮาร์ท (Engineering Professor)")
        
        tab1, tab2, tab3 = st.tabs(["🔥 บทที่ 1: Heat Balance & CQ", "📋 บทที่ 2: Audit & Data Collection", "🧮 บทที่ 3: Workshop คำนวณจริง"])

        # --- TAB 1: THEORY ---
        with tab1:
            st.header("บทที่ 1: ทฤษฎีสมดุลความร้อนและค่า CQ")
            st.markdown("""
            > **"ทำไมเราต้องหา Heat Balance?"** > เพื่อตรวจสอบว่าข้อมูลที่เราวัดมา (Data Integrity) นั้นถูกต้องเชื่อถือได้หรือไม่ ก่อนนำไปวิเคราะห์ผลประหยัดพลังงาน
            """)
            
            st.divider()
            
            c1, c2 = st.columns(2)
            with c1:
                st.subheader("1. สมการ Heat Balance")
                st.latex(r"\% Heat Balance = \frac{(Q_{evap} + W_{input}) - Q_{cond}}{Q_{cond}} \times 100")
                st.success("✅ **เกณฑ์ที่ยอมรับได้ (Criteria):** ต้องไม่เกิน **± 5%**")
                
            with c2:
                st.subheader("2. สมการย่อย (Sub-Formulas)")
                st.info("จำสูตรแปลงหน่วยให้แม่น: **1 Ton = 3.5169 kW**")
                st.latex(r"Q_{evap} (Ton) = \frac{500 \times GPM \times CQ1}{12,000}")
                st.latex(r"Q_{cond} (Ton) = \frac{500 \times GPM \times CQ2}{15,000}")
                st.markdown("*หมายเหตุ: ใช้ 500 คูณเมื่อ GPM เป็นหน่วย US Gallon*")

            st.divider()
            st.subheader("3. รู้จักตัวแปร CQ (Characteristic Quantity)")
            
            cq_data = [
                {"Variable": "CQ1", "Description": "ผลต่างอุณหภูมิน้ำฝั่ง Evaporator (T_in - T_out)", "Purpose": "เช็คสมดุลน้ำเย็น"},
                {"Variable": "CQ2", "Description": "ผลต่างอุณหภูมิน้ำฝั่ง Condenser (T_out - T_in)", "Purpose": "เช็คสมดุลระบายความร้อน"},
                {"Variable": "CQ6", "Description": "Condenser Approach Temp (T_cond_sat - T_out)", "Purpose": "เช็คตะกรันในท่อ (Fouling)"},
                {"Variable": "CQ7", "Description": "Evaporator Approach Temp (T_out - T_evap_sat)", "Purpose": "เช็คประสิทธิภาพแลกเปลี่ยนความร้อน"}
            ]
            st.table(pd.DataFrame(cq_data))

        # --- TAB 2: AUDIT & SURVEY ---
        with tab2:
            st.header("บทที่ 2: ขั้นตอนการสำรวจหน้างาน (Site Audit)")
            st.markdown("ข้อมูลที่ต้องเก็บจาก Nameplate และ HMI เพื่อนำมาใช้คำนวณ")
            
            st.subheader("📸 Checklist สิ่งที่ต้องถ่ายรูป")
            c1, c2 = st.columns(2)
            with c1:
                st.info("1. Nameplate (ป้ายเพลท)")
                st.markdown("- **Chiller:** kW, Tons, Design Temp")
                st.markdown("- **Pump:** kW (Motor), Head, Flow")
                st.markdown("- **Cooling Tower:** Fan Motor kW")
            with c2:
                st.info("2. หน้าจอ HMI (ขณะเครื่องเดิน)")
                st.markdown("- **Power:** kW, Volts, Amps, %FLA")
                st.markdown("- **Temp:** Evap In/Out, Cond In/Out")
                st.markdown("- **Pressure/Sat:** Refrigerant Temp/Pressure")

        # --- TAB 3: WORKSHOP CALCULATION (NEW!) ---
        with tab3:
            st.header("🧮 บทที่ 3: Workshop การคำนวณพลังงาน (Case Study)")
            st.markdown("จากข้อมูลหน้างานจริง (CPMS Audit Guide) เราจะนำมาคำนวณหาการใช้พลังงานดังนี้")
            
            # --- EXAMPLE 1: PUMP ---
            st.subheader("1. การคำนวณพลังงานปั๊มน้ำ (Pump Energy)")
            st.markdown("📌 **โจทย์:** จากการสำรวจพบว่ามีปั๊มขนาด **1,071 kW** (Total) แต่ใช้งานจริงวัดได้ **445.5 kW** เปิดใช้งาน **13 ชั่วโมง/วัน**")
            
            with st.expander("ดูวิธีการคำนวณละเอียด (Click to expand)", expanded=True):
                st.markdown("### ขั้นตอนที่ 1: หา %Load ของปั๊ม")
                st.latex(r"\% Load = \frac{\text{Actual Power (kW)}}{\text{Full Load Power (kW)}} \times 100")
                st.code("445.5 / 1,071 = 0.4159... -> คิดเป็น 41.6%", language="python")
                
                st.markdown("### ขั้นตอนที่ 2: คำนวณหน่วยไฟฟ้าต่อวัน (kWh/Day)")
                st.latex(r"kWh/Day = \text{Actual Power (kW)} \times \text{Running Hours}")
                st.code("445.5 kW x 13 hr = 5,791.5 หน่วย (kWh) ต่อวัน", language="python")
                
                st.info("💡 **สรุป:** ปั๊มชุดนี้ทำงานที่ 41.6% ของพิกัด และกินไฟวันละ 5,791.5 หน่วย")

            st.divider()

            # --- EXAMPLE 2: COOLING TOWER ---
            st.subheader("2. การคำนวณพลังงาน Cooling Tower")
            st.markdown("📌 **โจทย์:** มี Cooling Tower ขนาด **5.5 kW จำนวน 25 ตัว** (รวม 137.5 kW) แต่ **เปิดใช้งานจริงแค่ 12 ตัว** เปิด **13 ชั่วโมง/วัน**")
            
            with st.expander("ดูวิธีการคำนวณละเอียด (Click to expand)", expanded=True):
                st.markdown("### ขั้นตอนที่ 1: หา kW ที่ใช้งานจริง (Actual kW)")
                st.markdown("ต้องคิดจากจำนวนพัดลมที่เปิดจริงเท่านั้น")
                st.code("5.5 kW x 12 ตัว = 66 kW (นี่คือค่า Actual Power)", language="python")
                
                st.markdown("### ขั้นตอนที่ 2: หา %Load เทียบกับ Full Capacity")
                st.markdown("สมมติว่า Full Load คือเปิดหมด 25 ตัว (5.5 x 25 = 137.5 kW)")
                st.latex(r"\% Load = \frac{66}{137.5} \times 100 = 48\%")
                st.caption("*(ในสไลด์ตัวอย่างใช้ฐาน 132 kW เลยได้ 50% แต่หลักการเดียวกันคือเทียบ Actual/Total)*")
                
                st.markdown("### ขั้นตอนที่ 3: คำนวณหน่วยไฟฟ้าต่อวัน")
                st.latex(r"kWh/Day = 66 \text{ kW} \times 13 \text{ hr}")
                st.code("66 x 13 = 858 หน่วย (kWh) ต่อวัน", language="python")

            st.divider()

            # --- EXAMPLE 3: HEAT BALANCE ---
            st.subheader("3. การคำนวณ Heat Balance (Case CPN Rayong)")
            st.markdown("📌 **โจทย์:** Chiller #1 มีข้อมูลดังนี้")
            col_data, col_calc = st.columns(2)
            
            with col_data:
                st.write("**ข้อมูลดิบ (Raw Data):**")
                st.write("- **GPM:** 3,000 gpm (Flow)")
                st.write("- **T_evap_in:** 54°F")
                st.write("- **T_evap_out:** 44°F")
                st.write("- **W_input (kW):** 661 kW")
                st.write("- **T_cond_out:** 94.1°F")
                st.write("- **T_cond_in:** 84.1°F")
            
            with col_calc:
                st.write("**วิธีทำ (Solution):**")
                st.write("1. หา CQ1 (Delta T Evap) = 54 - 44 = **10°F**")
                st.write("2. หา Q_evap (Ton) = (500 x 3000 x 10) / 12000 = **1,250 Ton**")
                st.write("3. แปลง Q_evap เป็น kW = 1250 x 3.5169 = **4,396 kW**")
                st.write("4. หา CQ2 (Delta T Cond) = 94.1 - 84.1 = **10°F**")
                st.write("5. หา Q_cond (Ton) = (500 x 3000 x 10) / 15000 = **1,000 Ton**")
                st.write("6. แปลง Q_cond เป็น kW = 1000 x 3.5169 = **3,516 kW**")
            
            st.info("⚠️ **ผลลัพธ์:** Heat Balance = (4396 + 661 - 3516) / 3516 * 100 = **+43.8%**")
            st.error("❌ **วิเคราะห์:** ค่าเกิน +5% มาก แสดงว่า Flow ฝั่ง Condenser น้อยกว่าความเป็นจริงมาก (Flow Meter อาจเพี้ยน)")

    # --- 4. QUIZ (NEW 20 QUESTIONS) ---
    elif page == "✍️ Final Exam":
        st.title("✍️ ทดสอบความรู้ (Final Exam)")
        st.caption("ข้อสอบชุดใหม่ จากเนื้อหาบทที่ 1, 2 และ 3")
        
        quiz_db = {
            "Heat Balance & CQ": [
                {"q": "สูตรการหา % Heat Balance ที่ถูกต้องคือข้อใด?", "c": ["(Qevap + Winput - Qcond) / Qcond * 100", "(Qevap - Qcond) / Winput * 100"], "a": "(Qevap + Winput - Qcond) / Qcond * 100"},
                {"q": "เกณฑ์มาตรฐาน (Criteria) ของ % Heat Balance คือช่วงใด?", "c": ["± 5%", "± 10%"], "a": "± 5%"},
                {"q": "ในการแปลงหน่วย 1 Ton ความเย็น มีค่าเท่ากับกี่ kW?", "c": ["3.5169 kW", "12.000 kW"], "a": "3.5169 kW"},
                {"q": "CQ1 คือค่าผลต่างอุณหภูมิของส่วนใด?", "c": ["น้ำเข้า-ออก Evaporator", "น้ำเข้า-ออก Condenser"], "a": "น้ำเข้า-ออก Evaporator"},
                {"q": "CQ6 (Condenser Approach Temp) ใช้ตรวจสอบสิ่งใด?", "c": ["ความสกปรกของท่อ (Fouling)", "ประสิทธิภาพปั๊มน้ำ"], "a": "ความสกปรกของท่อ (Fouling)"},
                {"q": "ถ้าค่า CQ วัดจริง 'ต่ำกว่า' ค่า CQ Design (Low Delta T) เกิดจากสาเหตุใด?", "c": ["Water Flow Rate สูงเกินไป", "Water Flow Rate ต่ำเกินไป"], "a": "Water Flow Rate สูงเกินไป"},
                {"q": "ค่า W_input ในสมการ Heat Balance หมายถึงอะไร?", "c": ["พลังงานไฟฟ้าขาเข้า Chiller", "พลังงานลมจาก Cooling Tower"], "a": "พลังงานไฟฟ้าขาเข้า Chiller"},
                {"q": "สูตรคำนวณ Q_cond (Ton) ตัวหารคือเท่าไหร่?", "c": ["15,000", "12,000"], "a": "15,000"},
                {"q": "สูตรคำนวณ Q_evap (Ton) ตัวหารคือเท่าไหร่?", "c": ["12,000", "15,000"], "a": "12,000"},
                {"q": "หาก % Heat Balance เป็นบวก (+) มากเกินไป แสดงว่าอะไรผิดปกติ?", "c": ["Flow ฝั่ง Condenser น้อยกว่าจริง", "Flow ฝั่ง Evaporator น้อยกว่าจริง"], "a": "Flow ฝั่ง Condenser น้อยกว่าจริง"}
            ],
            "Calculation & Audit": [
                {"q": "ถ้าเปิด Cooling Tower 5.5kW จำนวน 10 ตัว เป็นเวลา 10 ชม. จะใช้ไฟกี่หน่วย?", "c": ["550 หน่วย", "55 หน่วย"], "a": "550 หน่วย"},
                {"q": "สูตรหา %Load ของ Pump คือ?", "c": ["Actual kW / Full Load kW", "Full Load kW / Actual kW"], "a": "Actual kW / Full Load kW"},
                {"q": "ถ้า Pump ขนาด 100 kW ทำงานจริงที่ 80 kW คิดเป็น Load กี่ %?", "c": ["80%", "20%"], "a": "80%"},
                {"q": "ข้อมูลใดต้องเก็บจาก Nameplate ของ Chiller?", "c": ["kW & Tons", "ราคาเครื่อง"], "a": "kW & Tons"},
                {"q": "ค่า Refrigerant Temp นำไปใช้หาค่าใด?", "c": ["Approach Temp (CQ6, CQ7)", "Flow Rate"], "a": "Approach Temp (CQ6, CQ7)"},
                {"q": "ถ้า Heat Balance ได้ +40% ควรทำอย่างไร?", "c": ["ตรวจสอบ Flow Meter ฝั่ง Condenser", "ปล่อยผ่าน"], "a": "ตรวจสอบ Flow Meter ฝั่ง Condenser"},
                {"q": "การคำนวณค่าไฟ Cooling Tower ต้องคิดจาก?", "c": ["จำนวนพัดลมที่เปิดจริง", "จำนวนพัดลมทั้งหมดที่มี"], "a": "จำนวนพัดลมที่เปิดจริง"},
                {"q": "CQ7 คำนวณจากค่าใด?", "c": ["T_out_Evap - T_Refrig_Sat", "T_in - T_out"], "a": "T_out_Evap - T_Refrig_Sat"},
                {"q": "Sensors ใดจำเป็นสำหรับหาค่า Load ของอาคาร?", "c": ["Flow Rate & Temp Evap", "Pressure Gauge"], "a": "Flow Rate & Temp Evap"},
                {"q": "13,923 หน่วย ในตัวอย่าง Pump มาจาก?", "c": ["1,071 kW x 13 hr", "445.5 kW x 13 hr"], "a": "1,071 kW x 13 hr"}
            ]
        }
        
        topic = st.selectbox("เลือกหัวข้อสอบ:", list(quiz_db.keys()))
        
        if 'quiz_state' not in st.session_state or st.session_state.get('last_topic') != topic:
            st.session_state['quiz_state'] = 'start'
            st.session_state['last_topic'] = topic
            st.session_state['score'] = 0

        with st.form("exam_form"):
            answers = {}
            for i, item in enumerate(quiz_db[topic]):
                st.markdown(f"**{i+1}. {item['q']}**")
                answers[i] = st.radio(f"เลือกคำตอบข้อ {i+1}", item['c'], key=f"q{i}", label_visibility="collapsed")
                st.divider()
            
            if st.form_submit_button("ส่งคำตอบ (Submit)"):
                score = 0
                for i, item in enumerate(quiz_db[topic]):
                    if answers[i] == item['a']: score += 1
                
                st.success(f"🎉 คุณได้คะแนน: {score} / 10")
                if score < 5: st.warning("ควรกลับไปทบทวนเนื้อหาใหม่นะครับ")
                else: st.balloons()

# --- EXECUTION ---
if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False
check_cookies()
if not st.session_state['logged_in']: login_page()
else: main_app()