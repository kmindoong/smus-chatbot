import streamlit as st
import time
from pathlib import Path

# --- 1. 이미지 경로 설정 ---
LOGO_IMAGE_PATH = "images/icon.png"

# --- 2. 페이지 설정 ---
st.set_page_config(layout="centered")

# --- 3. (핵심) CSS 주입 ---
POPUP_CSS = """
<style>
    /* 팝업 내부의 UI (환영 메시지 등) */
    .chatbot-welcome-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        text-align: center;
        color: white;
        padding-top: 1rem;
    }

    /* ★ 수정: h1, h2 대신 새로운 클래스 사용 ★ */
    .welcome-title {
        color: white; 
        font-size: 1.5rem;  /* 제목 폰트 크기 */
        font-weight: 600; /* 제목 굵기 */
        margin-bottom: 0.25rem;
        margin-top: 0.5rem;
    }
    
    .welcome-subtitle {
        color: #B0B0B8; 
        font-size: 1.0rem; /* 부제목 폰트 크기 */
        font-weight: 400; 
        margin-top: 0;
        margin-bottom: 1rem; /* 아래쪽 여백 */
    }

    /* 채팅 메시지 폰트 크기 조절 */
    div[data-testid="stChatMessage"] p {
        font-size: 0.95rem; /* 채팅 메시지 폰트 크기 */
    }

    /* 채팅 입력창 폰트 크기 조절 */
    div[data-testid="stChatInput"] input {
        font-size: 0.95rem; /* 채팅 입력창 폰트 크기 */
    }
</style>
"""
st.markdown(POPUP_CSS, unsafe_allow_html=True)


# --- 4. 챗봇 UI 그리기 ---
with st.container():
    st.markdown('<div class="chatbot-welcome-container">', unsafe_allow_html=True)
    
    if Path(LOGO_IMAGE_PATH).exists():
        st.image(LOGO_IMAGE_PATH, width=100)
    else:
        st.warning(f"로고 파일을 찾을 수 없습니다: {LOGO_IMAGE_PATH}")
    
    # ★ 수정: h1 -> p.welcome-title ★
    st.markdown("<p class='welcome-title'>안녕하세요, 권민정님</p>", unsafe_allow_html=True) 

    # ★ 수정: h2 -> p.welcome-subtitle ★
    st.markdown("<p class='welcome-subtitle'>학습도우미 'SMUS 봇'이에요</p>", unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

# --- 5. 챗봇 채팅 로직 ---
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        
if prompt := st.chat_input("대화를 시작해 보세요."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    with st.chat_message("assistant"):
        time.sleep(0.5)
        response = f"'{prompt}'에 대해 답변을 생성 중입니다..."
        st.markdown(response)
        
    st.session_state.messages.append({"role": "assistant", "content": response})
    st.rerun()