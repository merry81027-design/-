import streamlit as st
import pandas as pd

# ==========================================
# 1. 網頁基本設定
# ==========================================
st.set_page_config(page_title="個人申請最低錄取分數查詢系統", page_icon="🎓", layout="centered")
st.title("🎓 112-114 個申最低錄取分數查詢")
st.markdown("💡 **搜尋技巧**：關鍵字搜尋不到時請打校系全名，中間留空格，例如輸入 `國立臺灣大學 資訊工程學系`。資料與雲端試算表即時同步！")
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
    df = pd.read_csv(url, dtype={'學年度': str, '系校代碼': str})
    df = df.dropna(subset=['系校代碼'])
    return df

try:
    with st.spinner("🔄 正在與雲端資料庫同步中..."):
        df = load_data(URL)
except Exception as e:
    st.error("❌ 無法讀取資料庫，請確認 Google 試算表權限。")
    st.stop()

# ==========================================
# 3. 網頁搜尋介面與「校名翻譯蒟蒻」
# ==========================================
# 建立常見大學簡稱字典
alias_dict = {
    "台大": "臺灣大學",
    "臺大": "臺灣大學",
    "政大": "政治大學",
    "清大": "清華大學",
    "交大": "交通大學",
    "陽交大": "陽明交通大學",
    "成大": "成功大學",
    "師大": "師範大學", 
    "台師大": "臺灣師範大學",
    "臺師大": "臺灣師範大學",
    "彰師大": "彰化師範大學",
    "高師大": "高雄師範大學",
    "國北教": "臺北教育大學",
    "國北護": "臺北護理健康大學",
    "市北教": "臺北市立大學",
    "中教大": "臺中教育大學",
    "北大": "臺北大學",
    "海大": "海洋大學",
    "台科大": "臺灣科技大學",
    "臺科大": "臺灣科技大學",
    "北科大": "臺北科技大學",
    "暨大": "暨南國際大學",
    "東華": "東華大學",
    "高大": "高雄大學",
    "中山": "中山大學",
    "中央": "中央大學",
    "中正": "中正大學",
    "中興": "中興大學",
    "長庚": "長庚大學",
    "高醫": "高雄醫學大學",
    "中國醫": "中國醫藥大學",
    "中山醫": "中山醫學大學",
    "北醫": "臺北醫學大學"
}

user_input = st.text_input("🔍 請輸入學校或科系關鍵字：", placeholder="例如：政大 心理")

if user_input:
    # --- 步驟 A: 將使用者的簡稱翻譯成正式全名 ---
    search_query = user_input.replace('台', '臺') # 先統一將台轉成臺
    
   # 掃描字典 (加入 sorted 確保先替換名字長的，避免「高師大」被「師大」攔截)
    for short_name in sorted(alias_dict.keys(), key=len, reverse=True):
        full_name = alias_dict[short_name]
        if short_name in search_query:
            search_query = search_query.replace(short_name, full_name)
            
    # 切割關鍵字 (例如 "政治大學 心理" 變成 ["政治大學", "心理"])
    keywords = search_query.split()
    
    # --- 步驟 B: 執行搜尋 ---
    df['full_text'] = df['學校名稱'].astype(str) + " " + df['校系名稱'].astype(str)
    
    mask = pd.Series([True] * len(df))
    for k in keywords:
        mask = mask & df['full_text'].str.contains(k, na=False)
        
    candidates = df[mask]
    
    # 如果還是找不到，用原始字串再試一次保險
    if candidates.empty:
        raw_keywords = user_input.split()
        mask_retry = pd.Series([True] * len(df))
        for k in raw_keywords:
            mask_retry = mask_retry & df['full_text'].str.contains(k, na=False)
        candidates = df[mask_retry]

    # --- 步驟 C: 顯示結果 ---
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
            
            st.subheader(f"🏫 【{school_name}】")
            st.caption(f"📌 系名紀錄：{dept_name_display} (代碼：{code})")
            
            cols = ['學年度', '校系名稱', '招生名額', '篩選一', '篩選二', '篩選三', '篩選四', '篩選五']
            show_cols = [c for c in cols if c in history_data.columns]
            
            st.dataframe(history_data[show_cols], hide_index=True, use_container_width=True)
            st.divider()
