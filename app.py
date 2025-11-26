import streamlit as st
import google.generativeai as genai
from pypdf import PdfReader
import datetime
from io import BytesIO

# --- 1. 頁面設定 ---
st.set_page_config(
    page_title="元大日股外電報告產生器",
    page_icon="🇯🇵",
    layout="wide"
)

# 自訂 CSS 讓介面更美觀
st.markdown("""
    <style>
    .main {
        background-color: #f8f9fa;
    }
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        height: 3em;
    }
    .stTextArea textarea {
        background-color: #ffffff;
        color: #31333F;
    }
    div[data-testid="stDateInput"], div[data-testid="stSelectbox"] {
        background-color: white;
        padding: 10px;
        border-radius: 8px;
        border: 1px solid #ddd;
        margin-bottom: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 標題區 ---
st.title("🇯🇵 日股外電報告產生器 (元大證券)")
st.caption("V5.3 Python Streamlit 版本 | 自動偵測可用模型 | 支援多檔上傳")

# --- 3. 處理 API Key 與 模型清單自動抓取 ---
api_key = None
has_valid_key = False
available_models = []

# 1. 嘗試取得 Key
if "GOOGLE_API_KEY" in st.secrets:
    api_key = st.secrets["GOOGLE_API_KEY"]
else:
    api_key = st.text_input("輸入 Google Gemini API Key", type="password")

# 2. 如果有 Key，嘗試連線並抓取模型清單
if api_key:
    try:
        genai.configure(api_key=api_key)
        # 測試列出模型 (這同時也能驗證 Key 是否有效)
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                available_models.append(m.name)
        
        # 簡單排序，讓 gemini-1.5 等較新的模型排前面
        available_models.sort(reverse=True)
        has_valid_key = True
        
    except Exception as e:
        st.error(f"⚠️ API Key 驗證失敗或連線錯誤: {e}")
        st.caption("請檢查您的 API Key 是否正確，或是否已在 Google Cloud Console 啟用 Generative Language API。")
        # 預設後備清單，避免介面壞掉
        available_models = ["models/gemini-1.5-flash", "models/gemini-1.5-pro"]
else:
    # 沒有 Key 時的預設顯示
    available_models = ["請先輸入 API Key"]

# --- 4. 介面佈局 ---
col_left, col_right = st.columns([0.4, 0.6], gap="large")

with col_left:
    # --- 上傳檔案 ---
    st.info("1️⃣ 上傳券商 PDF 報告")
    uploaded_files = st.file_uploader(
        "支援拖曳多個檔案", 
        type=["pdf"], 
        accept_multiple_files=True
    )

    st.write("---")

    # --- 設定 ---
    st.info("2️⃣ 設定報告參數")
    
    report_date = st.date_input(
        "📅 選擇報告日期",
        datetime.date.today()
    )
    
    # 動態模型選擇
    selected_model_name = st.selectbox(
        "🤖 選擇 AI 模型 (自動偵測)",
        available_models,
        index=0,
        help="此清單由系統根據您的 API Key 自動向 Google 查詢可用的模型。"
    )
    
    if uploaded_files:
        st.success(f"已上傳 {len(uploaded_files)} 份檔案")
    else:
        st.warning("請先上傳檔案")

    st.write("---")

    # --- 按鈕 ---
    # 只有當有檔案且 API Key 驗證成功時才啟用按鈕
    generate_btn = st.button("✨ AI 直接生成報告", type="primary", disabled=not (uploaded_files and has_valid_key))
    show_prompt = st.checkbox("顯示完整指令 (若需手動複製)")

# --- 5. 核心邏輯 ---
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

# --- 6. 輸出區 ---
with col_right:
    st.write("### 📝 輸出結果")
    
    if show_prompt and final_prompt:
        st.info("下方是完整指令：")
        st.code(final_prompt, language="text")

    if generate_btn:
        status_box = st.empty()
        status_box.info(f"🤖 正在使用 {selected_model_name} 模型生成中...")
        
        try:
            # genai 已經在上方 configure 過了，這裡直接使用
            model = genai.GenerativeModel(selected_model_name)
            response = model.generate_content(final_prompt)
            result_text = response.text
            
            status_box.success("✅ 生成完成！")
            st.text_area("生成結果", value=result_text, height=600)
            
        except Exception as e:
            status_box.error(f"生成失敗: {str(e)}")
            st.error("請確認 API Key 權限或網路狀態。")

    elif not generate_btn and not show_prompt:
        st.info("👈 請在左側上傳檔案並按下生成按鈕")
