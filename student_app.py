import streamlit as st
import json
import os
import pandas as pd

# --- 1. 讀取 JSON 題庫資料 ---
@st.cache_data
def load_exam_data(file_name):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    full_path = os.path.join(current_dir, file_name)
    if os.path.exists(full_path):
        with open(full_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        st.error(f"⚠️ 找不到題庫檔案！系統實際尋找的路徑為：\n`{full_path}`")
        return []

EXAM_FILE = '臨床血清免疫學解析.json' 
exam_data = load_exam_data(EXAM_FILE)

# --- 2. 存檔與讀檔系統 ---
PROGRESS_FILE = 'progress_db.json'

def load_user_progress(student_id):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    full_path = os.path.join(current_dir, PROGRESS_FILE)
    if os.path.exists(full_path):
        with open(full_path, 'r', encoding='utf-8') as f:
            db = json.load(f)
            if student_id in db:
                data = db[student_id]
                answers = {int(k): v for k, v in data.get('user_answers', {}).items()}
                marked = set(data.get('marked_questions', []))
                return answers, marked
    return {}, set()

def save_user_progress(student_id, answers, marked):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    full_path = os.path.join(current_dir, PROGRESS_FILE)
    db = {}
    if os.path.exists(full_path):
        with open(full_path, 'r', encoding='utf-8') as f:
            db = json.load(f)
            
    db[student_id] = {
        'user_answers': answers,
        'marked_questions': list(marked)
    }
    
    with open(full_path, 'w', encoding='utf-8') as f:
        json.dump(db, f, ensure_ascii=False, indent=4)

# --- 3. 初始化系統狀態 ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'view_pointer' not in st.session_state:
    st.session_state['view_pointer'] = 0 # 記錄目前看到篩選列表的第幾題

# --- 4. 網頁介面設計 ---
st.set_page_config(page_title="臨床血清免疫學 | 國考線上測驗", page_icon="🧬", layout="wide")

# ==========================================
# 登入畫面
# ==========================================
if not st.session_state['logged_in']:
    st.title("🧬 臨床血清免疫學國考題庫")
    st.info("系統已啟用自動存檔與分類刷題功能。")
    
    student_id = st.text_input("👤 輸入學號/姓名 (將作為存檔帳號)：")
    password = st.text_input("🔑 輸入課堂密碼：", type="password")
    
    if st.button("登入系統"):
        if not student_id:
            st.warning("請輸入學號或姓名以建立專屬存檔！")
        elif password == "hwai2026": 
            st.session_state['logged_in'] = True
            st.session_state['student_id'] = student_id
            
            answers, marked = load_user_progress(student_id)
            st.session_state['user_answers'] = answers
            st.session_state['marked_questions'] = marked
            st.session_state['view_pointer'] = 0
            st.rerun()
        else:
            st.error("密碼錯誤，請重新確認！")

# ==========================================
# 測驗主畫面
# ==========================================
else:
    if not exam_data:
        st.stop()
        
    student_id = st.session_state['student_id']
    
    # --- 動態提取所有的年份與主題 ---
    all_years = set()
    all_topics = set()
    for q in exam_data:
        tags = q.get('tags', {})
        if '年份' in tags: all_years.add(tags['年份'])
        if '主題' in tags: all_topics.add(tags['主題'])
    
    # 排序以利選單顯示
    year_options = ["全部"] + sorted(list(all_years), reverse=True)
    topic_options = ["全部"] + sorted(list(all_topics))

    with st.sidebar:
        st.title("👨‍⚕️ 國考衝刺中心")
        st.success(f"目前登入：**{student_id}**")
        menu = st.radio("📌 系統功能", ["📝 開始測驗", "📚 錯題本與收藏", "📈 學習分析儀表板"])
        
        # 只有在開始測驗時才顯示篩選器
        if menu == "📝 開始測驗":
            st.divider()
            st.subheader("🔍 自訂測驗範圍")
            selected_year = st.selectbox("選擇考古題年份：", year_options)
            selected_topic = st.selectbox("選擇課程主題：", topic_options)

        st.divider()
        if st.button("🚪 登出系統", use_container_width=True):
            save_user_progress(st.session_state['student_id'], st.session_state['user_answers'], st.session_state['marked_questions'])
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

    # ==========================================
    # 分頁 1：開始測驗 (具備動態篩選)
    # ==========================================
    if menu == "📝 開始測驗":
        
        # 根據篩選條件產生「有效題號清單」
        active_indices = []
        for i, q in enumerate(exam_data):
            tags = q.get('tags', {})
            match_year = (selected_year == "全部" or tags.get('年份') == selected_year)
            match_topic = (selected_topic == "全部" or tags.get('主題') == selected_topic)
            if match_year and match_topic:
                active_indices.append(i)
                
        if not active_indices:
            st.warning("⚠️ 在目前的篩選條件下找不到任何題目，請嘗試調整左側的年份或主題！")
            st.stop()
            
        # 安全機制：確保指標不會超出篩選後的範圍
        if st.session_state['view_pointer'] >= len(active_indices):
            st.session_state['view_pointer'] = 0

        # 取得絕對題號
        pointer = st.session_state['view_pointer']
        absolute_idx = active_indices[pointer]
        q = exam_data[absolute_idx]
        
        # 標題區塊
        head_col1, head_col2 = st.columns([4, 1])
        with head_col1:
            st.subheader(f"📝 測驗進度：第 {pointer + 1} / {len(active_indices)} 題")
            st.caption(f"(原始題庫編號：第 {absolute_idx + 1} 題)")
        with head_col2:
            is_marked = absolute_idx in st.session_state['marked_questions']
            mark_btn_text = "🚩 取消收藏" if is_marked else "⛳ 收藏此題"
            if st.button(mark_btn_text, use_container_width=True):
                if is_marked:
                    st.session_state['marked_questions'].remove(absolute_idx)
                else:
                    st.session_state['marked_questions'].add(absolute_idx)
                save_user_progress(student_id, st.session_state['user_answers'], st.session_state['marked_questions'])
                st.rerun()
        
        st.markdown(f"#### {q['question_text']}")
        st.write("") 
        
        # 選項邏輯
        options_list = [f"({k}) {v}" for k, v in q.get('options', {}).items()]
        option_keys = list(q.get('options', {}).keys())
        if not options_list:
            options_list = ["(A)", "(B)", "(C)", "(D)"]
            option_keys = ["A", "B", "C", "D"]
            
        has_answered = absolute_idx in st.session_state['user_answers']
        previous_answer = st.session_state['user_answers'].get(absolute_idx)
        
        default_idx = None
        if has_answered and previous_answer in option_keys:
            default_idx = option_keys.index(previous_answer)

        selected_option = st.radio("請選擇答案：", options_list, index=default_idx, key=f"radio_q_{absolute_idx}", disabled=has_answered)
        
        if not has_answered:
            if st.button("✅ 提交答案", type="primary"):
                if selected_option:
                    st.session_state['user_answers'][absolute_idx] = selected_option[1]
                    save_user_progress(student_id, st.session_state['user_answers'], st.session_state['marked_questions'])
                    st.rerun() 
                else:
                    st.warning("請先選擇一個選項再提交！")
        
        # 解析呈現區塊
        if has_answered:
            st.divider()
            user_ans = st.session_state['user_answers'][absolute_idx]
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

        # 換題導航
        st.divider()
        nav_col1, nav_col2, nav_col3 = st.columns([1, 2, 1])
        with nav_col1:
            if pointer > 0:
                if st.button("⬅️ 上一題", use_container_width=True):
                    st.session_state['view_pointer'] -= 1
                    st.rerun()
        with nav_col3:
            if pointer < len(active_indices) - 1:
                btn_type = "primary" if has_answered else "secondary"
                if st.button("下一題 ➡️", use_container_width=True, type=btn_type):
                    st.session_state['view_pointer'] += 1
                    st.rerun()

    # ==========================================
    # 分頁 2：錯題本與收藏 (保持不變)
    # ==========================================
    elif menu == "📚 錯題本與收藏":
        st.header("📚 專屬錯題本與收藏庫")
        st.write("考前一週衝刺必看！這裡收錄了您曾經答錯，以及手動標記收藏的重點題目。")
        
        wrong_questions = [idx for idx, ans in st.session_state['user_answers'].items() if ans != exam_data[idx]['answer']]
        bookmarked_questions = list(st.session_state['marked_questions'])
        review_list = list(set(wrong_questions + bookmarked_questions))
        review_list.sort() 
        
        if not review_list:
            st.info("太棒了！目前沒有錯題或收藏的題目。請繼續保持！")
        else:
            for idx in review_list:
                q = exam_data[idx]
                with st.expander(f"第 {idx + 1} 題 (原始題號) - 點擊展開"):
                    if idx in wrong_questions:
                        st.error("🔴 歷史錯題")
                    if idx in bookmarked_questions:
                        st.warning("🚩 我的收藏")
                        
                    st.markdown(f"**題目：** {q['question_text']}")
                    for k, v in q.get('options', {}).items():
                        st.write(f"({k}) {v}")
                    st.success(f"**正確答案：** {q['answer']}")
                    if q.get('explanation'):
                        st.info(f"**老師解析：**\n{q['explanation']}")

    # ==========================================
    # 分頁 3：學習分析儀表板 (保持不變)
    # ==========================================
    elif menu == "📈 學習分析儀表板":
        st.header("📈 學習進度與弱點分析")
        
        total_q = len(exam_data)
        answered_q = len(st.session_state['user_answers'])
        correct_q = sum(1 for idx, ans in st.session_state['user_answers'].items() if ans == exam_data[idx]['answer'])
        wrong_q = answered_q - correct_q
        
        col1, col2, col3 = st.columns(3)
        col1.metric("總完成度", f"{int((answered_q/total_q)*100)} %" if total_q > 0 else "0 %", f"{answered_q} / {total_q} 題")
        col2.metric("整體正確率", f"{int((correct_q/answered_q)*100)} %" if answered_q > 0 else "0 %", f"答對 {correct_q} 題")
        col3.metric("待強化錯題", f"{wrong_q} 題", delta_color="inverse")
        
        st.divider()
        
        if answered_q > 0:
            st.subheader("📊 答題狀況分佈")
            chart_data = pd.DataFrame(
                {"題數": [correct_q, wrong_q, total_q - answered_q]},
                index=["答對", "答錯", "未作答"]
            )
            st.bar_chart(chart_data)
        else:
            st.info("請先完成部分測驗，系統將為您產生學習數據分析。")
