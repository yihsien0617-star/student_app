import streamlit as st
import json
import os

# --- 1. 讀取 JSON 題庫資料 ---
@st.cache_data
def load_exam_data(file_path):
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

# 請將這裡的檔名替換成您實際轉檔出來的 JSON 檔名
EXAM_FILE = 'immunology_exam.json' 
exam_data = load_exam_data(EXAM_FILE)

# --- 2. 初始化 Session State (紀錄測驗進度) ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'current_q_index' not in st.session_state:
    st.session_state['current_q_index'] = 0
if 'score' not in st.session_state:
    st.session_state['score'] = 0
if 'show_explanation' not in st.session_state:
    st.session_state['show_explanation'] = False
if 'selected_option' not in st.session_state:
    st.session_state['selected_option'] = None

# --- 3. 網頁介面設計 ---
st.set_page_config(page_title="中華醫大醫檢系 | 國考線上測驗", page_icon="🧬", layout="centered")

# --- 登入畫面 ---
if not st.session_state['logged_in']:
    st.title("🧬 臨床血清免疫學線上題庫")
    st.info("請輸入課堂專屬密碼以進入測驗系統。")
    password = st.text_input("輸入密碼：", type="password")
    
    if st.button("登入"):
        if password == "hwai2026": # 預設密碼，您可以隨時更改
            st.session_state['logged_in'] = True
            st.rerun()
        else:
            st.error("密碼錯誤，請重新確認！")

# --- 測驗畫面 ---
else:
    if not exam_data:
        st.error("找不到題庫資料，請確認 JSON 檔案是否存在。")
    else:
        # 側邊欄：顯示進度與選單
        with st.sidebar:
            st.header("📊 學習儀表板")
            st.progress((st.session_state['current_q_index']) / len(exam_data))
            st.write(f"進度：第 **{st.session_state['current_q_index'] + 1}** 題 / 共 {len(exam_data)} 題")
            st.write(f"目前答對：**{st.session_state['score']}** 題")
            
            st.divider()
            if st.button("🚪 登出系統"):
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.rerun()

        # 主畫面：顯示題目
        current_q = exam_data[st.session_state['current_q_index']]
        
        st.subheader(f"📝 第 {current_q.get('question_number', st.session_state['current_q_index'] + 1)} 題")
        st.markdown(f"### {current_q['question_text']}")
        
        # 整理選項
        options_list = []
        option_keys = []
        for key, text in current_q['options'].items():
            options_list.append(f"({key}) {text}")
            option_keys.append(key)
            
        # 讓學生選擇答案
        selected = st.radio("請選擇您的答案：", options_list, index=None, key=f"radio_{st.session_state['current_q_index']}")
        
        # 提交按鈕與回饋邏輯
        if not st.session_state['show_explanation']:
            if st.button("✅ 送出答案"):
                if selected:
                    # 擷取學生選的字母 (A, B, C, D)
                    student_ans = selected[1] 
                    st.session_state['selected_option'] = student_ans
                    st.session_state['show_explanation'] = True
                    
                    if student_ans == current_q['answer']:
                        st.session_state['score'] += 1
                        st.toast("🎉 答對了！基礎觀念很扎實！")
                    else:
                        st.toast("❌ 答錯了，請看下方老師解析釐清觀念！")
                    st.rerun()
                else:
                    st.warning("請先選擇一個答案！")
        
        # 顯示解析與下一題按鈕
        else:
            student_ans = st.session_state['selected_option']
            correct_ans = current_q['answer']
            
            if student_ans == correct_ans:
                st.success(f"**您的答案：{student_ans} | 正確答案：{correct_ans} ➔ 答對！**")
            else:
                st.error(f"**您的答案：{student_ans} | 正確答案：{correct_ans} ➔ 答錯！**")
            
            # 展開老師撰寫的精華解析
            with st.expander("💡 點開看老師獨家解析", expanded=True):
                if current_q.get('explanation'):
                    st.info(current_q['explanation'])
                else:
                    st.write("本題暫無詳細解析。")
                    
                # 顯示難度等標籤
                if current_q.get('tags'):
                    st.write("---")
                    cols = st.columns(len(current_q['tags']))
                    for idx, (k, v) in enumerate(current_q['tags'].items()):
                        cols[idx].metric(label=k, value=v)
            
            # 換題邏輯
            if st.session_state['current_q_index'] < len(exam_data) - 1:
                if st.button("➡️ 下一題", type="primary"):
                    st.session_state['current_q_index'] += 1
                    st.session_state['show_explanation'] = False
                    st.session_state['selected_option'] = None
                    st.rerun()
            else:
                st.balloons()
                st.success(f"🏆 恭喜您完成本測驗！總共答對 {st.session_state['score']} 題。")
                if st.button("🔄 重新測驗"):
                    st.session_state['current_q_index'] = 0
                    st.session_state['score'] = 0
                    st.session_state['show_explanation'] = False
                    st.session_state['selected_option'] = None
                    st.rerun()
