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

# --- 2. 深度 CSS 客製化 (完美還原截圖風格 + 圖示) ---
st.markdown("""
    <style>
    /* 全站字體與背景：淺灰藍色 */
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;500;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Noto Sans TC', sans-serif;
    }
    
    .stApp {
        background-color: #f1f5f9; /* 截圖中的淺灰藍底色 */
    }
    
    /* 移除頂部預設空白，讓 Header 貼頂 */
    .block-container {
        padding-top: 0rem;
        padding-bottom: 2rem;
        padding-left: 3rem;
        padding-right: 3rem;
        max-width: 100%;
    }

    /* --- 頂部深藍色 Header --- */
    .header-container {
        background-color: #1e3a8a; /* 元大深藍 */
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
    
    /* --- 白色卡片樣式 (針對 st.container) --- */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: white;
        border-radius: 16px; /* 圓角 */
        padding: 24px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05); /* 輕微浮起陰影 */
        border: 1px solid #e2e8f0;
        margin-bottom: 1.5rem;
    }
    
    /* --- 步驟標題 (藍色圓圈數字) --- */
    .step-header {
        display: flex;
        align-items: center;
        margin-bottom: 1.5rem;
        font-size: 1.15rem;
        font-weight: 700;
        color: #1e3a8a; /* 深藍字體 */
    }
    
    .step-number {
        background-color: #2563eb; /* 亮藍色圓圈 */
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

    /* --- 檔案上傳區 (模仿截圖中的大虛線框 + 圖示) --- */
    div[data-testid="stFileUploader"] section {
        border: 2px dashed #94a3b8; /* 灰色虛線 */
        background-color: #ffffff !important;  /* 改為超白底 */
        border-radius: 12px;
        padding: 40px 20px; /* 加大高度 */
        align-items: center;
        justify-content: center;
        text-align: center;
        position: relative; /* 為了放圖示 */
    }
    
    /* 使用 CSS 偽元素加入雲朵箭頭圖示 */
    div[data-testid="stFileUploader"] section::before {
        content: '';
        display: block;
        width: 64px;
        height: 64px;
        margin: 0 auto 15px auto;
        /* 使用 SVG 圖示 */
        background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="%232563eb" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M4 14.899A7 7 0 1 1 15.71 8h1.79a4.5 4.5 0 0 1 2.5 8.242"/><path d="M12 12v9"/><path d="m16 16-4-4-4 4"/></svg>');
        background-repeat: no-repeat;
        background-position: center;
    }

    div[data-testid="stFileUploader"] section:hover {
        border-color: #2563eb; /* 滑鼠移過去變藍色 */
        background-color: #f8fafc; /* 滑鼠移上去時稍微變灰一點點，增加互動感 */
    }
    
    /* 隱藏上傳按鈕的預設醜邊框，改用文字提示 */
    div[data-testid="stFileUploader"] small {
        font-size: 0.9rem;
        color: #64748b;
    }
    
    /* --- 輸入框樣式 (純白立體底框) --- */
    div[data-baseweb="select"] > div, 
    div[data-baseweb="input"] > div {
        background-color: #ffffff !important; 
        border: 1px solid #cbd5e1 !important;
        border-radius: 8px !important;
        box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05) !important;
        padding: 4px;
    }
    
    .stMarkdown label, .stDateInput label, .stSelectbox label {
        font-weight: 600 !important;
        color: #334155 !important;
        font-size: 0.95rem !important;
        margin-bottom: 0.5rem !important;
    }

    /* --- 按鈕樣式 (底部並排) --- */
    div.stButton > button {
        width: 100%;
        height: 50px; /* 加高按鈕 */
        border-radius: 8px;
        font-weight: 600;
        font-size: 1.05rem;
        border: none;
        transition: all 0.2s;
    }
    
    /* 複製指令 (深灰藍) */
    div.stButton > button[kind="secondary"] {
        background-color: #334155;
        color: white;
    }
    div.stButton > button[kind="secondary"]:hover {
        background-color: #1e293b;
    }
    
    /* AI 生成 (亮藍色) */
    div.stButton > button[kind="primary"] {
        background-color: #2563eb;
        color: white;
        box-shadow: 0 4px 6px -1px rgba(37, 99, 235, 0.3);
    }
    div.stButton > button[kind="primary"]:hover {
        background-color: #1d4ed8;
        transform: translateY(-2px); /* 微浮效果 */
        box-shadow: 0 6px 8px -1px rgba(37, 99, 235, 0.4);
    }
    
    /* 隱藏多餘元素 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    </style>
    """, unsafe_allow_html=True)

# --- 3. 頂部藍色 Header (HTML) ---
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
            V 6.2 Pro
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

# --- 5. 介面佈局 (左 45% : 右 55%) ---
col_left, col_right = st.columns([0.45, 0.55], gap="large")

with col_left:
    # === 卡片 1: 上傳 PDF 報告 ===
    with st.container(border=True):
        # 使用 HTML 渲染帶有圓圈數字的標題
        st.markdown("""
            <div class="step-header">
                <div class="step-number">1</div>
                <div>上傳券商 PDF 報告</div>
            </div>
        """, unsafe_allow_html=True)
        
        # 上傳元件 (文字提示修改為更直觀)
        uploaded_files = st.file_uploader(
            "將 PDF 拖曳至此框框中，或點擊選取檔案 (支援多檔)", 
            type=["pdf"], 
            accept_multiple_files=True,
        )
        
        if uploaded_files:
            st.success(f"✅ 已成功讀取 {len(uploaded_files)} 份檔案")

    # === 卡片 2: 設定與模型選擇 ===
    with st.container(border=True):
        st.markdown("""
            <div class="step-header">
                <div class="step-number">2</div>
                <div>設定與模型選擇</div>
            </div>
        """, unsafe_allow_html=True)
        
        # 報告日期
        report_date = st.date_input("報告日期", datetime.date.today())
        
        st.write("") # 增加一點間距
        
        # 模型選擇 (取代原本的 API Key 輸入框位置)
        selected_model_name = st.selectbox(
            "Google Gemini 模型 (自動連結 API)",
            available_models,
            index=0,
            help="系統已自動連結 Secrets 中的 API Key，請選擇要使用的模型版本"
        )
        
        if api_key:
            st.caption("✓ API Key 連線正常")
        else:
            st.error("⚠️ 未偵測到 Secrets API Key")

    # === 按鈕區 ===
    c1, c2 = st.columns(2)
    with c1:
        # 複製指令 (深色按鈕)
        show_prompt_btn = st.button("📋 複製完整指令", type="secondary")
    with c2:
        # AI 生成 (亮藍色按鈕)
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

# --- 7. 右側輸出區 (卡片樣式 + 一鍵複製 + 跑步動畫) ---
with col_right:
    with st.container(border=True):
        st.markdown('<div class="step-header">輸出結果</div>', unsafe_allow_html=True)
        
        # 情況 A：只顯示指令
        if show_prompt_btn and final_prompt:
            st.info("指令已生成，請點擊右上角複製：")
            st.code(final_prompt, language="text")

        # 情況 B：AI 生成結果 (加入動畫)
        if generate_btn:
            # 1. 建立一個空的 placeholder
            status_box = st.empty()
            
            # 2. 顯示跑步動畫與文字
            with status_box.container():
                # 使用一個網路上的跑步 GIF (這是一個通用的範例連結)
                st.image("https://i.gifer.com/ZKZg.gif", width=100)
                st.info(f"🤖 AI 正在努力奔跑分析中... ({selected_model_name})，請稍候片刻！")
            
            try:
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel(selected_model_name)
                response = model.generate_content(final_prompt)
                result_text = response.text
                
                # 3. 生成完成後，清空 placeholder，顯示結果
                status_box.empty()
                st.success("✅ 報告生成完成！")
                
                # 使用 st.code 呈現結果，右上角會自動出現複製按鈕
                st.code(result_text, language="text")
                
            except Exception as e:
                status_box.error(f"生成失敗: {str(e)}")
                st.error("請確認 API Key 是否正確。")
        
        # 情況 C：等待中 (空白狀態)
        elif not show_prompt_btn:
             st.markdown("""
            <div style="height:550px; display:flex; flex-direction:column; align-items:center; justify-content:center; color:#94a3b8; background-color:white;">
                <p style="font-size:1.2rem; font-weight:500; color:#cbd5e1;">等待 PDF 解析與生成...</p>
                <p style="font-size:0.9rem; color:#94a3b8; margin-top:10px;">請在左側上傳檔案並按下「AI 直接生成」</p>
            </div>
            """, unsafe_allow_html=True)
