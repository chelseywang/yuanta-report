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
    div[data-baseweb="textarea"] > div { 
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
    
    /* ✨ V 7.5 修正：
       為了在白色的卡片上能看見框框，我們必須用「顏色」把它框出來
    */
    
    div[data-testid="stCodeBlock"] {
        /* 1. 給它一個極淡的灰藍底色，跟純白背景區分 */
        background-color: #f8fafc !important; 
        
        /* 2. 給它一個「深藍色」的粗邊框，這樣絕對看得見 */
        border: 2px solid #1e3a8a !important; 
        
        border-radius: 8px !important;
        padding: 10px !important;
        margin-top: 5px !important;
    }

    div[data-testid="stCodeBlock"] pre {
        background-color: transparent !important;
    }

    div[data-testid="stCodeBlock"] code {
        color: #0f172a !important; /* 深色文字 */
        background-color: transparent !important;
        font-family: 'Microsoft JhengHei', 'Noto Sans TC', sans-serif !important;
        font-size: 16px !important;
        font-weight: 700 !important;
    }

    /* 確保複製按鈕是深色的 */
    div[data-testid="stCodeBlock"] button {
        color: #1e3a8a !important;
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
            V 7.5 (藍框顯眼版)
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
DEFAULT_PROMPT_TEMPLATE = """請你扮演「元大證券國際金融部研究員」，根據我上傳的 PDF 券商研究報告，整理成「日股外電格式」。

請僅根據 PDF 報告內容進行整理，不可自行補充報告未提及的資訊或投資觀點。若有多份 PDF，請每份報告各整理一檔公司。

請完整依照以下規範輸出，尤其注意「公司名稱格式、字數、空行、目標價與評級變動」，不可自行更改排版。

1. 開頭固定格式

早安！{date}
日股外電整理 
元大證券國金部產品科


注意：
- 日期使用 YYYY/MM/DD 格式。
- 「元大證券國金部」後方必須空兩行，再開始第一家公司。
- 不需要額外加入標題、前言或說明。


2. 公司標題格式

🇯🇵[公司代號] [英文公司名稱]([中文公司名稱])

例如：

🇯🇵8086 Nipro(尼普洛)

🇯🇵9041 Kintetsu Group Holdings(近鐵集團控股)

注意：
- 英文公司名稱後方加入中文翻譯名稱。
- 中文公司名稱必須使用半形括號 ()，禁止使用全形括號 （）。
- 股票代號放最前方。
- 公司標題下一行直接接第一段，不可空行。


3. 第一段格式：券商研究摘要

字數：150–170字。

內容需整理券商對公司的核心分析，包括：

- 最新季度財報表現，以及是否符合／優於／低於券商或市場預期。
- 主要事業或部門表現。
- 目前產業趨勢及公司營運環境。
- 下一季或下半年主要成長動能。
- 未來獲利成長關鍵。
- 若報告有提及，可加入成本、價格、需求、產品週期、資本支出等重要因素。

撰寫原則：
- 使用「美系券商指出」或「日系券商指出」作為開頭。
- 若報告來自 J.P. Morgan、Morgan Stanley、Goldman Sachs、BofA、Citi 等美系券商，統一寫「美系券商指出」。
- 若來自 Nomura、Daiwa、Mizuho、SMBC Nikko 等日系券商，統一寫「日系券商指出」。
- 採法人研究報告語氣，精簡、客觀、資訊密度高。
- 不得在第一段提及「目標價」或「評級」。
- 不需要介紹公司基本資料。
- 避免逐條翻譯原文，應重新整理成連貫的一段中文。

排版：

🇯🇵8086 Nipro(尼普洛)
美系券商指出，Nipro首季營業利益……


4. 第一段與第二段之間

第一段結束後必須「空一行」，再開始第二段。

不可連在一起。


5. 第二段格式：目標價、評級與風險

字數：80–100字。

第一句必須依照 PDF 中「本次報告相較前次報告」的目標價與評級變化撰寫。

情況 A：目標價有上調

「美系／日系券商將目標價從 XXXX 日圓上調至 OOOO 日圓，評級維持[評級]。」

若評級也調升：

「美系／日系券商將目標價從 XXXX 日圓上調至 OOOO 日圓，評級調升為[評級]。」


情況 B：目標價有下調

「美系／日系券商將目標價從 XXXX 日圓下調至 OOOO 日圓，評級維持[評級]。」

若評級也調降：

「美系／日系券商將目標價從 XXXX 日圓下調至 OOOO 日圓，評級調降為[評級]。」


情況 C：目標價維持不變

「美系／日系券商將目標價維持在 OOOO 日圓，評級維持[評級]。」


情況 D：目標價不變，但評級改變

「美系／日系券商將目標價維持在 OOOO 日圓，評級調升為[評級]。」

或

「美系／日系券商將目標價維持在 OOOO 日圓，評級調降為[評級]。」


評級中文統一翻譯：

Overweight → 買進
Buy → 買進
Outperform → 優於大盤
Neutral → 中立
Equal-weight → 中立
Hold → 持有
Underweight → 減碼
Sell → 賣出

若 PDF 本身使用其他評級名稱，請依原文語意翻譯。


第二句之後補充：
- 券商維持或調整目標價／評級的主要原因。
- 市場目前關注的核心投資主軸。
- 主要下行風險或後續觀察重點。

注意：
- 必須先確認 PDF 中前一次目標價與評級，不能只看到本次目標價就自行判斷為「維持」。
- 若報告內有 Rating / Price Target History，應以該表格判斷前次與本次變化。
- 不可自行推測目標價是否上調或下調。


6. 不同公司之間的空行

每家公司第二段結束後，必須「空兩行」，才開始下一家公司。

格式如下：

美系券商將目標價維持在 1,600 日圓，評級維持中立。……



🇯🇵9041 Kintetsu Group Holdings(近鐵集團控股)
美系券商指出，……


7. 最後固定免責聲明

最後一家公司第二段結束後，必須「空兩行」，再放以下固定文字：

以上資料為元大證券依上手提供研究報告摘譯，僅供內部教育訓練使用。


8. 完整排版範例

早安！2026/08/11
日股外電整理 元大證券國金部


🇯🇵7181 Japan Post Insurance(日本郵政保險)
日系券商指出，Japan Post Insurance在新的中期業務計畫中，預計進一步改善資本效率，並透過調整資產配置提高投資收益。隨日本利率環境正常化，公司利差收入具改善空間，同時持續強化保障型商品銷售與成本控管，預期中期獲利能力逐步提升，未來資本配置及股東回報政策將成為市場主要關注焦點。

日系券商將目標價從 4,700 日圓上調至 5,000 日圓，評級維持買進。該調整主因看好資本配置效率提升與穩定配息政策，後續則需留意日本利率波動對內含價值及保險負債評價的影響。


🇯🇵6501 Hitachi(日立製作所)
美系券商參訪Hitachi Energy在加拿大魁北克的工廠後指出，全球電網設備需求持續強勁，主要受再生能源併網、資料中心用電增加與電網汰換需求推動。公司目前訂單能見度維持高檔，並積極擴充變壓器及相關設備產能，預計持續增加人力與資本支出，以因應全球電力基礎建設的長期成長需求。

美系券商將目標價維持在 5,900 日圓，評級維持中立。儘管能源事業訂單強勁，但電網設備產能擴張仍需時間，短期獲利上行空間有限，另需關注中國新建設需求疲弱對工業相關業務的影響。


以上資料為元大證券依上手提供研究報告摘譯，僅供內部教育訓練使用。


9. 最終檢查

輸出前請自行確認：

- 公司名稱是否為「英文名稱(中文名稱)」。
- 所有公司中文名稱皆使用半形括號 ()。
- 第一段是否為150–170字。
- 第二段是否為80–100字。
- 第一段沒有目標價與評級。
- 第二段第一句有明確寫出目標價及評級。
- 目標價「上調／下調／維持」是否有根據前次券商紀錄正確判斷。
- 公司標題與第一段之間沒有空行。
- 第一段與第二段之間空一行。
- 不同公司之間空兩行。
- 免責聲明前空兩行。
- 不得加入 PDF 未提及的資訊。
- 最終只輸出「日股外電成品」，不要額外解釋整理過程。"""

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

    # === 卡片 2: 設定 (含標題複製功能 - 藍框版) ===
    with st.container(border=True):
        st.markdown("""
            <div class="step-header">
                <div class="step-number">2</div>
                <div>設定與模型選擇</div>
            </div>
        """, unsafe_allow_html=True)
        
        # 1. 日期選擇器
        report_date = st.date_input("報告日期", datetime.date.today())
        
        # --- ✨ NEW: 標題複製區 ---
        st.write("")
        st.markdown("**👇 信件標題 (點擊右上角圖示即可複製)**")
        
        # 格式化日期：YYYY年MM月DD日
        formatted_date = report_date.strftime("%Y年%m月%d日")
        # 組合標題
        title_text = f"早安！{formatted_date} 日股外電整理 元大證券國金部"
        
        # 使用 st.code 呈現
        st.code(title_text, language="text")
        # -----------------------------------------------
        
        st.write("") 
        
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

