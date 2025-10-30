import streamlit as st
import time
from pathlib import Path

# --- 1. 이미지 경로 설정 ---
LOGO_IMAGE_PATH = "images/icon.png"

# --- 2. 페이지 설정 ---
st.set_page_config(layout="centered")

# --- 3. 질문 제안 목록 ---
SUGGESTIONS = ["강의 계획서 찾아줘", "휴학 신청은 어떻게 해?", "성적 조회 알려줘"]

# --- 4. CSS 주입 ---
# (퀵 리플라이 관련 CSS 제거, 나머지 동일)
POPUP_CSS = """
<style>
    .stApp {
        padding-top: 0px !important;
        padding-bottom: 0px !important;
    }
    .chatbot-welcome-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        text-align: center;
        color: white;
        padding-top: 1rem;
        padding-bottom: 0.5rem;
    }
    .welcome-title {
        color: white; 
        font-size: 1.5rem;  
        font-weight: 600; 
        margin-bottom: 0.25rem;
        margin-top: 0.5rem;
    }
    .welcome-subtitle {
        color: #B0B0B8; 
        font-size: 1.0rem; 
        font-weight: 400; 
        margin-top: 0;
        margin-bottom: 1rem;
    }
    div[data-testid="stChatMessage"] p {
        font-size: 0.95rem; 
    }
    div[data-testid="stChatInput"] input {
        font-size: 0.95rem; 
    }
</style>
"""
st.markdown(POPUP_CSS, unsafe_allow_html=True)


# --- 5. 챗봇 초기 메시지 및 질문 제안 함수 ---
def display_initial_message_and_suggestions():
    if "messages" not in st.session_state:
        st.session_state.messages = []

    if not st.session_state.messages: # 채팅 기록이 없을 때만 초기 UI 표시
        # 챗봇 환영 메시지 (로고, 제목 등)
        with st.container():
            st.markdown('<div class="chatbot-welcome-container">', unsafe_allow_html=True)
            if Path(LOGO_IMAGE_PATH).exists():
                st.image(LOGO_IMAGE_PATH, width=100)
            else:
                st.warning(f"로고 파일을 찾을 수 없습니다: {LOGO_IMAGE_PATH}")
                st.warning(f"현재 작업 폴더: {Path.cwd()}")
            st.markdown("<p class='welcome-title'>안녕하세요, 권민정님</p>", unsafe_allow_html=True) 
            st.markdown("<p class='welcome-subtitle'>학습도우미 'SMUS 봇'이에요</p>", unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        # 챗봇의 첫 답변 (소개)
        with st.chat_message("assistant"):
            st.markdown("무엇을 도와드릴까요? 아래 질문들을 클릭하거나 직접 입력해주세요.")

        st.session_state.messages.append({"role": "assistant", "content": "초기 메시지 표시"})

        # ★★★ (핵심 수정) st.button으로 질문 제안 ★★★
        # 3개의 컬럼을 만들어 버튼을 배치
        cols = st.columns(len(SUGGESTIONS)) 
        clicked_suggestion = None

        for i, suggestion in enumerate(SUGGESTIONS):
            with cols[i]:
                # use_container_width=True로 버튼이 컬럼에 꽉 차게
                if st.button(suggestion, key=f"suggestion_{i}", use_container_width=True):
                    clicked_suggestion = suggestion

        # 만약 버튼 중 하나가 클릭되었다면
        if clicked_suggestion:
            # 1. 클릭된 질문을 '사용자' 메시지로 세션에 추가
            st.session_state.messages.append({"role": "user", "content": clicked_suggestion})
            
            # 2. 가짜 답변 생성
            with st.spinner("답변을 생성 중입니다..."):
                time.sleep(0.5) # 0.5초 대기
                if clicked_suggestion == "강의 계획서 찾아줘":
                    response = "강의 계획서 조회 메뉴로 안내해 드릴게요. [여기]를 클릭하세요."
                elif clicked_suggestion == "휴학 신청은 어떻게 해?":
                    response = "휴학 신청은 [학사정보시스템 > 학적변동] 메뉴에서 하실 수 있습니다."
                elif clicked_suggestion == "성적 조회 알려줘":
                    response = "이번 학기 성적 조회는 7월 25일부터 가능합니다."
                else:
                    response = "..."
            
            # 3. 생성된 답변을 '봇' 메시지로 세션에 추가
            st.session_state.messages.append({"role": "assistant", "content": response})
            
            # 4. 페이지를 즉시 새로고침하여 채팅창에 반영
            st.rerun()

# --- 6. 챗봇 채팅 로직 ---
def run_chatbot_logic():
    st.markdown('<div id="chat_messages_end"></div>', unsafe_allow_html=True)

    # 세션에 저장된 모든 메시지 출력
    for message in st.session_state.messages:
        if message["content"] != "초기 메시지 표시": # UI 중복 방지
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        
    # ★★★ (수정) 키보드 입력(st.chat_input) 처리 부분 ★★★
    if prompt := st.chat_input("대화를 시작해 보세요.", key="chat-input"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        with st.chat_message("assistant"):
            with st.spinner("답변을 생성 중입니다..."):
                time.sleep(1)
                # (st.button으로 처리되지 않은 모든 질문은 여기로 옴)
                response = f"'{prompt}'에 대해 답변을 생성 중입니다. (아직 구현되지 않은 기능)"
                st.markdown(response)
            
        st.session_state.messages.append({"role": "assistant", "content": response})
        st.rerun()

    # (스크롤 JS는 동일, 퀵 리플라이 JS는 삭제됨)
    st.markdown(
        """
        <script>
            var element = document.getElementById("chat_messages_end");
            if (element) {
                element.scrollIntoView({behavior: "smooth", block: "end"});
            }
        </script>
        """, 
        unsafe_allow_html=True
    )

# --- 7. 앱 실행 ---
display_initial_message_and_suggestions()
run_chatbot_logic()