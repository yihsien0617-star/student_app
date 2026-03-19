import streamlit as st
import json
import os

# --- 1. 讀取 JSON 題庫資料 (絕對路徑版) ---
@st.cache_data
def load_exam_data(file_name):
    # 自動取得目前這支 Python 檔案所在的資料夾路徑
    current_dir = os.path.dirname(os.path.abspath(__file__))
    full_path = os.path.join(current_dir, file_name)
    
    if os.path.exists(full_path):
        with open(full_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        st.error(f"⚠️ 找不到檔案！系統實際尋找的路徑為：\n`{full_path}`")
        return []

# 確保檔名與您產出的 JSON 完全一致
EXAM_FILE = '臨床血清免疫學解析.json' 
exam_data = load_exam_data(EXAM_FILE)

# --- 2. 初始化系統狀態 ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'current_index' not in st.session_state:
    st.session_state['current_index'] = 0
if 'user_answers' not in st.session_state:
    st.session_state['user_answers'] = {} 
if 'marked_questions' not in st.session_state:
    st.session_state['marked_questions'] = set() 

# --- 3. 網頁介面設計 ---
st.set_page_config(page_title="醫檢師國考 | 臨床血清免疫學", page_icon="🧬", layout="wide")

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

else:
    if not exam_data:
        st.stop()
        
    with st.sidebar:
        st.subheader("📊 測驗導覽")
        
        correct_count = sum(1 for idx, ans in st.session_state['user_answers'].items() if ans == exam_data[idx]['answer'])
        total_answered = len(st.session_state['user_answers'])
        
        st.progress(total_answered / len(exam_data) if len(exam_data) > 0 else 0)
        col_a, col_b = st.columns(2)
        col_a.metric("已作答", f"{total_answered} / {len(exam_data)}")
        col_b.metric("答對題數", f"{correct_count}")
        
        st.divider()
        st.write("📍 **題號快速跳轉** (🟢答對 🔴答錯 ⚪未答 🚩標記)")
        
        cols = st.columns(5)
        for i in range(len(exam_data)):
            status = "⚪"
            if i in st.session_state['user_answers']:
                if st.session_state['user_answers'][i] == exam_data[i]['answer']:
                    status = "🟢"
                else:
                    status = "🔴"
            
            flag = "🚩" if i in st.session_state['marked_questions'] else ""
            btn_label = f"{status}{i+1}{flag}"
            
            with cols[i % 5]:
                if st.button(btn_label, key=f"nav_{i}", help=f"第 {i+1} 題"):
                    st.session_state['current_index'] = i
                    st.rerun()
        
        st.divider()
        if st.button("🚪 登出系統", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

    current_idx = st.session_state['current_index']
    q = exam_data[current_idx]
    
    head_col1, head_col2 = st.columns([4, 1])
    with head_col1:
        st.subheader(f"📝 第 {q.get('question_number', current_idx + 1)} 題")
    with head_col2:
        is_marked = current_idx in st.session_state['marked_questions']
        mark_btn_text = "🚩 取消標記" if is_marked else "⛳ 標記此題"
        if st.button(mark_btn_text, use_container_width=True):
            if is_marked:
                st.session_state['marked_questions'].remove(current_idx)
            else:
                st.session_state['marked_questions'].add(current_idx)
            st.rerun()
    
    st.markdown(f"#### {q['question_text']}")
    st.write("") 
    
    # ==========================================
    # 💡 防呆機制：處理選項與題目合併的狀況
    # ==========================================
    options_list = [f"({k}) {v}" for k, v in q.get('options', {}).items()]
    option_keys = list(q.get('options', {}).keys())
    
    # 如果轉檔時選項被合併到題目裡抓不出來，直接給預設的純字母按鈕
    if not options_list:
        options_list = ["(A)", "(B)", "(C)", "(D)"]
        option_keys = ["A", "B", "C", "D"]
        
    has_answered = current_idx in st.session_state['user_answers']
    previous_answer = st.session_state['user_answers'].get(current_idx)
    
    default_idx = None
    if has_answered and previous_answer in option_keys:
        default_idx = option_keys.index(previous_answer)

    selected_option = st.radio(
        "請選擇答案：", 
        options_list, 
        index=default_idx,
        key=f"radio_q_{current_idx}",
        disabled=has_answered 
    )
    
    if not has_answered:
        if st.button("✅ 提交答案", type="primary"):
            if selected_option:
                # 擷取選項字母 (A, B, C, D)
                ans_letter = selected_option[1]
                st.session_state['user_answers'][current_idx] = ans_letter
                st.rerun() 
            else:
                st.warning("請先選擇一個選項再提交！")
    
    if has_answered:
        st.divider()
        user_ans = st.session_state['user_answers'][current_idx]
        correct_ans = q['answer']
        
        if user_ans == correct_ans:
            st.success(f"🎉 **答對了！** 您的答案：{user_ans}")
        else:
            st.error(f"❌ **答錯了！** 您的答案：{user_ans} ，正確答案應為：{correct_ans}")
        
        st.markdown("### 💡 老師解析")
        if q.get('explanation'):
            st.info(q['explanation'])
        else:
            st.write("本題暫無詳細解析。")
            
        if q.get('tags'):
            tag_cols = st.columns(len(q['tags']))
            for idx, (k, v) in enumerate(q['tags'].items()):
                tag_cols[idx].metric(label=k, value=v)

    st.divider()
    nav_col1, nav_col2, nav_col3 = st.columns([1, 2, 1])
    with nav_col1:
        if current_idx > 0:
            if st.button("⬅️ 上一題", use_container_width=True):
                st.session_state['current_index'] -= 1
                st.rerun()
    with nav_col3:
        if current_idx < len(exam_data) - 1:
            btn_type = "primary" if has_answered else "secondary"
            if st.button("下一題 ➡️", use_container_width=True, type=btn_type):
                st.session_state['current_index'] += 1
                st.rerun()
