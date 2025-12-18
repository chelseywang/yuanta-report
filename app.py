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

# --- 2. 深度 CSS 客製化 ---
st.markdown("""
    <style>
    /* 全站基礎設定 */
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;500;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Microsoft JhengHei', 'Noto Sans TC', sans-serif;
    }
    
    .stApp {
        background-color: #f1f5f9;
    }
    
    .block-container {
        padding-top: 0rem;
        padding-bottom: 2rem;
        padding-left: 3rem;
        padding-right: 3rem;
        max-width: 100%;
    }

    /* Header */
    .header-container {
        background-color: #1e3a8a;
        padding: 1.8rem 4rem;
        margin-left: -3rem;
        margin-right: -3rem;
        margin-bottom: 2rem;
        color: white;
        display: flex;
        justify_content: space-between;
        align_items: center;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    
    /* 卡片樣式 */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: white;
        border-radius: 16px;
        padding: 24px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        border: 1px solid #e2e8f0;
        margin-bottom: 1.5rem;
    }
    
    /* 步驟標題 */
    .step-header {
        display: flex;
        align-items: center;
        margin-bottom: 1.5rem;
        font-size: 1.15rem;
        font-weight: 700;
        color: #1e3a8a;
    }
    
    .step-number {
        background-color: #2563eb;
        color: white;
        width: 32px;
        height: 32px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-right: 12px;
        font-weight: 800;
        font-size: 1rem;
        flex-shrink: 0;
    }

    /* 檔案上傳區 */
    div[data-testid="stFileUploader"] section {
        border: 2px dashed #94a3b8;
        background-color: #ffffff !important;
        border-radius: 12px;
        padding: 40px 20px;
        align-items: center;
        justify-content: center;
        text-align: center;
        position: relative;
    }
    
    div[data-testid="stFileUploader"] section::before {
        content: '';
        display: block;
        width: 64px;
        height: 64px;
        margin: 0 auto 15px auto;
        background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="%232563eb" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M4 14.899A7 7 0 1 1 15.71 8h1.79a4.5 4.5 0 0 1 2.5 8.242"/><path d="M12 12v9"/><path d="m16 16-4-4-4 4"/></svg>');
        background-repeat: no-repeat;
        background-position: center;
    }

    div[data-testid="stFileUploader"] section:hover {
        border-color: #2563eb;
        background-color: #f8fafc;
    }
    
    div[data-testid="stFileUploader"] small {
        font-size: 0.9rem;
        color: #64748b;
    }
    
    /* 輸入框樣式 */
    div[data-baseweb="select"] > div, 
    div[data-baseweb="input"] > div,
    div[data-baseweb="textarea"] > div { /* 增加對 textarea 的支援 */
        background-color: #ffffff !important; 
        border: 1px solid #cbd5e1 !important;
        border-radius: 8px !important;
        box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05) !important;
        padding: 4px;
    }
    
    .stMarkdown label, .stDateInput label, .stSelectbox label, .stTextArea label, .stTextInput label {
        font-weight: 600 !important;
        color: #334155 !important;
        font-size: 0.95rem !important;
        margin-bottom: 0.5rem !important;
    }

    /* 按鈕樣式 */
    div.stButton > button {
        width: 100%;
        height: 50px;
        border-radius: 8px;
        font-weight: 600;
        font-size: 1.05rem;
        border: none;
        transition: all 0.2s;
    }
    
    div.stButton > button[kind="secondary"] {
        background-color: #334155;
        color: white;
    }
    div.stButton > button[kind="secondary"]:hover {
        background-color: #1e293b;
    }
    
    div.stButton > button[kind="primary"] {
        background-color: #2563eb;
        color: white;
        box-shadow: 0 4px 6px -1px rgba(37, 99, 235, 0.3);
    }
    div.stButton > button[kind="primary"]:hover {
        background-color: #1d4ed8;
        transform: translateY(-2px);
        box-shadow: 0 6px 8px -1px rgba(37, 99, 235, 0.4);
    }
    
    /* 輸出結果區塊 */
    div[data-testid="stCodeBlock"] {
        border: 2px solid #2563eb !important;
        border-radius: 8px !important;
        overflow: hidden !important;
    }

    code {
        font-family: 'Microsoft JhengHei', 'Noto Sans TC', sans-serif !important;
        font-size: 12px !important;
        line-height: 1.6 !important;
        white-space: pre-wrap !important;
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    </style>
    """, unsafe_allow_html=True)

# --- 3. 頂部藍色 Header ---
st.markdown("""
    <div class="header-container">
        <div style="display:flex; align-items:center;">
            <div style="background-color:rgba(255,255,255,0.2); padding:10px; border-radius:10px; margin-right:15px;">
                <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>
            </div>
            <div>
                <h1 style="margin:0; font-size:1.6rem; font-weight:700; letter-spacing:0.5px;">日股外電報告產生器</h1>
                <p style="margin:4px 0 0 0; color:#cbd5e1; font-size:0.9rem;">元大證券國際金融部專用格式</p>
            </div>
        </div>
        <div style="background-color:rgba(255,255,255,0.15); padding:6px 16px; border-radius:20px; font-size:0.85rem; font-weight:500;">
            V 7.0 (Auto-Title)
        </div>
    </div>
""", unsafe_allow_html=True)

# --- 4. 邏輯處理 ---
api_key = None
available_models = ["gemini-2.0-flash-exp", "gemini-1.5-flash", "gemini-1.5-pro"]

if "GOOGLE_API_KEY" in st.secrets:
    api_key = st.secrets["GOOGLE_API_KEY"]
    try:
        genai.configure(api_key=api_key)
        fetched_models = []
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                name = m.name.replace("models/", "")
                fetched_models.append(name)
        
        if fetched_models:
            fetched_models.sort(reverse=True)
            available_models = fetched_models
            if "gemini-2.0-flash-exp" not in available_models:
                available_models.insert(0, "gemini-2.0-flash-exp")
    except Exception as e:
        pass 

# --- 預設 Prompt 模板 (這裡使用 {date} 作為佔位符) ---
DEFAULT_PROMPT_TEMPLATE = """請你扮演「元大證券國際金融部研究員」，根據我上傳的 PDF 券商報告（內容附在最後），整理成「日股外電格式」。
請完整依照以下規範輸出，排版格式與空行必須嚴格遵守：

【輸出格式規範】
1️⃣ 開頭固定：
早安！{date}
日股外電整理 元大證券國金部

(⚠️注意：此處空兩行)

2️⃣ 個股格式（每檔公司兩段，請嚴格遵守空格行數）

🇯🇵[公司代號 公司名稱 (英文名)]
第一段（150–170字）：(⚠️注意：這一段文字必須「緊接」在公司名稱的下一行，中間「不可」有空行)。
內容整理美系／日系券商的分析摘要，說明產業趨勢、公司展望、次季動能、成長關鍵。不得提及目標價與評級。

(⚠️注意：第一段與第二段之間必須「空一行」)

第二段（80–100字）：
第一句一定要寫：「美系／日系券商將目標價（上調／下調／維持）至 OOOO 日圓，評級維持不變。」
後續補充：券商調整原因、市場關注風險與主軸。

(⚠️注意：不同公司之間請務必「空兩行」區隔)

3️⃣ 範例參考（請完全複製此排版間距，尤其是換行）：

🇯🇵7181 Japan Post Insurance (Japan Post Insurance)
日系券商指出，Japan Post Insurance在新的中期業務計畫中... (緊接上一行，無空行)
(略...)
...有望在新中期計畫中更注重股息回報。
(此處空一行)
日系券商將目標價從 4,700 日圓上調至 5,000 日圓，評級維持不變。...
(略...)
...以及市場狀況急劇惡化對盈利及內含價值的影響。


(⚠️注意：此處空兩行)


🇯🇵6501 Hitachi (Hitachi)
美系券商參訪Hitachi Energy在加拿大魁北克的工廠後... (緊接上一行，無空行)
(略...)
...並計劃至2028年3月增加15,000名員工以提升產能。
(此處空一行)
美系券商將目標價維持在 5,900 日圓，評級維持不變。...
(略...)
...以及中國新建設需求疲軟等。


(⚠️注意：最後這句免責聲明前也要空兩行)


以上資料為元大證券依上手提供研究報告摘譯，僅供內部教育訓練使用。"""

# --- 5. 介面佈局 ---
col_left, col_right = st.columns([0.45, 0.55], gap="large")

with col_left:
    # === 卡片 1: 上傳 ===
    with st.container(border=True):
        st.markdown("""
            <div class="step-header">
                <div class="step-number">1</div>
                <div>上傳券商 PDF 報告</div>
            </div>
        """, unsafe_allow_html=True)
        
        uploaded_files = st.file_uploader(
            "將 PDF 拖曳至此框框中，或點擊選取檔案 (支援多檔)", 
            type=["pdf"], 
            accept_multiple_files=True,
        )
        
        if uploaded_files:
            st.success(f"✅ 已成功讀取 {len(uploaded_files)} 份檔案")

    # === 卡片 2: 設定 (含自動標題功能) ===
    with st.container(border=True):
        st.markdown("""
            <div class="step-header">
                <div class="step-number">2</div>
                <div>設定與模型選擇</div>
            </div>
        """, unsafe_allow_html=True)
        
        # 1. 日期選擇器
        report_date = st.date_input("報告日期", datetime.date.today())
        
        # --- ✨ 新增功能：自動標題產生器 ---
        # 格式化日期為 YYYY年MM月DD日
        date_str_title = report_date.strftime("%Y年%m月%d日")
        # 組合標題字串
        auto_title = f"早安！{date_str_title} 日股外電整理 元大證券國金部"
        
        # 顯示可複製的文字框
        st.text_input(
            "📧 信件/訊息標題 (已與日期連動，可直接複製)", 
            value=auto_title,
            help="這個標題會隨著您上方選擇的日期自動更新。"
        )
        # ----------------------------------
        
        st.write("") 
        
        # 模型選擇
        selected_model_name = st.selectbox(
            "Google Gemini 模型 (自動偵測可用清單) (手動選擇Gemini-flash-2.5)",
            available_models,
            index=0, 
            help="系統已自動連結 API 並列出所有可用模型，若遇額度問題請切換其他版本。"
        )
        
        if api_key:
            st.caption(f"✓ API 連線正常，共偵測到 {len(available_models)} 個模型")
        else:
            st.error("⚠️ 未偵測到 Secrets API Key")

    # === 卡片 3 (自定義 Prompt) ===
    with st.container(border=True):
        # 使用 Expander 把長長的 Prompt 收起來，保持介面整潔
        with st.expander("✏️ 自定義 Prompt 指令 (進階設定)", expanded=False):
            st.caption("您可以在此修改 AI 的指令模板。`{date}` 會自動替換為上方選擇的日期。")
            user_custom_prompt = st.text_area(
                "Prompt 內容編輯",
                value=DEFAULT_PROMPT_TEMPLATE,
                height=300,
                label_visibility="collapsed"
            )

    # === 按鈕區 ===
    c1, c2 = st.columns(2)
    with c1:
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
    
    # --- 組合最終 Prompt ---
    # 1. 取得使用者(或預設)的指令模板
    # 2. 將 {date} 替換為實際日期
    # 3. 在最後面加上 PDF 內容
    
    instruction_part = user_custom_prompt.replace("{date}", date_str)
    
    final_prompt = f"""{instruction_part}

【以下是 PDF 內容】：
{extracted_text}
"""

# --- 7. 右側輸出區 ---
with col_right:
    with st.container(border=True):
        st.markdown('<div class="step-header">輸出結果 (請注意目標價、日期、券商標記是否符合原文)</div>', unsafe_allow_html=True)
        
        if show_prompt_btn and final_prompt:
            st.info("指令已生成，請點擊右上角複製：")
            st.code(final_prompt, language="text")

        if generate_btn:
            status_box = st.empty()
            with status_box.container():
                st.image("https://i.gifer.com/ZKZg.gif", width=100)
                st.info(f"🤖 AI 正在努力奔跑分析中... ({selected_model_name})，請稍候片刻！")
            
            try:
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel(selected_model_name)
                response = model.generate_content(final_prompt)
                result_text = response.text
                
                status_box.empty()
                st.success("✅ 報告生成完成！請點擊下方藍色框框右上角的 📄 圖示進行複製")
                
                st.code(result_text, language="text")
                
            except Exception as e:
                status_box.error(f"生成失敗: {str(e)}")
                st.error("請確認 API Key 是否正確。")
        
        elif not show_prompt_btn:
             st.markdown("""
            <div style="height:550px; display:flex; flex-direction:column; align-items:center; justify-content:center; color:#94a3b8; background-color:white;">
                <p style="font-size:1.2rem; font-weight:500; color:#cbd5e1;">等待 PDF 解析與生成...</p>
                <p style="font-size:0.9rem; color:#94a3b8; margin-top:10px;">請在左側上傳檔案並按下「AI 直接生成」</p>
            </div>
            """, unsafe_allow_html=True)
