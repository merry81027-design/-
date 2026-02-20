import streamlit as st
import pandas as pd

# ==========================================
# 1. 網頁基本設定
# ==========================================
st.set_page_config(page_title="高中生落點分析系統", page_icon="🎓", layout="centered")
st.title("🎓 112-114年 大學落點分析系統")
st.markdown("💡 **搜尋技巧**：支援複合關鍵字，例如輸入 `台大 資工` 或 `師大 心輔`。資料與雲端試算表即時同步！")
st.divider()

# ==========================================
# 2. 連結 Google 試算表 (即時讀取)
# ==========================================
# 🔴 老師請注意：請把下面的引號內容，換成您剛剛複製的「資料庫 ID」！
SHEET_ID = "1VVm5MkdMzYF80dngcnHiBIWz7D1Sh0BnQeRvlKlA9DA" 
URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

# 設定快取時間為 10 秒 (ttl=10)。代表您在 Excel 改完資料，網頁最多 10 秒後就會更新！
@st.cache_data(ttl=10)
def load_data(url):
    # 直接讀取 Google 試算表匯出的 CSV 格式
    df = pd.read_csv(url, dtype={'學年度': str, '系校代碼': str})
    df = df.dropna(subset=['系校代碼'])
    return df

try:
    with st.spinner("🔄 正在與雲端資料庫同步中..."):
        df = load_data(URL)
except Exception as e:
    st.error("❌ 無法讀取資料庫，請確認 Google 試算表權限是否已設定為「知道連結的任何人皆可檢視」。")
    st.stop()

# ==========================================
# 3. 網頁搜尋介面
# ==========================================
# 建立一個輸入框
user_input = st.text_input("🔍 請輸入學校或科系關鍵字：", placeholder="例如：政大 心理")

if user_input:
    # --- 搜尋邏輯 ---
    normalized_input = user_input.replace('台', '臺')
    keywords = normalized_input.split()
    
    df['full_text'] = df['學校名稱'].astype(str) + " " + df['校系名稱'].astype(str)
    
    mask = pd.Series([True] * len(df))
    for k in keywords:
        mask = mask & df['full_text'].str.contains(k, na=False)
        
    candidates = df[mask]
    
    # 備用搜尋 (處理簡體台)
    if candidates.empty:
        raw_keywords = user_input.split()
        mask_retry = pd.Series([True] * len(df))
        for k in raw_keywords:
            mask_retry = mask_retry & df['full_text'].str.contains(k, na=False)
        candidates = df[mask_retry]

    # --- 顯示結果 ---
    if candidates.empty:
        st.warning(f"⚠️ 找不到包含「{user_input}」的科系，請嘗試更換或縮短關鍵字。")
    else:
        target_codes = candidates['系校代碼'].unique()
        st.success(f"🎯 找到 {len(target_codes)} 個相關科系！")
        
        for code in target_codes:
            history_data = df[df['系校代碼'] == code]
            history_data = history_data.sort_values(by='學年度', ascending=False)
            
            school_name = history_data.iloc[0]['學校名稱']
            dept_names = history_data['校系名稱'].unique()
            dept_name_display = " / ".join(dept_names)
            
            # 使用網頁的排版元件
            st.subheader(f"🏫 【{school_name}】")
            st.caption(f"📌 系名紀錄：{dept_name_display} (代碼：{code})")
            
            cols = ['學年度', '校系名稱', '招生名額', '篩選一', '篩選二', '篩選三', '篩選四', '篩選五']
            show_cols = [c for c in cols if c in history_data.columns]
            
            # 在網頁上畫出漂亮的表格，hide_index=True 可以隱藏最前面的流水號
            st.dataframe(history_data[show_cols], hide_index=True, use_container_width=True)
            st.divider()
