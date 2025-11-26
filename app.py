import streamlit as st
import google.generativeai as genai
from pypdf import PdfReader
import datetime

# --- 1. 頁面設定 ---
st.set_page_config(
    page_title="日股外電報告產生器",
    page_icon="🇯🇵",
    layout="wide"
)

# --- 2. 自訂 CSS (打造截圖風格) ---
st.markdown("""
    <style>
    /* 全站背景：淺灰藍色，更接近截圖 */
    .stApp {
        background-color: #f0f2f6;
    }
    
    /* 頂部藍色導覽列 */
    .header-container {
        background-color: #1a3682; /* 深藍色 */
        padding: 1.5rem 3rem;
        margin: -6rem -4rem 2rem -4rem; /* 抵銷 Streamlit 預設 padding */
        color: white;
        display: flex;
        justify_content: space-between;
        align_items: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    /* 卡片樣式 - 模仿截圖中的白色圓角卡片 */
    .css-1r6slb0, .stColumn > div > div {
        border-radius: 16px;
    }
    
    /* 自定義卡片容器 */
    .card {
        background-color: white;
        padding: 24px;
        border-radius: 16px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05); /* 輕微陰影 */
        margin-bottom: 24px;
        border: 1px solid #eef0f2;
    }
    
    /* 標題樣式 */
    .card-title {
        font-size: 1.1rem;
        font-weight: 700;
        color: #1f2937;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
    }
    
    .number-badge {
        background-color: #2563eb;
        color: white;
        width: 24px;
        height: 24px;
        border-radius: 50%;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-size: 0.85rem;
        margin-right: 10px;
    }
    
    /* 按鈕樣式 - 藍色與深色 */
    div.stButton > button {
        width: 100%;
        border-radius: 8px;
        height: 48px;
        font-weight: 600;
        border: none;
        transition: all 0.2s;
    }
    
    /* 主要按鈕 (生成) - 亮藍色 */
    div.stButton > button[kind="primary"] {
        background-color: #2563eb; 
        color: white;
    }
    div.stButton > button[kind="primary"]:hover {
        background-color: #1d4ed8;
    }
    
    /* 次要按鈕 (複製) - 深灰藍色 */
    div.stButton > button[kind="secondary"] {
        background-color: #374151;
        color: white;
    }
    div.stButton > button[kind="secondary"]:hover {
        background-color: #1f2937;
    }

    /* 輸入框優化 */
    div[data-testid="stDateInput"] > div, div[data-testid="stSelectbox"] > div {
        background-color: #ffffff;
        border-radius: 8px;
    }
    
    /* 隱藏 Streamlit 預設 footer */
    footer {visibility: hidden;}
    
    </style>
    """, unsafe_allow_html=True)

# --- 3. 頂部藍色 Header ---
st.markdown("""
    <div class="header-container">
        <div style="display:flex; align-items:center;">
            <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-right:15px;"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>
            <div>
                <h2 style="margin:0; color:white; font-size:1.4rem; font-weight:700; line-height:1.2;">日股外電報告產生器</h2>
                <p style="margin:0; color:#bfdbfe; font-size:0.85rem; font-weight:400;">元大證券國際金融部專用格式</p>
            </div>
        </div>
        <div style="background-color:rgba(255,255,255,0.2); padding:6px 16px; border-radius:6px; font-size:0.85rem; font-weight:500;">
            V 1.1 (Auto-Save)
        </div>
    </div>
""", unsafe_allow_html=True)


# --- 4. 邏輯處理 (API Key & 模型) ---
api_key = None
available_models = ["models/gemini-1.5-flash", "models/gemini-1.5-pro"] 

if "GOOGLE_API_KEY" in st.secrets:
    api_key = st.secrets["GOOGLE_API_KEY"]
    try:
        genai.configure(api_key=api_key)
        fetched_models = []
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                fetched_models.append(m.name)
        if fetched_models:
            fetched_models.sort(reverse=True)
            available_models = fetched_models
    except:
        pass 

# --- 5. 介面佈局 ---
# 調整比例：左邊稍微窄一點，右邊寬一點，符合截圖比例
col_left, col_right = st.columns([0.45, 0.55], gap="large")

with col_left:
    # --- 卡片 1: 上傳 ---
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-title"><span class="number-badge">1</span>上傳券商 PDF 報告</div>', unsafe_allow_html=True)
    
    uploaded_files = st.file_uploader(
        "點擊或拖曳 PDF 檔案至此", 
        type=["pdf"], 
        accept_multiple_files=True,
    )
    # 自訂上傳區域樣式 (透過 CSS 比較難完全覆蓋 Streamlit 的 upload widget，但我們讓外框卡片乾淨)
    if uploaded_files:
        st.success(f"已讀取 {len(uploaded_files)} 個檔案")
        
    st.markdown('</div>', unsafe_allow_html=True)

    # --- 卡片 2: 設定 ---
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-title"><span class="number-badge">2</span>設定與模型選擇</div>', unsafe_allow_html=True)
    
    st.caption("報告日期")
    report_date = st.date_input(
        "報告日期",
        datetime.date.today(),
        label_visibility="collapsed"
    )
    
    st.write("") # 空行
    st.caption("Google Gemini 模型選擇")
    selected_model_name = st.selectbox(
        "模型選擇",
        available_models,
        index=0,
        label_visibility="collapsed",
        help="此處替代原本的 API Key 輸入框，請直接選擇模型。"
    )
    
    if not api_key:
        st.warning("⚠️ 請先在 Streamlit Secrets 設定 API Key")
    else:
        st.caption(f"已自動連結 API Key，目前使用: {selected_model_name}")
    
    st.markdown('</div>', unsafe_allow_html=True)

    # --- 按鈕區 (放在卡片外，底部並排) ---
    c1, c2 = st.columns(2)
    with c1:
        # 使用 secondary style 模擬深色按鈕
        show_prompt_btn = st.button("📋 複製完整指令", type="secondary")
    with c2:
        generate_btn = st.button("✨ AI 直接生成", type="primary", disabled=not (uploaded_files and api_key))


# --- 6. 核心生成邏輯 ---
final_prompt = ""
extracted_text = ""

if uploaded_files:
    for pdf_file in uploaded_files:
        try:
            reader = PdfReader(pdf_file)
            file_text = ""
            for page in reader.pages:
                file_text += page.extract_text() + "\n"
            extracted_text += f"\n\n=== 檔案: {pdf_file.name} ===\n{file_text}"
        except Exception as e:
            st.error(f"檔案 {pdf_file.name} 解析失敗: {e}")

    date_str = report_date.strftime("%Y年%m月%d日")
    
    template = f"""
請你扮演「元大證券國際金融部研究員」，根據我上傳的 PDF 券商報告（內容附在最後），整理成「日股外電格式」。
請完整依照以下規範輸出：

【輸出格式規範】
1️⃣ 開頭固定：
早安！{date_str} 日股外電整理 元大證券國金部

2️⃣ 個股格式（每檔公司兩段）
🇯🇵[公司代號 公司名稱 (英文名)]
第一段（150–170字）：
整理美系／日系券商的分析摘要，說明
- 產業趨勢
- 公司展望
- 次季動能
- 成長關鍵
不得提及目標價與評級。

第二段（80–100字）：
第一句一定要寫：
「美系／日系券商將目標價（上調／下調／維持）至 OOOO 日圓，評級維持不變。」
後續補充：
- 券商調整原因（估值、基本面、成本、成長預期）
- 市場關注風險與主軸。

3️⃣ 券商名稱規則
- 若為美系券商 → 統一寫「美系券商」
- 若為日系券商 → 統一寫「日系券商」
不得出現券商名字。

4️⃣ 內容規範
- 不得出現 PDF 檔名或報告完整標題尾巴
- 不得出現主觀推薦語氣
- 數字、年份、日圓金額請保留
- 如為產業主題報告 → 以「產業分析」方式撰寫（篇幅與公司相同）
- 空行與段落格式務必如下範例：

【格式範例如下，請完全複製此排版】

早安！{date_str} 日股外電整理 元大證券國金部
🇯🇵6098 Recruit Holdings (Recruit Holdings)

（150–170字的第一段）

（80–100字的第二段）

🇯🇵8984 大和房屋 REIT (Daiwa House REIT)

（第一段）

（第二段）

以上資料為元大證券依上手提供研究報告摘譯，僅供內部教育訓練使用。

5️⃣ 字數提示
- 每家公司共 230–260 字
- 產業報告可略長但同風格
- 段落之間需空一行（格式務必與範例一致）

【以下是 PDF 內容】：
{extracted_text}
"""
    final_prompt = template

# --- 7. 右側輸出區 ---
with col_right:
    # 這裡的卡片高度設為 min-height: 85vh 以符合截圖中右側長條的樣式
    st.markdown('<div class="card" style="height: 600px; display:flex; flex-direction:column;">', unsafe_allow_html=True)
    
    # 標題與複製按鈕列
    col_header, col_copy = st.columns([0.7, 0.3])
    with col_header:
        st.markdown('<div class="card-title" style="margin-bottom:0;">輸出結果</div>', unsafe_allow_html=True)
    with col_copy:
        pass # 這裡可以放個小按鈕，但 Streamlit 排版限制，我們先保持乾淨
    
    st.write("") # 空行
    
    if show_prompt_btn and final_prompt:
        st.info("指令已生成，請複製下方內容：")
        st.code(final_prompt, language="text")

    if generate_btn:
        status_box = st.empty()
        status_box.info(f"🤖 AI 正在撰寫報告 ({selected_model_name})...")
        
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(selected_model_name)
            response = model.generate_content(final_prompt)
            result_text = response.text
            
            status_box.success("✅ 生成完成！")
            st.text_area("結果", value=result_text, height=500, label_visibility="collapsed")
            
        except Exception as e:
            status_box.error(f"生成失敗: {str(e)}")
            st.error("請確認 API Key 是否正確。")
    else:
        # 空白狀態提示
        st.markdown("""
        <div style="height:100%; display:flex; align-items:center; justify-content:center; color:#9ca3af;">
            <p>等待 PDF 解析與生成...</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)
