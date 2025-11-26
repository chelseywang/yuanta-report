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
    /* 全站背景：淺灰 */
    .stApp {
        background-color: #f3f4f6;
    }
    
    /* 頂部藍色導覽列模擬 */
    .header-container {
        background-color: #1e3a8a;
        padding: 1.5rem 2rem;
        margin: -6rem -4rem 2rem -4rem; /* 抵銷 Streamlit 預設 padding */
        color: white;
        display: flex;
        justify_content: space-between;
        align_items: center;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    
    /* 卡片樣式 */
    .css-1r6slb0, .stColumn > div > div {
        border-radius: 12px;
    }
    
    /* 自定義卡片容器 (透過 markdown 插入 div) */
    .card {
        background-color: white;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06);
        margin-bottom: 20px;
        border: 1px solid #e5e7eb;
    }
    
    /* 調整按鈕樣式 */
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        height: 3em;
        font-weight: bold;
    }
    
    /* 輸入框與選單背景 */
    div[data-testid="stDateInput"], div[data-testid="stSelectbox"] {
        background-color: white;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 頂部藍色 Header ---
st.markdown("""
    <div class="header-container">
        <div>
            <h2 style="margin:0; color:white; font-size:1.5rem; display:inline-block; vertical-align:middle;">📄 日股外電報告產生器</h2>
            <p style="margin:0; color:#bfdbfe; font-size:0.8rem;">元大證券國際金融部專用格式</p>
        </div>
        <div style="background-color:#1d4ed8; padding:5px 15px; border-radius:20px; font-size:0.8rem;">
            V 5.4 (Auto-Detect)
        </div>
    </div>
""", unsafe_allow_html=True)


# --- 4. 邏輯處理 (API Key & 模型) ---
api_key = None
available_models = ["models/gemini-1.5-flash", "models/gemini-1.5-pro"] # 預設清單

# 嘗試取得 Key
if "GOOGLE_API_KEY" in st.secrets:
    api_key = st.secrets["GOOGLE_API_KEY"]
    # 嘗試自動抓取模型清單
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
        pass # 若抓取失敗則使用預設清單

# --- 5. 介面佈局 (左 4 : 右 6) ---
col_left, col_right = st.columns([0.4, 0.6], gap="medium")

with col_left:
    # --- 卡片 1: 上傳 ---
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### ❶ 上傳券商 PDF 報告")
    uploaded_files = st.file_uploader(
        "點擊或拖曳 PDF 檔案至此", 
        type=["pdf"], 
        accept_multiple_files=True,
        label_visibility="collapsed"
    )
    if uploaded_files:
        st.success(f"已上傳 {len(uploaded_files)} 份檔案")
    st.markdown('</div>', unsafe_allow_html=True)

    # --- 卡片 2: 設定 (日期 + 模型) ---
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### ❷ 設定與模型")
    
    st.caption("報告日期")
    report_date = st.date_input(
        "報告日期",
        datetime.date.today(),
        label_visibility="collapsed"
    )
    
    st.caption("選擇 AI 模型 (取代 API Key)")
    selected_model_name = st.selectbox(
        "選擇模型",
        available_models,
        index=0,
        label_visibility="collapsed",
        help="系統已自動帶入 Secrets 中的 Key，請直接選擇要使用的模型。"
    )
    
    if not api_key:
        st.error("⚠️ 未偵測到 Secrets Key，請在 Streamlit 後台設定。")
    
    st.markdown('</div>', unsafe_allow_html=True)

    # --- 按鈕區 ---
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        show_prompt = st.checkbox("顯示完整指令", value=False)
    with col_btn2:
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
    # 模擬卡片樣式
    st.markdown('<div class="card" style="min-height: 500px;">', unsafe_allow_html=True)
    st.markdown("### 📝 輸出結果")
    
    if show_prompt and final_prompt:
        st.info("指令預覽：")
        st.code(final_prompt, language="text")

    if generate_btn:
        status_box = st.empty()
        status_box.info(f"🤖 正在使用 {selected_model_name} 模型生成報告，請稍候...")
        
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(selected_model_name)
            response = model.generate_content(final_prompt)
            result_text = response.text
            
            status_box.success("✅ 生成完成！")
            st.text_area("生成結果", value=result_text, height=600, label_visibility="collapsed")
            
        except Exception as e:
            status_box.error(f"生成失敗: {str(e)}")
            st.error("請確認 API Key 是否正確。")
    else:
        # 空白狀態
        st.markdown("""
        <div style="color:#9ca3af; text-align:center; padding-top:100px;">
            <p>等待 PDF 解析與生成...</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)
