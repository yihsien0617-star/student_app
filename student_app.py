import streamlit as st
import json
import os

# --- 1. 讀取 JSON 題庫資料 (絕對路徑升級版) ---
@st.cache_data
def load_exam_data(file_name):
    # 自動取得目前這支 Python 檔案所在的資料夾路徑
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # 將資料夾路徑與檔名組合，產生絕對路徑
    full_path = os.path.join(current_dir, file_name)
    
    if os.path.exists(full_path):
        with open(full_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        # 如果還是找不到，直接把「系統實際上在找的路徑」印在網頁上給您看！
        st.error(f"⚠️ 找不到檔案！系統實際尋找的路徑為：\n`{full_path}`")
        return []

# 請確保這裡的檔名與您產出的檔案完全一致 (注意大小寫)
EXAM_FILE = '臨床血清免疫學解析.json' 
exam_data = load_exam_data(EXAM_FILE)

# --- 2. 初始化系統狀態 (阿摩模式必備) ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'current_index' not in st.session_state:
    st.session_state['current_index'] = 0
if 'user_answers' not in st.session_state:
    st.session_state['user_answers'] = {} # 記錄每題學生的答案 {題號索引: 'A'}
if 'marked_questions' not in st.session_state:
    st.session_state['marked_questions'] = set() # 記錄被標記的題目索引

# --- 3. 網頁介面設計 ---
st.set_page_config(page_title="醫檢師國考 | 臨床血清免疫學", page_icon="🧬", layout="wide")

# --- 登入畫面 ---
if not st.session_state['logged_in']:
    st.title("🧬 臨床血清免疫學國考題庫系統")
    st.info("系統採用阿摩/ExamWise刷題架構，請輸入課堂專屬密碼進入。")
    password = st.text_input("輸入密碼：", type="password")
    
    if st.button("登入系統"):
        if password == "hwai2026": 
            st.session_state['logged_in'] = True
            st.rerun()
        else:
            st.error("密碼錯誤，請重新確認！")

# --- 測驗主畫面 (阿摩/ExamWise 風格) ---
else:
    if not exam_data:
        st.error("找不到題庫資料，請確認 JSON 檔案是否存在。")
    else:
        # ==========================================
        # 左側邊欄：類似阿摩的「題號導覽網格」與進度
        # ==========================================
        with st.sidebar:
            st.subheader("📊 測驗導覽")
            
            # 計算答對題數
            correct_count = sum(1 for idx, ans in st.session_state['user_answers'].items() if ans == exam_data[idx]['answer'])
            total_answered = len(st.session_state['user_answers'])
            
            # 進度條與計分板
            st.progress(total_answered / len(exam_data) if len(exam_data) > 0 else 0)
            col_a, col_b = st.columns(2)
            col_a.metric("已作答", f"{total_answered} / {len(exam_data)}")
            col_b.metric("答對題數", f"{correct_count}")
            
            st.divider()
            st.write("📍 **題號快速跳轉** (🟢答對 🔴答錯 ⚪未答 🚩標記)")
            
            # 建立題號網格 (每列 5 題)
            cols = st.columns(5)
            for i in range(len(exam_data)):
                # 決定按鈕顯示的符號
                status = "⚪"
                if i in st.session_state['user_answers']:
                    if st.session_state['user_answers'][i] == exam_data[i]['answer']:
                        status = "🟢"
                    else:
                        status = "🔴"
                
                flag = "🚩" if i in st.session_state['marked_questions'] else ""
                btn_label = f"{status}{i+1}{flag}"
                
                # 點擊題號跳轉
                with cols[i % 5]:
                    if st.button(btn_label, key=f"nav_{i}", help=f"第 {i+1} 題"):
                        st.session_state['current_index'] = i
                        st.rerun()
            
            st.divider()
            if st.button("🚪 登出系統", use_container_width=True):
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.rerun()

        # ==========================================
        # 右側主畫面：題目呈現與作答區
        # ==========================================
        current_idx = st.session_state['current_index']
        q = exam_data[current_idx]
        
        # 頂部工具列 (題號與標記功能)
        head_col1, head_col2 = st.columns([4, 1])
        with head_col1:
            st.subheader(f"📝 第 {q.get('question_number', current_idx + 1)} 題")
        with head_col2:
            # 標記功能 (類似阿摩的標籤)
            is_marked = current_idx in st.session_state['marked_questions']
            mark_btn_text = "🚩 取消標記" if is_marked else "⛳ 標記此題"
            if st.button(mark_btn_text, use_container_width=True):
                if is_marked:
                    st.session_state['marked_questions'].remove(current_idx)
                else:
                    st.session_state['marked_questions'].add(current_idx)
                st.rerun()
        
        # 題目內文
        st.markdown(f"#### {q['question_text']}")
        st.write("") # 空行增加閱讀舒適度
        
        # 整理選項
        options_list = [f"({k}) {v}" for k, v in q['options'].items()]
        option_keys = list(q['options'].keys())
        
        # 檢查這題是否已經作答過
        has_answered = current_idx in st.session_state['user_answers']
        previous_answer = st.session_state['user_answers'].get(current_idx)
        
        # 如果已作答，找出當時選的 index 以便預設選取
        default_idx = None
        if has_answered and previous_answer in option_keys:
            default_idx = option_keys.index(previous_answer)

        # 作答區 (使用 Radio 按鈕)
        selected_option = st.radio(
            "請選擇答案：", 
            options_list, 
            index=default_idx,
            key=f"radio_q_{current_idx}",
            disabled=has_answered # 阿摩模式：答過就鎖定，直接看解析
        )
        
        # 提交答案邏輯
        if not has_answered:
            if st.button("✅ 提交答案", type="primary"):
                if selected_option:
                    # 擷取選項字母 (A, B, C, D)
                    ans_letter = selected_option[1]
                    st.session_state['user_answers'][current_idx] = ans_letter
                    st.rerun() # 重新載入以顯示解析
                else:
                    st.warning("請先選擇一個選項再提交！")
        
        # ==========================================
        # 解析呈現區 (作答後才會顯示)
        # ==========================================
        if has_answered:
            st.divider()
            user_ans = st.session_state['user_answers'][current_idx]
            correct_ans = q['answer']
            
            # 對錯判定提示
            if user_ans == correct_ans:
                st.success(f"🎉 **答對了！** 您的答案：{user_ans}")
            else:
                st.error(f"❌ **答錯了！** 您的答案：{user_ans} ，正確答案應為：{correct_ans}")
            
            # 老師獨家解析區塊
            st.markdown("### 💡 老師解析")
            if q.get('explanation'):
                st.info(q['explanation'])
            else:
                st.write("本題暫無詳細解析。")
                
            # 顯示難度與再現性標籤
            if q.get('tags'):
                tag_cols = st.columns(len(q['tags']))
                for idx, (k, v) in enumerate(q['tags'].items()):
                    tag_cols[idx].metric(label=k, value=v)

        # ==========================================
        # 底部導航按鈕 (上一題 / 下一題)
        # ==========================================
        st.divider()
        nav_col1, nav_col2, nav_col3 = st.columns([1, 2, 1])
        with nav_col1:
            if current_idx > 0:
                if st.button("⬅️ 上一題", use_container_width=True):
                    st.session_state['current_index'] -= 1
                    st.rerun()
        with nav_col3:
            if current_idx < len(exam_data) - 1:
                # 如果已經作答，按鈕變明顯一點引導往下
                btn_type = "primary" if has_answered else "secondary"
                if st.button("下一題 ➡️", use_container_width=True, type=btn_type):
                    st.session_state['current_index'] += 1
                    st.rerun()
