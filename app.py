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

# --- 2. 自訂 CSS (深度客製化版面) ---
st.markdown("""
    <style>
    /* 1. 全站設定：背景淺灰 */
    .stApp {
        background-color: #f0f2f6;
    }
    
    /* 2. 移除 Streamlit 預設頂部空白，讓藍色 Header 滿版 */
    .block-container {
        padding-top: 0rem;
        padding-bottom: 2rem;
        padding-left: 3rem;
        padding-right: 3rem;
        max-width: 100%;
    }
    
    /* 3. 頂部藍色導覽列 (滿版設計) */
    .header-container {
        background-color: #1a3682; /* 深藍色 */
        padding: 2rem 4rem;
        margin-left: -3rem;  /* 抵銷 block-container 的 padding */
        margin-right: -3rem; /* 抵銷 block-container 的 padding */
        margin-bottom: 2rem;
        color: white;
        display: flex;
        justify_content: space-between;
        align_items: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.15);
    }
    
    /* 4. 白色卡片容器 (針對 st.container) */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #ffffff;
        border-radius: 12px;
        padding: 24px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
        border: 1px solid #e5e7eb;
        margin-bottom: 1rem;
    }
    
    /* 5. 特別強調：輸入框的白色底框設計 */
    div[data-testid="stDateInput"], div[data-testid="stSelectbox"] {
        background-color: #f8fafc; /* 非常淡的灰底，區分層次 */
        padding: 12px;
        border-radius: 8px;
        border: 1px solid #e2e8f0;
        margin-bottom: 12px;
    }
    
    /* 讓輸入框標籤文字明顯一點 */
    .stMarkdown label, .stDateInput label, .stSelectbox label {
        font-weight: 600 !important;
        color: #334155 !important;
        font-size: 0.95rem !important;
    }
    
    /* 6. 卡片標題樣式 */
    .card-header {
        font-size: 1.1rem;
        font-weight: 700;
        color: #1e3a8a;
        margin-bottom: 1.2rem;
        display: flex;
        align-items: center;
    }
    
    /* 藍色圓形數字 */
    .number-badge {
        background-color: #2563eb;
        color: white;
        width: 28px;
        height: 28px;
        border-radius: 50%;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-size: 0.9rem;
        margin-right: 12px;
        font-weight: bold;
    }
    
    /* 7. 按鈕樣式優化 */
    div.stButton > button {
        width: 100%;
        border-radius: 8px;
        height: 48px;
        font-weight: 600;
        font-size: 1rem;
        border: none;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        transition: all 0.2s;
    }
    div.stButton > button[kind="primary"] {
        background-color: #2563eb; 
        color: white;
    }
    div.stButton > button[kind="primary"]:hover {
        background-color: #1d4ed8;
        transform: translateY(-1px);
    }
    div.stButton > button[kind="secondary"] {
        background-color: #475569;
        color: white;
    }
    div.stButton > button[kind="secondary"]:hover {
        background-color: #334155;
    }
    
    /* 隱藏 Footer */
    footer {visibility: hidden;}
    header {visibility: hidden;} /* 隱藏 Streamlit 預設右上角選單漢堡 */
    </style>
    """, unsafe_allow_html=True)

# --- 3. 頂部藍色 Header (HTML) ---
st.markdown("""
    <div class="header-container">
        <div style="display:flex; align-items:center;">
            <div style="background-color:rgba(255,255,255,0.15); padding:10px; border-radius:10px; margin-right:15px;">
                <svg xmlns="http://www.w3.org/2000/svg" width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>
            </div>
            <div>
                <h2 style="margin:0; color:white; font-size:1.4rem; font-weight:700; letter-spacing: 1px;">日股外電報告產生器</h2>
                <p style="margin:5px 0 0 0; color:#bfdbfe; font-size:0.85rem; font-weight:400;">元大證券國際金融部專用格式</p>
            </div>
        </div>
        <div style="text-align:right;">
            <span style="background-color:rgba(255,255,255,0.2); padding:5px 12px; border-radius:20px; font-size:0.8rem; font-weight:500;">V 5.7</span>
        </div>
    </div>
""", unsafe_allow_html=True)

# --- 4. 邏輯處理 ---
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
col_left, col_right = st.columns([0.45, 0.55], gap="large")

with col_left:
    # --- 卡片 1: 上傳 ---
    with st.container(border=True):
        st.markdown('<div class="card-header"><span class="number-badge">1</span>上傳券商 PDF 報告</div>', unsafe_allow_html=True)
        uploaded_files = st.file_uploader(
            "點擊或拖曳 PDF 檔案至此", 
            type=["pdf"], 
            accept_multiple_files=True,
        )
        if uploaded_files:
            st.success(f"已讀取 {len(uploaded_files)} 個檔案")

    # --- 卡片 2: 設定 ---
    with st.container(border=True):
        st.markdown('<div class="card-header"><span class="number-badge">2</span>設定與模型選擇</div>', unsafe_allow_html=True)
        
        # 報告日期 (會被 CSS 包成白色底框)
        report_date = st.date_input(
            "報告日期",
            datetime.date.today()
        )
        
        # 模型選擇 (會被 CSS 包成白色底框)
        selected_model_name = st.selectbox(
            "Google Gemini 模型 (自動連結 API)",
            available_models,
            index=0,
            help="選擇不同的模型可能會影響生成速度與詳細程度"
        )
        
        if api_key:
            st.caption(f"✓ API Key 狀態正常")
        else:
            st.error("⚠️ 未偵測到 Secrets API Key")

    # --- 按鈕區 ---
    c1, c2 = st.columns(2)
    with c1:
        show_prompt_btn = st.button("📋 複製完整指令", type="secondary")
    with c2:
        generate_btn = st.button("✨ AI 直接生成", type="primary", disabled=not (uploaded_files and api_key))

# --- 6. 生成邏輯 ---
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
    with st.container(border=True):
        st.markdown('<div class="card-header" style="margin-bottom:0.5rem;">輸出結果 (可一鍵複製)</div>', unsafe_allow_html=True)
        
        # 1. 如果有按下「複製完整指令」
        if show_prompt_btn and final_prompt:
            st.info("指令已生成：")
            st.code(final_prompt, language="text") # st.code 自帶複製按鈕

        # 2. 如果按下「生成」
        if generate_btn:
            status_box = st.empty()
            status_box.info(f"🤖 AI 正在撰寫報告 ({selected_model_name})...")
            
            try:
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel(selected_model_name)
                response = model.generate_content(final_prompt)
                result_text = response.text
                
                status_box.success("✅ 生成完成！")
                
                # --- 關鍵修改：使用 st.code 替代 st.text_area 以實現一鍵複製 ---
                # language="text" 讓它顯示為純文字，右上角會有 Copy 按鈕
                st.code(result_text, language="text")
                
            except Exception as e:
                status_box.error(f"生成失敗: {str(e)}")
                st.error("請確認 API Key 是否正確。")
        
        # 3. 預設空狀態
        elif not show_prompt_btn:
             st.markdown("""
            <div style="height:550px; display:flex; align-items:center; justify-content:center; color:#9ca3af; background-color:white;">
                <p>等待 PDF 解析與生成...</p>
            </div>
            """, unsafe_allow_html=True)
