// --- 0. DOM 요소 캐싱 ---
const chatBody = document.getElementById('chat-body');
const chatInput = document.getElementById('chat-input');
const sendButton = document.getElementById('send-button');
const darkModeButton = document.getElementById('toggle-dark-mode');
const closeButton = document.getElementById('close-chatbot');
const resetButton = document.getElementById('reset-chat-button');
const chatBottomSpacer = document.getElementById('chat-bottom-spacer'); // ⭐️ 신규 추가

// ⭐️ 1. "이전 대화" 관련 요소 (신규)
const prevChatButton = document.querySelector('.prev-chat-button'); // ⭐️ 헤더의 '이전 대화' 버튼
const historyModal = document.getElementById('history-modal');
const modalCloseBtn = document.querySelector('.modal-close');
const historyList = document.getElementById('history-list');

// ⭐️ 2. API URL 및 인증 토큰 (기존 코드)
const API_URL = '/api/chat'; // API 엔드포인트

// ★★★ [로컬 테스트용] Cognito 토큰 ★★★
// 로컬 테스트 시, AWS Cognito 콘솔에서 발급받은 '유효한' JWT 토큰을 여기에 붙여넣으세요.
// Fargate 배포 시에는 실제 로그인 로직으로 대체되어야 합니다.
// ⭐️ (수정) &access_token=... 뒷부분을 모두 삭제
const TEMP_AUTH_TOKEN = "eyJraWQiOiJCRzdheVg2d016YXRDbFlsdFN2K3BUTVFWUDFBVWlmdjFnRjd2UlFMTlE4PSIsImFsZyI6IlJTMjU2In0.eyJhdF9oYXNoIjoiR0tiMHVTdDZkd25zRVNDTkt5VWFWUSIsInN1YiI6ImI0ZjgyZDhjLTEwMDEtNzAwMS05Yjk4LWI0MmVlMTIwNTNiYyIsImVtYWlsX3ZlcmlmaWVkIjp0cnVlLCJpc3MiOiJodHRwczpcL1wvY29nbml0by1pZHAuYXAtbm9ydGhlYXN0LTIuYW1hem9uYXdzLmNvbVwvYXAtbm9ydGhlYXN0LTJfMkJna1dFaFhFIiwiY29nbml0bzp1c2VybmFtZSI6Im1qa3dvbiIsImF1ZCI6IjVlbTc0YWhxYml1c3NjdWFiZ2c3ajFkdWdiIiwiZXZlbnRfaWQiOiI1ZDYyNGE2Yy1hNDU3LTRlNmItOWIwNi1kMGI1YmY5NmFlMjYiLCJ0b2tlbl91c2UiOiJpZCIsImF1dGhfdGltZSI6MTc2MjMyNTQxMywibmFtZSI6Im1pbmplb25nIGt3b24iLCJleHAiOjE3NjIzMjkwMTMsImlhdCI6MTc2MjMyNTQxMywianRpIjoiMjU4ODk3MzMtM2UwMS00MWRhLTg2NTEtOWU2NmRkY2Q0NDQ4IiwiZW1haWwiOiJtamt3b24wMjI2QGdtYWlsLmNvbSJ9.v4OSPlNODMixleFkRuy6fu7puXvhCQZbwM3ZX5h1ywyBSPScbtxpsaJyrwy9FQHM34ghKgweBeU3jtkWI-diBPlBz78Fc7nQ5HDnq5jPKorqhpRa0TNEq11zjNlbT3HGZlwUoutC7rwAHoG-uFvzEksCd3gdpchztmDKjfb6k3Jp-uACdn3kpBQABX3arcZ2qAX-Q9i9ck9Rc5_xIxICdcYyOFAOFTQi3lM6xlUA7Z7n5_gL1MIFo7P1cNT5igA9-58NTbRaRU8VGLu4daXfzGFdCdafqUVCY2l3HIPKB6iBsRd5ZPCbK-suKZdUyt0Wh_soWM3Xu_ZOjLH3sIKLiQ";

// ⭐️ "답변 중지" 기능용 전역 변수 (신규)
let abortController = null;
// ⭐️ 전송/중지 SVG 아이콘 (신규)
const ICON_SEND = `<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 10 4 15 9 20"></polyline><path d="M20 4v7a4 4 0 0 1-4 4H4"></path></svg>`; //
const ICON_STOP = `<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect></svg>`; // (정지 아이콘)

function stopGeneration() {
    if (abortController) {
        abortController.abort("User stopped generation."); // ⭐️ fetch 중단
    }
}

// ⭐️ 3. 세션 ID 관리를 위한 전역 변수
let currentSessionId = null;
let currentBotMessageElement = null; // 현재 봇 응답을 저장할 임시 변수

function initializeAuth() {
    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
        // --- 로컬 테스트 환경 ---
        console.log("Running in local mode. Using LOCAL_TEST_TOKEN.");
        authToken = LOCAL_TEST_TOKEN;
    } else {
        // --- Fargate (프로덕션) 환경 ---
        console.log("Running in Fargate/Prod mode. Requesting token from parent window.");
        
        // 1. 부모 창으로부터 토큰 수신 대기
        window.addEventListener('message', (event) => {
            // ⭐️ 보안: (필수) 'https://your-main-portal.com'을 실제 부모 창의 도메인으로 변경하세요.
            // if (event.origin !== 'https://your-main-portal.com') { 
            //    console.warn('Message received from untrusted origin:', event.origin);
            //    return;
            // }

            if (event.data && event.data.type === 'cognito-id-token') {
                if (event.data.token) {
                    console.log("Received token from parent window.");
                    authToken = event.data.token;
                } else {
                    console.error("Token message received from parent, but token is empty.");
                }
            }
        });

        // 2. 부모 창에 챗봇이 준비되었음을 알림 (토큰 요청)
        window.parent.postMessage('chatbot-ready-for-token', '*'); 
    }
}

// --- 1. 이벤트 리스너 ---
document.addEventListener('DOMContentLoaded', () => {
    initializeChat(); // 기존 함수
    initializeAuth(); // ⭐️ (신규) 인증 초기화 함수 호출
});

sendButton.addEventListener('click', sendMessage);

chatInput.addEventListener('keydown', (e) => {
    // ⭐️ event.isComposing이 false일 때만(한글 조합이 끝났을 때만) Enter가 작동하도록 수정
    if (e.key === 'Enter' && !e.shiftKey && !e.isComposing) {
        e.preventDefault(); // 줄바꿈 방지
        sendMessage();
    }
});
darkModeButton.addEventListener('click', () => {
    document.body.classList.toggle('dark-mode');
});
closeButton.addEventListener('click', () => {
    window.parent.postMessage('close-chatbot', '*');
});
// ⭐️ 6. 홈 버튼 (resetButton) 수정
// (세션 ID를 null로 초기화)
resetButton.addEventListener('click', initializeChat);

chatBody.addEventListener('click', handleChatBodyClick); // 복사 버튼 리스너

// --- 2. 핵심 기능 ---

// [최종] 퀵 리플라이(자주하는 질문)가 포함된 초기화 함수
function initializeChat() {
    chatBody.innerHTML = ''; 
    chatBody.appendChild(chatBottomSpacer);
    // 'welcome-message' 클래스로 인사말 식별
    const welcomeMsg = createMessageElement("안녕하세요, 권민정님. 학습도우미 'SMUS 봇'이에요.", 'received welcome-message');
    chatBody.insertBefore(welcomeMsg, chatBottomSpacer);
    
    // 퀵 리플라이 버튼 HTML
    const quickReplyHTML = `
    <div class="quick-reply-wrapper">
        <button class="quick-reply">담당자 정보 알려줘</button>
        <button class="quick-reply">데이터를 활용하고 싶은데 신청 방법은?</button>
        <button class="quick-reply">VDI 설정 방법 알려줘</button>
    </div>`;
    chatBottomSpacer.insertAdjacentHTML('beforebegin', quickReplyHTML);
    
    // 퀵 리플라이 버튼에 이벤트 리스너 연결
    document.querySelectorAll('.quick-reply').forEach(button => {
        button.addEventListener('click', handleQuickReplyClick);
    });
    
    // chatBody.appendChild(resetButton); // 홈 버튼 다시 추가
    resetButton.style.display = 'none'; // 첫 화면에서는 숨김
}

// [최종] 퀵 리플라이 클릭 처리
function handleQuickReplyClick(e) {
    const question = e.target.textContent;
    chatInput.value = question;
    sendMessage();
}

// [최종] 복사 버튼 클릭 처리 (http:// 환경용 execCommand)
function handleChatBodyClick(e) {
    const copyButton = e.target.closest('.copy-button');
    if (!copyButton) return;

    const messageElement = copyButton.closest('.message');
    if (!messageElement) return;

    const messageTextSpan = messageElement.querySelector('.message-text');
    if (!messageTextSpan) return;

    const messageText = messageTextSpan.textContent;
    
    // execCommand 로직
    const textarea = document.createElement('textarea');
    textarea.value = messageText;
    textarea.style.position = 'absolute';
    textarea.style.left = '-9999px';
    document.body.appendChild(textarea);
    textarea.select();
    let success = false;
    try {
        success = document.execCommand('copy');
    } catch (err) {
        console.error('Failed to copy text (execCommand): ', err);
    }
    document.body.removeChild(textarea);

    if (success) {
        const originalIcon = copyButton.innerHTML;
        copyButton.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>';
        copyButton.classList.add('copied'); 
        setTimeout(() => {
            copyButton.innerHTML = originalIcon;
            copyButton.classList.remove('copied');
        }, 1500);
    }
}

// [최종] 스트리밍 sendMessage 함수
// ⭐️ 이 함수 전체를 덮어쓰세요 (약 258라인 ~ 423라인) ⭐️
async function sendMessage() {
    const messageText = chatInput.value.trim();
    if (messageText === "" || abortController) return; // ⭐️ 중복/빈 메시지 전송 방지
    
    // 1. 사용자 메시지 추가 (인사말/퀵 리플라이 제거)
    addMessageToUI(messageText, 'sent');
    chatInput.value = "";

    // 2. 입력창/전송 버튼 비활성화
    chatInput.disabled = true;
    sendButton.disabled = true;
    
    // 3. ⭐️ 로딩 버블 *하나만* 생성
    currentBotMessageElement = createMessageElement("답변 생성하는 중입니다...", 'received loading-bubble');
    chatBody.insertBefore(currentBotMessageElement, chatBottomSpacer); 
    
    // 4. 타이핑 인디케이터 추가
    addTypingIndicator(currentBotMessageElement);
    
    // 5. "중지" 버튼 생성 및 추가
    const stopButton = document.createElement('button');
    stopButton.className = 'stop-generation-button';
    stopButton.title = "중지";
    stopButton.innerHTML = ICON_STOP; 
    stopButton.addEventListener('click', stopGeneration);
    currentBotMessageElement.querySelector('.message-content-wrapper').appendChild(stopButton);

    try {
        // 6. AbortController 생성
        abortController = new AbortController();

        const response = await fetch(API_URL, {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + authToken // ⭐️ TEMP_AUTH_TOKEN -> authToken
            },
            body: JSON.stringify({ 
                message: messageText,
                sessionId: currentSessionId
            }),
            signal: abortController.signal 
        });

        if (!response.ok) {
            // HTTP 오류 발생 시
            const errorData = await response.json();
            throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
        }
        
        const reader = response.body.getReader();
        const decoder = new TextDecoder('utf-8');
        let streamingText = ""; 
        let isFirstChunk = true; // 첫 청크(sessionId 또는 텍스트)인지 확인

        // 7. 스트리밍 루프 시작
        while (true) {
            const { done, value } = await reader.read();
            if (done) {
                // 스트림 정상 종료 시
                finalizeMessage(currentBotMessageElement); // 복사 버튼 추가
                break;
            }
            
            let chunkText = decoder.decode(value, { stream: true });

            if (isFirstChunk) {
                try {
                    // 8. sessionId 파싱 시도
                    const data = JSON.parse(chunkText.trim());
                    if (data.sessionId) {
                        currentSessionId = data.sessionId; // 세션 ID 저장
                        isFirstChunk = false; // JSON 청크 처리 완료
                        continue; // 이 청크는 화면에 그리지 않고 건너뛰기
                    }
                } catch (e) {
                    // JSON 파싱 실패
                    if (chunkText.includes('{"sessionId":')) {
                         console.log("Waiting for more JSON chunk...");
                         continue; // 쪼개진 JSON이므로 다음 청크 기다림
                    }
                }

                // 9. ⭐️ 첫 *실제 텍스트* 청크 도착 시 로딩 UI 정리
                currentBotMessageElement.classList.remove('loading-bubble'); // 세로 정렬 CSS 제거
                
                let textSpan = currentBotMessageElement.querySelector('.message-text');
                if (textSpan) {
                    textSpan.textContent = ""; // "답변 생성중입니다..." 텍스트 제거
                }
                isFirstChunk = false; // 첫 텍스트 청크 처리 완료
            }
            
            // 10. 텍스트 화면에 누적
            streamingText += chunkText;
            
            let textSpan = currentBotMessageElement.querySelector('.message-text');
            if (!textSpan) { 
                const contentWrapper = currentBotMessageElement.querySelector('.message-content-wrapper');
                textSpan = document.createElement('span');
                textSpan.classList.add('message-text');
                contentWrapper.appendChild(textSpan);
            }
            textSpan.textContent = streamingText; // 텍스트 실시간 업데이트
            
            scrollToBottom();
        }

    } catch (error) {
        // 11. 오류 처리 (중지 또는 기타 에러)
        if (error.name === 'AbortError') {
            console.log("Stream stopped by user.");
            if (currentBotMessageElement) {
                currentBotMessageElement.classList.remove('loading-bubble');
                removeTypingIndicator(currentBotMessageElement);
                let textSpan = currentBotMessageElement.querySelector('.message-text');
                if (textSpan) {
                    textSpan.textContent = "사용자가 질문을 중지했습니다.";
                }
                currentBotMessageElement.classList.add('error');
            }
        } else {
            console.error('Error fetching stream response:', error);
            if (currentBotMessageElement) {
                currentBotMessageElement.classList.remove('loading-bubble');
                removeTypingIndicator(currentBotMessageElement);
                let textSpan = currentBotMessageElement.querySelector('.message-text');
                if(textSpan && (textSpan.textContent === '답변 생성하는 중입니다...' || textSpan.textContent === '')) {
                    textSpan.textContent = `죄송합니다. 오류가 발생했습니다: ${error.message}`;
                }
                currentBotMessageElement.classList.add('error');
            }
        }
    } finally {
        // 12. ⭐️ (중요) 항상 실행되는 마무리 작업
        chatInput.disabled = false; // 입력창 활성화
        sendButton.disabled = false; // 전송 버튼 활성화

        // ⭐️ 5. (수정) 버블 내 로딩 요소들 (중지 버튼, 점점점)을 모두 제거
        if (currentBotMessageElement) {
            const stopBtn = currentBotMessageElement.querySelector('.stop-generation-button');
            if (stopBtn) stopBtn.remove();
            
            // ⭐️ (신규) "점점점" 인디케이터도 여기서 확실히 제거합니다.
            removeTypingIndicator(currentBotMessageElement); 
        }

        // ⭐️ 6. (수정) 기존 'sendButton' 원상복구 로직 삭제
        abortController = null; 

        currentBotMessageElement = null; 
        resetButton.style.display = 'flex';
        scrollToBottom();
        chatInput.focus();
    }
}

// --- 3. UI 헬퍼 함수 ---

// [최종] 메시지 생성 (복사 버튼 로직 분리)
function createMessageElement(text, type) {
    const messageElement = document.createElement('div');
    messageElement.classList.add('message', ...type.split(' ')); 

    if (type.startsWith('received')) {
        const contentWrapper = document.createElement('div');
        contentWrapper.classList.add('message-content-wrapper');

        if (text) { // 인사말 등 초기 텍스트
            const textSpan = document.createElement('span');
            textSpan.classList.add('message-text');
            textSpan.textContent = text;
            contentWrapper.appendChild(textSpan);
        }
        messageElement.appendChild(contentWrapper);

    } else { // 'sent'
        messageElement.textContent = text;
    }
    return messageElement;
}

// [최종] 스트림 종료 시 복사 버튼 추가 (인사말 제외)
function finalizeMessage(messageElement) {
    if (!messageElement || messageElement.classList.contains('welcome-message')) {
        return;
    }
    
    const contentWrapper = messageElement.querySelector('.message-content-wrapper');
    if (contentWrapper && !contentWrapper.querySelector('.copy-button')) {
        const copyButton = document.createElement('button');
        copyButton.classList.add('copy-button');
        copyButton.title = "답변 복사"; // 툴팁
        copyButton.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></path><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>`;
        contentWrapper.appendChild(copyButton);
    }
}

// [최종] 메시지 UI 추가
function addMessageToUI(text, type) {
    const messageElement = createMessageElement(text, type);
    const quickReplies = chatBody.querySelector('.quick-reply-wrapper');
    if(quickReplies) quickReplies.remove(); // 퀵 리플라이 제거

    // ⭐️ 이 2줄을 여기에 추가하세요 ⭐️
    const welcomeMsg = chatBody.querySelector('.welcome-message');
    if(welcomeMsg) welcomeMsg.remove(); // 인사말(welcome-message) 제거

    chatBody.insertBefore(messageElement, chatBottomSpacer); // ⭐️ (수정)
    resetButton.style.display = 'flex'; // 홈 버튼 표시
    scrollToBottom();
}

// [최종] 타이핑 인디케이터 (메시지 버블 안에 추가)
function addTypingIndicator(targetElement) {
    const contentWrapper = targetElement.querySelector('.message-content-wrapper');
    if (!contentWrapper) return;
    
    const typingIndicator = document.createElement('div');
    typingIndicator.classList.add('typing-indicator'); 
    typingIndicator.innerHTML = '<span></span><span></span><span></span>';
    contentWrapper.appendChild(typingIndicator);
    scrollToBottom();
}

// [최종] 타이핑 인디케이터 제거
function removeTypingIndicator(targetElement) {
    const indicator = targetElement.querySelector('.typing-indicator');
    if (indicator) indicator.remove();
}

// [최종] 스크롤 하단 이동
function scrollToBottom() {
    chatBody.scrollTop = chatBody.scrollHeight;
}

/**
 * ISO 8601 문자열(UTC)을 'YYYY-MM-DD HH:MM:SS' (로컬 시간)으로 변환합니다.
 */
function formatTimestamp(isoString) {
    const date = new Date(isoString); // 'Z'가 붙어있어 UTC로 인식되고, 로컬 시간대로 자동 변환됩니다.
    
    const yyyy = date.getFullYear();
    const mm = String(date.getMonth() + 1).padStart(2, '0'); // 월은 0부터 시작
    const dd = String(date.getDate()).padStart(2, '0');
    
    const hh = String(date.getHours()).padStart(2, '0');
    const min = String(date.getMinutes()).padStart(2, '0');
    const ss = String(date.getSeconds()).padStart(2, '0');
    
    // 사용자가 요청한 '시:분:초' 형식
    return `${yyyy}-${mm}-${dd} ${hh}:${min}:${ss}`;
}

// ⭐️ 7. "이전 대화" 버튼 클릭 시
prevChatButton.addEventListener('click', async () => {
    try {
        // 백엔드에서 세션 목록 가져오기 (⭐️ API_SESSIONS_URL은 실제 경로로 변경)
        const response = await fetch('/api/sessions', {
            headers: { 'Authorization': 'Bearer ' + authToken } // ⭐️ TEMP_AUTH_TOKEN -> authToken
        });
        if (!response.ok) throw new Error('대화 목록 로드 실패');
        
        const sessions = await response.json();
        
        historyList.innerHTML = ''; // 기존 목록 비우기
        if (sessions.length === 0) {
            historyList.innerHTML = '<li>이전 대화가 없습니다.</li>';
        } else {
            sessions.forEach(session => {
                const li = document.createElement('li');
            
                // ⭐️ 1. 제목과 시간을 가져옵니다.
                const title = session.session_title || "제목 없음";
                // ⭐️ 2. 방금 추가한 헬퍼 함수로 시간 포맷팅
                const time = formatTimestamp(session.session_id); 
                
                // ⭐️ 3. 텍스트 대신 HTML을 사용하여 두 줄로 표시
                li.innerHTML = `
                    <span class="history-title">${title}</span>
                    <span class="history-time">${time}</span>
                `;
                
                li.dataset.sessionId = session.session_id; // 세션 ID 저장
                historyList.appendChild(li);
            });
        }
        
        historyModal.style.display = 'block'; // 모달 보이기
        
    } catch (error) {
        console.error('Error loading history:', error);
        alert('이전 대화를 불러오는 데 실패했습니다.');
    }
});

// ⭐️ 8. 모달의 목록 아이템 클릭 시
historyList.addEventListener('click', (event) => {
    // ⭐️ 1. 클릭된 지점에서 가장 가까운 'li' 태그를 찾습니다.
    const clickedLi = event.target.closest('li');
    
    // ⭐️ 2. 'li'를 찾았고, 'sessionId' 데이터가 있는지 확인합니다.
    if (clickedLi && clickedLi.dataset.sessionId) {
        const sessionId = clickedLi.dataset.sessionId;
        loadChatHistory(sessionId); // 해당 대화 불러오기
    }
});

// ⭐️ 9. 모달 닫기 버튼
modalCloseBtn.addEventListener('click', () => {
    historyModal.style.display = 'none';
});

// ⭐️ 10. 모달 바깥쪽 클릭 시 닫기
window.addEventListener('click', (event) => {
    if (event.target == historyModal) {
        historyModal.style.display = 'none';
    }
});

// ⭐️ 11. 특정 대화 내역 불러오기 함수 (신규)
async function loadChatHistory(sessionId) {
    if (!sessionId) return;

    // ⭐️ (디버깅) F12(개발자 도구) 콘솔에 이 로그가 찍히는지 확인
    console.log(`[DEBUG] loadChatHistory 호출됨! Session ID: ${sessionId}`);

    // ⭐️ 1. 로더(프로그레스바) 보이기
    const loader = document.getElementById('loader-overlay');
    loader.style.display = 'flex';
    
    try {
        // 백엔드에서 메시지 목록 가져오기 (⭐️ API_MESSAGES_URL은 실제 경로로 변경)
        const response = await fetch(`/api/messages/${sessionId}`, {
            headers: { 'Authorization': 'Bearer ' + authToken } // ⭐️ TEMP_AUTH_TOKEN -> authToken
        });
        if (!response.ok) throw new Error('대화 내역 로드 실패');
        
        const messages = await response.json(); // [{role: 'user', content: '...'}, ...]
        
        chatBody.innerHTML = ''; // 현재 챗봇창 비우기
        chatBody.appendChild(chatBottomSpacer);
        
        messages.forEach(msg => {
            const senderType = (msg.role === 'user') ? 'sent' : 'received';
            const messageElement = createMessageElement(msg.content, senderType);
            chatBody.insertBefore(messageElement, chatBottomSpacer);
        });
        
        currentSessionId = sessionId; // ⭐️ 현재 세션을 이 ID로 설정
        historyModal.style.display = 'none'; // 모달 닫기
        resetButton.style.display = 'flex'; // 홈 버튼 표시
        scrollToBottom();
        
    } catch (error) {
        console.error('Error loading chat messages:', error);
        alert('대화 내역을 불러오는 데 실패했습니다.');
    } finally {
        // ⭐️ 2. 로딩이 성공하든 실패하든, 로더 숨기기
        loader.style.display = 'none';
    }
}