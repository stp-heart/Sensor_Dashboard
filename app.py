import streamlit as st
import pandas as pd
import numpy as np
import time
import extra_streamlit_components as stx
import requests
import concurrent.futures

# --- 1. SET UP (บรรทัดแรกสุด) ---
st.set_page_config(
    page_title="Team Sensor Academy",
    page_icon="👨‍🏫",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# ⚠️ CONFIGURATION
# ==========================================
USER_DB_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vR0XoahMwduVM49_EJjYxMnbU9ABtSZzYPiInXBvSf_LhtAJqhl_5FRw-YrHQ7EIl2wbN27uZv0YTz9/pub?output=csv"
REGISTER_URL = "https://docs.google.com/forms/d/e/1FAIpQLSdx0bamRVPVOfiBXMpbbOSZny9Snr4U0VImflmJwm6KcdYKSA/viewform?usp=publish-editor"
# ลิงก์ไฟล์งานล่าสุดของคุณ
CPN_AYY_CSV_URL = "https://docs.google.com/spreadsheets/d/1pqKDiANufw3J0GXaV2aeU_rAN31FUHMBB8nv_Uh5dFQ/export?format=csv&gid=0"

cookie_manager = stx.CookieManager()

# --- HELPER FUNCTIONS ---
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
        r = requests.get(str(url), timeout=3)
        return "Good" if (r.status_code == 200 and r.json()) else "Bad"
    except: return "Bad"

def fetch_realtime_data_parallel(df):
    if 'API_URL' not in df.columns: return ["No API_URL Column"] * len(df)
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        return list(executor.map(check_single_sensor, df['API_URL'].tolist()))

def check_cookies():
    try:
        u = cookie_manager.get(cookie="sensor_user")
        if u and not st.session_state.get('logged_in', False):
            df = load_users()
            m = df[df['username'].astype(str) == str(u)]
            if not m.empty:
                st.session_state.update({'logged_in':True, 'user':m.iloc[0]['name'], 'role':str(m.iloc[0]['role']).strip()})
    except: pass

# --- UI COMPONENTS ---
def login_page():
    c1, c2, c3 = st.columns([1,1,1])
    with c2: 
        try: st.image("logo.png", use_container_width=True)
        except: st.title("👨‍🏫 Professor Heart")
    st.markdown("<h3 style='text-align:center'>Engineering Academy Login</h3>", unsafe_allow_html=True)
    t1, t2 = st.tabs(["🔐 Login", "📝 Register"])
    with t1:
        u = st.text_input("Username", key="u")
        p = st.text_input("Password", type="password", key="p")
        if st.button("Login", use_container_width=True):
            df = load_users()
            if not df.empty:
                m = df[(df['username'].astype(str)==u) & (df['password'].astype(str)==p)]
                if not m.empty:
                    st.session_state.update({'logged_in':True, 'user':m.iloc[0]['name'], 'role':str(m.iloc[0]['role']).strip()})
                    cookie_manager.set("sensor_user", u, expires_at=pd.Timestamp.now() + pd.Timedelta(days=7))
                    st.rerun()
                else: st.error("รหัสผ่านไม่ถูกต้อง")
            else: st.error("ไม่สามารถเชื่อมต่อฐานข้อมูลได้")
    with t2:
        st.info("กรอกข้อมูลเพื่อลงทะเบียน")
        st.link_button("👉 ไปที่แบบฟอร์ม", REGISTER_URL, use_container_width=True)

# --- LEARNING CONTENT (FULL) ---
def render_learning():
    st.title("📖 Engineering Academy: Deep Dive")
    st.markdown("### โดย ศาสตราจารย์ฮาร์ท (Engineering Professor)")
    
    tab_explain, tab_calc, tab_workshop, tab_collect = st.tabs([
        "1. อธิบายตาราง Audit (Table Anatomy)", 
        "2. เจาะลึกสูตรคำนวณ (Advanced Formulas)", 
        "3. Workshop คำนวณจริง (Case Study)",
        "4. การเก็บข้อมูล (Data Collection)"
    ])

    # --- TAB 1: TABLE ANATOMY ---
    with tab_explain:
        st.header("บทที่ 1: เจาะลึกตาราง Audit (Table Anatomy)")
        st.info("ทำความเข้าใจที่มาของข้อมูลในตาราง Report ทีละคอลัมน์")

        # Table Data Mockup
        st.subheader("📊 ตัวอย่างตาราง Chiller Operation Data")
        mock_data = {
            "Setpoint": ["44°F"], "%FLA": ["85%"], "Power (kW)": ["210 kW"],
            "Tevi": ["54°F"], "Tevo": ["44°F"], "CQ1": ["10°F"],
            "Tcdi": ["85°F"], "Tcdo": ["95°F"], "CQ2": ["10°F"],
            "Evap_Sat": ["40°F"], "CQ7": ["4°F"],
            "Cond_Sat": ["100°F"], "CQ6": ["5°F"]
        }
        st.dataframe(pd.DataFrame(mock_data))

        st.markdown("---")
        c1, c2 = st.columns(2)
        
        with c1:
            st.markdown("#### 🔵 กลุ่ม 1: ข้อมูลดิบ (Raw Data from HMI)")
            st.markdown("""
            **1. Setpoint**
            * **คือ:** ค่าอุณหภูมิน้ำออกที่เราตั้งค่าสั่งให้เครื่องทำ
            * **ที่มา:** อ่านจากหน้าจอ HMI
            
            **2. %FLA (% Full Load Amps)**
            * **คือ:** เปอร์เซ็นต์กระแสที่ใช้เทียบกับพิกัดสูงสุด
            * **ที่มา:** อ่านจากหน้าจอ HMI
            * **ใช้ทำอะไร:** ประเมิน Load คร่าวๆ
            
            **3. Power (kW)**
            * **คือ:** กำลังไฟฟ้าที่กินจริง
            * **ที่มา:** Power Meter หรือหน้าจอ HMI
            
            **4. Temp Evap (Tevi / Tevo)**
            * **คือ:** อุณหภูมิน้ำเข้า/ออก ฝั่งน้ำเย็น
            * **ที่มา:** Sensor ท่อ CHR/CHS หรือหน้าจอ HMI
            
            **5. Temp Cond (Tcdi / Tcdo)**
            * **คือ:** อุณหภูมิน้ำเข้า/ออก ฝั่งระบายความร้อน
            * **ที่มา:** Sensor ท่อ CDS/CDR หรือหน้าจอ HMI
            """)

        with c2:
            st.markdown("#### 🔴 กลุ่ม 2: ข้อมูลจากการคำนวณ (Calculated)")
            st.markdown("""
            **6. CQ1 (Delta T Evap)**
            * **สูตร:** $T_{evi} - T_{evo}$ (เข้า - ออก)
            * **ปกติ:** ควรประมาณ 10°F
            
            **7. CQ2 (Delta T Cond)**
            * **สูตร:** $T_{cdo} - T_{cdi}$ (ออก - เข้า)
            * **ปกติ:** ควรประมาณ 10°F
            
            **8. T_Sat (Evap/Cond)**
            * **คือ:** อุณหภูมิน้ำยาแอร์ (Saturation Temp)
            * **ที่มา:** แปลงค่าจาก Pressure Gauge หรือดูหน้าจอ
            
            **9. CQ7 (Evap Approach)**
            * **สูตร:** $T_{evo} - T_{EvapSat}$ (น้ำออก - น้ำยา)
            * **ใช้ดู:** ประสิทธิภาพการแลกเปลี่ยนความร้อนฝั่งเย็น
            
            **10. CQ6 (Cond Approach)**
            * **สูตร:** $T_{CondSat} - T_{cdo}$ (น้ำยา - น้ำออก)
            * **ใช้ดู:** ตะกรันในท่อ (Fouling) ถ้าสูงต้องแยงท่อ
            """)

    # --- TAB 2: FORMULAS ---
    with tab_calc:
        st.header("บทที่ 2: เจาะลึกสูตรคำนวณ (Formulas)")
        
        st.subheader("1. การหาค่า Loss (ความสูญเสียพลังงาน)")
        st.markdown("ใช้สำหรับหาว่า **'ปั๊มกินไฟเกินความจำเป็นไปเท่าไหร่'** จากการที่ CQ ต่ำกว่า Design")
        st.success("💡 **หลักการ:** $Power \propto Flow^3$ (กฎ Affinity Laws)")
        
        st.latex(r"Loss (kW) = kW_{Actual} \times \left[ 1 - \left( \frac{CQ_{Actual}}{CQ_{Design}} \right)^3 \right]")
        
        st.markdown("**ตัวแปร:**")
        st.markdown("- $kW_{Actual}$: กำลังไฟฟ้าปั๊มที่วัดได้จริง")
        st.markdown("- $CQ_{Actual}$: Delta T ที่วัดได้จริง")
        st.markdown("- $CQ_{Design}$: Delta T ที่ออกแบบไว้ (ปกติใช้ 10°F)")
        st.info("**ความหมาย:** ถ้า CQ ต่ำลง -> Flow จะสูงขึ้น -> kW ปั๊มจะพุ่งสูงขึ้นแบบกำลัง 3 ส่วนต่างนั้นคือ Loss")

        st.divider()

        st.subheader("2. การหา Heat Balance")
        st.latex(r"\% Heat Balance = \frac{(Q_{evap} + W_{input}) - Q_{cond}}{Q_{cond}} \times 100")
        
        c_f1, c_f2 = st.columns(2)
        with c_f1:
            st.markdown("**ฝั่งทำความเย็น ($Q_{evap}$)**")
            st.latex(r"Q_{evap} (Ton) = \frac{500 \times GPM \times CQ1}{12,000}")
            st.caption("CQ1 = Evap Return - Evap Leaving")
            st.markdown("*500 มาจาก 8.33 lb/gal x 60 min x 1 Btu/lb°F*")
        
        with c_f2:
            st.markdown("**ฝั่งระบายความร้อน ($Q_{cond}$)**")
            st.latex(r"Q_{cond} (Ton) = \frac{500 \times GPM \times CQ2}{15,000}")
            st.caption("CQ2 = Cond Leaving - Cond Return")
            st.markdown("*15,000 มาจาก 12,000 x 1.25 (เผื่อ Heat Rejection 25%)*")

    # --- TAB 3: WORKSHOP (ละเอียดสุดๆ) ---
    with tab_workshop:
        st.header("🧮 บทที่ 3: Workshop คำนวณจริง (Case Study)")
        st.markdown("ข้อมูลทั้งหมดอ้างอิงจากไฟล์ *TIESmartSolutions - CPMS audit guide.pptx*")

        # --- CASE 1: LOSS FROM CQ ---
        with st.expander("💸 Case 1: การหา Loss from CQ (สำคัญมาก!)", expanded=True):
            st.markdown("#### สถานการณ์สมมติ:")
            st.markdown("ระบบปั๊มน้ำ (Pump) กินไฟวัดจริง **445.5 kW** (จากไฟล์ Audit Guide)")
            st.markdown("แต่เมื่อวัดอุณหภูมิพบว่า **CQ วัดได้แค่ 5°F** (Low Delta T) ทั้งที่ Design ไว้ **10°F**")
            
            st.markdown("#### วิธีทำ:")
            st.markdown("1. **เทียบสัดส่วน CQ:**")
            st.latex(r"Ratio = \frac{CQ_{Actual}}{CQ_{Design}} = \frac{5}{10} = 0.5")
            st.caption("*(แปลว่า Flow Rate ไหลเร็วกว่าที่ควรจะเป็น 2 เท่า)*")
            
            st.markdown("2. **เข้าสูตร Affinity Law (กำลัง 3):**")
            st.latex(r"Loss = 445.5 \times [1 - (0.5)^3]")
            st.latex(r"Loss = 445.5 \times [1 - 0.125] = 445.5 \times 0.875")
            
            st.markdown("3. **ผลลัพธ์:**")
            st.latex(r"Loss = 389.8 \text{ kW}")
            
            st.error("❌ **วิเคราะห์:** ปั๊มกินไฟ 445.5 kW แต่ใช้งานจริงจังแค่ 55.7 kW อีก **389.8 kW คือพลังงานที่สูญเสียไปฟรีๆ** จากการที่น้ำไหลเร็วเกินไป (Over Flow)")

        # --- CASE 2: PUMP ENERGY ---
        with st.expander("💦 Case 2: การคำนวณพลังงาน Pump (จากไฟล์ PPT)", expanded=False):
            st.markdown("#### ข้อมูลหน้างาน:")
            st.write("- Nameplate Max: **1,071 kW**")
            st.write("- Actual Power: **445.5 kW**")
            st.write("- Hours: **13 hr**")
            
            st.markdown("#### วิธีคำนวณ:")
            st.markdown("**1. หา %Load:**")
            st.latex(r"\%Load = \frac{445.5}{1,071} \times 100 = 41.6\%")
            st.markdown("**2. หา kWh:**")
            st.latex(r"kWh = 445.5 \times 13 = 5,791.5 \text{ Units}")

        # --- CASE 3: COOLING TOWER ---
        with st.expander("V Case 3: การคำนวณ Cooling Tower (จากไฟล์ PPT)", expanded=False):
            st.markdown("#### ข้อมูลหน้างาน:")
            st.write("- Spec: **5.5 kW x 25 ตัว**")
            st.write("- เปิดจริง: **12 ตัว**")
            st.write("- Hours: **13 hr**")
            
            st.markdown("#### วิธีคำนวณ:")
            st.markdown("**1. หา kW ที่ใช้จริง (Actual kW):**")
            st.code("5.5 kW * 12 ตัว = 66 kW", language="python")
            
            st.markdown("**2. หาหน่วยไฟฟ้า (kWh):**")
            st.latex(r"kWh = 66 \text{ kW} \times 13 \text{ hr} = 858 \text{ Units}")

        # --- CASE 4: HEAT BALANCE ---
        with st.expander("🌡️ Case 4: คำนวณ Heat Balance (ละเอียด)", expanded=False):
            st.markdown("**ข้อมูล:** GPM=3000, CQ1=10, CQ2=10, Power=661 kW")
            st.markdown("**1. หา Q_evap:**")
            st.latex(r"\frac{500 \times 3000 \times 10}{12000} = 1,250 \text{ Ton} \Rightarrow 4,396 \text{ kW}")
            st.markdown("**2. หา Q_cond:**")
            st.latex(r"\frac{500 \times 3000 \times 10}{15000} = 1,000 \text{ Ton} \Rightarrow 3,516 \text{ kW}")
            st.markdown("**3. Heat Balance:**")
            st.latex(r"\frac{(4396 + 661) - 3516}{3516} \times 100 = +43.8\%")

    # --- TAB 4: DATA COLLECTION ---
    with tab_collect:
        st.header("บทที่ 4: การเก็บข้อมูล (Data Collection)")
        st.info("แยกแยะให้ออกระหว่างค่า Design (Nameplate) และค่า Actual (HMI)")
        
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("📌 1. Nameplate (Design)")
            st.markdown("ใช้เป็น **ตัวหาร** เพื่อหา %Load")
            st.markdown("""
            * **Chiller:** kW Max, Tons Max
            * **Pump:** kW Motor (Max)
            * **Cooling Tower:** Fan Motor kW (Max)
            """)
        with c2:
            st.subheader("🖥️ 2. HMI Screen (Actual)")
            st.markdown("ใช้คำนวณ **Energy & Efficiency**")
            st.markdown("""
            * **Power:** kW (Actual)
            * **Temp:** Evap In/Out (CQ1), Cond In/Out (CQ2)
            * **Pressure:** Saturation Temp (Approach)
            """)

# --- QUIZ SECTION (MASTER QUIZ) ---
def render_quiz():
    st.title("✍️ Final Exam")
    st.caption("ข้อสอบวัดความรู้จากทุกบทเรียน")
    
    quiz_db = {
        "หมวด 1: ทฤษฎี & สูตร": [
            {"q": "สูตรหา Loss จาก CQ อาศัยหลักการใด?", "c": ["Affinity Laws (Flow^3)", "Ohm's Law"], "a": "Affinity Laws (Flow^3)"},
            {"q": "ถ้า Design CQ=10 แต่วัดจริงได้ 5 (Ratio=0.5) พลังงานส่วนที่เป็น Loss คิดเป็นสัดส่วนเท่าไหร่?", "c": ["87.5% (1 - 0.5^3)", "50%"], "a": "87.5% (1 - 0.5^3)"},
            {"q": "CQ6 (Cond Approach) ที่สูงเกินไป บ่งบอกปัญหาอะไร?", "c": ["ตะกรันในท่อ (Fouling)", "น้ำยาแอร์ขาด"], "a": "ตะกรันในท่อ (Fouling)"},
            {"q": "ข้อมูล Setpoint เอามาจากไหน?", "c": ["หน้าจอ HMI", "Nameplate"], "a": "หน้าจอ HMI"},
            {"q": "ในการหา Q_cond (Ton) ตัวหารคือ?", "c": ["15,000", "12,000"], "a": "15,000"},
            {"q": "สูตร Heat Balance ข้อใดถูก?", "c": ["(Qevap+W-Qcond)/Qcond", "(Qevap-Qcond)/W"], "a": "(Qevap+W-Qcond)/Qcond"},
            {"q": "1 Ton ความเย็น เท่ากับกี่ kW?", "c": ["3.5169", "12"], "a": "3.5169"},
            {"q": "CQ1 คำนวณจาก?", "c": ["T_in - T_out (Evap)", "T_out - T_in (Cond)"], "a": "T_in - T_out (Evap)"},
            {"q": "W_input ต้องรวมอะไรบ้าง?", "c": ["Compressor Power", "Fan Power"], "a": "Compressor Power"},
            {"q": "เกณฑ์ Heat Balance ที่ผ่านคือ?", "c": ["± 5%", "± 10%"], "a": "± 5%"}
        ],
        "หมวด 2: การคำนวณ (Workshop)": [
            {"q": "Pump Max 1,071 kW, Actual 445.5 kW คิดเป็น Load กี่ %?", "c": ["41.6%", "50%"], "a": "41.6%"},
            {"q": "ถ้าเปิดปั๊ม 445.5 kW เป็นเวลา 13 ชม. ใช้ไฟกี่หน่วย?", "c": ["5,791.5 หน่วย", "13,923 หน่วย"], "a": "5,791.5 หน่วย"},
            {"q": "Cooling Tower 25 ตัว (ตัวละ 5.5kW) เปิดจริง 12 ตัว Actual kW คือ?", "c": ["66 kW", "137.5 kW"], "a": "66 kW"},
            {"q": "ถ้าเปิด Cooling Tower 66 kW เป็นเวลา 13 ชม. ใช้ไฟกี่หน่วย?", "c": ["858 kWh", "1,716 kWh"], "a": "858 kWh"},
            {"q": "ถ้า GPM=3000, CQ1=10 สูตรหา Q_evap(Ton) ที่ถูกคือ?", "c": "(500*3000*10)/12000", "a": "(500*3000*10)/12000"},
            {"q": "Q_evap 1,250 Ton แปลงเป็น kW ได้เท่าไหร่?", "c": ["4,396 kW", "1,250 kW"], "a": "4,396 kW"},
            {"q": "ถ้า CQ วัดจริง 6, Design 10 (Ratio 0.6) ค่า Ideal Power Factor คือ?", "c": ["0.216 (0.6^3)", "0.6"], "a": "0.216 (0.6^3)"},
            {"q": "ผลลัพธ์ Heat Balance +43.8% หมายความว่า?", "c": ["ผิดปกติ (Fail)", "ปกติ (Pass)"], "a": "ผิดปกติ (Fail)"},
            {"q": "การแปลงหน่วย 500 มาจาก?", "c": ["8.33 lb/gal x 60 min", "1 kg/L x 60 s"], "a": "8.33 lb/gal x 60 min"},
            {"q": "ถ้าไม่มี Flow Meter จะเกิดอะไรขึ้น?", "c": ["คำนวณ Heat Balance ไม่ได้", "ไม่เป็นไร"], "a": "คำนวณ Heat Balance ไม่ได้"}
        ]
    }
    
    topic = st.selectbox("เลือกชุดข้อสอบ:", list(quiz_db.keys()))
    if 'qs' not in st.session_state or st.session_state.get('lt') != topic:
        st.session_state.update({'qs':'start', 'lt':topic, 'sc':0})

    with st.form("quiz_f"):
        ans = {}
        for i, it in enumerate(quiz_db[topic]):
            st.markdown(f"**{i+1}. {it['q']}**")
            ans[i] = st.radio("ตอบ:", it['c'], key=f"q{i}", label_visibility="collapsed")
            st.divider()
        if st.form_submit_button("ส่งคำตอบ"):
            sc = sum([1 for i, it in enumerate(quiz_db[topic]) if ans[i]==it['a']])
            st.success(f"คะแนน: {sc}/{len(quiz_db[topic])}")
            if sc == len(quiz_db[topic]): st.balloons()

# --- MAIN RUN ---
def main_app():
    with st.sidebar:
        st.write(f"User: **{st.session_state['user']}**")
        if st.button("Logout"): 
            cookie_manager.delete("sensor_user")
            st.session_state['logged_in'] = False
            st.rerun()
            
    pg = st.sidebar.radio("Menu", ["🌏 Overview", "🏢 CPN AYY", "📖 Learning", "✍️ Quiz"])
    
    if pg == "🌏 Overview":
        st.title("🌏 Overview Dashboard")
        st.info("Mockup Data Area")
        
    elif pg == "🏢 CPN AYY":
        st.title("🏢 CPN AYY Monitor")
        try:
            df = pd.read_csv(CPN_AYY_CSV_URL, on_bad_lines='skip')
            df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
            
            if st.button("🔴 Check Live", type="primary"):
                df['Live'] = fetch_realtime_data_parallel(df)
                st.session_state['live'] = df
            
            d = st.session_state.get('live', df)
            if 'Live' not in d.columns: d['Live'] = 'Unknown'
            st.dataframe(d, use_container_width=True)
        except: st.error("Load Error")

    elif pg == "📖 Learning": render_learning()
    elif pg == "✍️ Quiz": render_quiz()

if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False
check_cookies()
if st.session_state['logged_in']: main_app()
else: login_page()