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
const TEMP_AUTH_TOKEN = "eyJraWQiOiJCRzdheVg2d016YXRDbFlsdFN2K3BUTVFWUDFBVWlmdjFnRjd2UlFMTlE4PSIsImFsZyI6IlJTMjU2In0.eyJhdF9oYXNoIjoiamNMV1JDWVI5SDFZWlY5TllyV001QSIsInN1YiI6ImI0ZjgyZDhjLTEwMDEtNzAwMS05Yjk4LWI0MmVlMTIwNTNiYyIsImVtYWlsX3ZlcmlmaWVkIjp0cnVlLCJpc3MiOiJodHRwczpcL1wvY29nbml0by1pZHAuYXAtbm9ydGhlYXN0LTIuYW1hem9uYXdzLmNvbVwvYXAtbm9ydGhlYXN0LTJfMkJna1dFaFhFIiwiY29nbml0bzp1c2VybmFtZSI6Im1qa3dvbiIsImF1ZCI6IjVlbTc0YWhxYml1c3NjdWFiZ2c3ajFkdWdiIiwiZXZlbnRfaWQiOiJlNGMzNzUzNy0zMzk2LTQxMzgtOTJjNi02NWQ5MzIyZjQyMDEiLCJ0b2tlbl91c2UiOiJpZCIsImF1dGhfdGltZSI6MTc2MjI1NTU0OCwibmFtZSI6Im1pbmplb25nIGt3b24iLCJleHAiOjE3NjIyNTkxNDgsImlhdCI6MTc2MjI1NTU0OCwianRpIjoiNWU2MmQ2OTctOWM5My00ZjAwLTk2NDgtMDgxMzRmMzhkMDllIiwiZW1haWwiOiJtamt3b24wMjI2QGdtYWlsLmNvbSJ9.Epn3Cab_8xZI8po4pKJj7d4Y2kWbINg187kwO8PAuAKzU5rSMj95hD5CwvlMFDaNih4u9kj-PtuwuKdC2iOX6JoMOwU6NmszbN6ra346QEtRhA-EdhvSBpp-3d8OdIOrekFVvvoDwTZwRh0af53bqJbcK-LMXfX-pcNX9icKjQS6dXjgzdTIqd7V27BSBHWBCnQ5gRZQaInt23S7F73lRjLsGwsHqsNlk2_2g8bgKLAntGXNxm3S2jAQDA4WQ48wRSaxuRy1oNXeMK8QGlrij7oHhHb6W7XqQnEiQP3xf-b77LKXkdMBUJLErrFtgAMGhGhKHrK653gbjLVYZQmY6Q";

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

// ⭐️ 1. 이 함수를 새로 추가합니다. (Send와 Stop을 모두 처리)
function handleSendClick() {
    if (abortController) {
        // "중지" 버튼 상태일 때: 중지 함수 호출
        stopGeneration();
    } else {
        // "전송" 버튼 상태일 때: 메시지 전송
        sendMessage();
    }
}

// ⭐️ 3. 세션 ID 관리를 위한 전역 변수
let currentSessionId = null;
let currentBotMessageElement = null; // 현재 봇 응답을 저장할 임시 변수

// --- 1. 이벤트 리스너 ---
document.addEventListener('DOMContentLoaded', initializeChat);
sendButton.addEventListener('click', handleSendClick); // ⭐️ sendMessage -> handleSendClick

chatInput.addEventListener('keydown', (e) => {
    // ⭐️ event.isComposing이 false일 때만(한글 조합이 끝났을 때만) Enter가 작동하도록 수정
    if (e.key === 'Enter' && !e.shiftKey && !e.isComposing) {
        e.preventDefault(); // 줄바꿈 방지
        handleSendClick(); // ⭐️ sendMessage -> handleSendClick
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
        <button class="quick-reply">안전보건 데이터를 확인하고 싶어, 어떤 테이블을 확인해야 해?</button>
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
    handleSendClick(); // ⭐️ sendMessage -> handleSendClick
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
async function sendMessage() {
    const messageText = chatInput.value.trim();
    if (messageText === "" || abortController) return; // ⭐️ 이미 실행 중이면 중복 실행 방지
    
    addMessageToUI(messageText, 'sent');
    chatInput.value = "";

    // ⭐️ 이 줄을 추가하여 입력창을 비활성화합니다.
    chatInput.disabled = true;
    
    // ⭐️ 1. "답변 생성하는 중입니다..." 텍스트로 봇 메시지 요소를 생성합니다.
    currentBotMessageElement = createMessageElement("답변 생성하는 중입니다...", 'received');
    
    chatBody.insertBefore(currentBotMessageElement, chatBottomSpacer); 
    
    // ⭐️ 2. addTypingIndicator는 점(dot) 애니메이션을 추가할 수 있으니 그대로 둡니다.
    // (이제 "답변 생성하는 중입니다..." 텍스트와 점 애니메이션이 같이 보일 것입니다.)
    addTypingIndicator(currentBotMessageElement);

    try {
        // ⭐️ 1. AbortController 생성 및 버튼 교체
        abortController = new AbortController();
        sendButton.innerHTML = ICON_STOP;
        sendButton.title = "중지";
        sendButton.classList.add('stop-button'); // ⭐️ 빨간색 클래스 추가

        const response = await fetch(API_URL, {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + TEMP_AUTH_TOKEN
            },
            body: JSON.stringify({ 
                message: messageText,
                sessionId: currentSessionId
            }),
            signal: abortController.signal // ⭐️ 2. fetch에 중단 신호 연결
        });

        if (!response.ok) {
            // ⭐️ 3. HTTP 오류 발생 시, "답변 생성..." 텍스트를 오류 메시지로 변경합니다.
            if (currentBotMessageElement) {
                removeTypingIndicator(currentBotMessageElement); 
                let textSpan = currentBotMessageElement.querySelector('.message-text');
                // ⭐️ textSpan.textContent = "" 라인을 삭제합니다.
            }
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const reader = response.body.getReader();
        const decoder = new TextDecoder('utf-8');
        let streamingText = ""; 
        let isFirstChunk = true; // ⭐️ 첫 청크인지 확인

        while (true) {
            const { done, value } = await reader.read();
            if (done) {
                finalizeMessage(currentBotMessageElement); // 스트림 끝나면 복사 버튼 추가
                break;
            }
            
            let chunkText = decoder.decode(value, { stream: true });

            // ----------------------------------------------------
            // ⭐️ (수정 1) sessionId 파싱 로직 ⭐️
            // ----------------------------------------------------
            if (isFirstChunk) {
                try {
                    // .trim()으로 백엔드의 \n 제거 후 JSON 파싱 시도
                    const data = JSON.parse(chunkText.trim());
                    
                    if (data.sessionId) {
                        // ⭐️ JSON 파싱 성공! (이 청크는 sessionId임)
                        currentSessionId = data.sessionId; // 새 세션 ID 저장
                        isFirstChunk = false; // 첫 청크(JSON) 처리 완료
                        continue; // ⭐️ 화면에 렌더링하지 않고 다음 루프로 건너뛰기
                    }
                } catch (e) {
                    // 파싱 실패 (JSON이 아니거나, 쪼개진 경우)
                    // (쪼개진 경우) 다음 청크를 기다리기 위해 isFirstChunk = true 유지
                    if (chunkText.includes('{"sessionId":')) {
                         console.log("Waiting for more JSON chunk...");
                         continue; // ⭐️ 화면에 그리지 않고 건너뛰기
                    }
                    // (JSON이 아닌 첫 텍스트 청크인 경우) 아래 로직으로 이동
                }

                // ----------------------------------------------------
                // ⭐️ (수정 2) "답변 생성중" 텍스트를 여기서 지웁니다.
                // ----------------------------------------------------
                // (sessionId 청크가 아니고, *첫 번째 실제 텍스트 청크*일 때)
                
                // (isFirstChunk 플래그를 한 번만 사용)
                removeTypingIndicator(currentBotMessageElement); 
                let textSpan = currentBotMessageElement.querySelector('.message-text');
                if (textSpan) {
                    textSpan.textContent = ""; // ⭐️ "답변 생성중..."을 비움
                }
                isFirstChunk = false; // ⭐️ 첫 텍스트 청크 처리가 끝났음을 표시
            }
            
            // ----------------------------------------------------
            // ⭐️ (수정 3) 텍스트를 화면에 추가
            // ----------------------------------------------------
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
        // ⭐️ 3. 중단 시 오류 처리
        if (error.name === 'AbortError') {
            console.log("Stream stopped by user.");
            if (currentBotMessageElement) {
                // ⭐️ 1. "점점점" 인디케이터를 제거합니다.
                removeTypingIndicator(currentBotMessageElement);

                let textSpan = currentBotMessageElement.querySelector('.message-text');
                if (textSpan) {
                    // ⭐️ 2. 텍스트를 "사용자가 질문을 중지했습니다."로 설정합니다.
                    textSpan.textContent = "사용자가 질문을 중지했습니다.";
                    
                    // ⭐️ 3. (선택) 중지된 메시지도 에러처럼 보이도록 빨간색으로 표시
                    currentBotMessageElement.classList.add('error');
                    
                    // ⭐️ 4. (제거) 복사 버튼은 추가하지 않습니다.
                    // finalizeMessage(currentBotMessageElement); 
                }
            }
        } else {
            console.error('Error fetching stream response:', error);
            // ⭐️ 5. (중요) HTTP 오류가 아닌 다른 예외(네트워크 오류 등)가 발생했을 때도 텍스트를 변경합니다.
            if (currentBotMessageElement) {
                removeTypingIndicator(currentBotMessageElement);
                let textSpan = currentBotMessageElement.querySelector('.message-text');
                
                // 텍스트가 "답변 생성..." 상태일 때만 오류 메시지로 덮어씁니다.
                if(textSpan && (textSpan.textContent === '답변 생성하는 중입니다...' || textSpan.textContent === '')) {
                    textSpan.textContent = '죄송합니다. 오류가 발생했습니다.';
                }
                currentBotMessageElement.classList.add('error');
            }
        }
    } finally {
        // ⭐️ 1. (신규) 인디케이터가 남아있으면 확실히 제거합니다.
        if (currentBotMessageElement) {
            removeTypingIndicator(currentBotMessageElement);
        }
        
        // ⭐️ 2. (신규) 입력창을 다시 활성화합니다.
        chatInput.disabled = false;

        // ⭐️ 3. 버튼을 "전송" 상태로 원상복구
        abortController = null; 
        sendButton.innerHTML = ICON_SEND;
        sendButton.title = "전송";
        sendButton.classList.remove('stop-button'); // ⭐️ 빨간색 클래스 제거

        currentBotMessageElement = null; 
        resetButton.style.display = 'flex'; // 홈 버튼 표시
        scrollToBottom();
        
        // ⭐️ 4. (신규) 사용자가 바로 입력할 수 있게 포커스
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
    typingIndicator.innerHTML = '<span>.</span><span>.</span><span>.</span>';
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

// ⭐️ 7. "이전 대화" 버튼 클릭 시
prevChatButton.addEventListener('click', async () => {
    try {
        // 백엔드에서 세션 목록 가져오기 (⭐️ API_SESSIONS_URL은 실제 경로로 변경)
        const response = await fetch('/api/sessions', {
            headers: { 'Authorization': 'Bearer ' + TEMP_AUTH_TOKEN }
        });
        if (!response.ok) throw new Error('대화 목록 로드 실패');
        
        const sessions = await response.json();
        
        historyList.innerHTML = ''; // 기존 목록 비우기
        if (sessions.length === 0) {
            historyList.innerHTML = '<li>이전 대화가 없습니다.</li>';
        } else {
            sessions.forEach(session => {
                const li = document.createElement('li');
                // ⭐️ (수정 필요) session.session_title 대신 실제 DynamoDB의 '제목' 속성을 사용
                li.textContent = session.session_title || (new Date(session.session_id)).toLocaleString();
                li.dataset.sessionId = session.session_id; // ⭐️ li에 세션 ID 저장
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
    if (event.target.tagName === 'LI' && event.target.dataset.sessionId) {
        const sessionId = event.target.dataset.sessionId;
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
    
    try {
        // 백엔드에서 메시지 목록 가져오기 (⭐️ API_MESSAGES_URL은 실제 경로로 변경)
        const response = await fetch(`/api/messages/${sessionId}`, {
            headers: { 'Authorization': 'Bearer ' + TEMP_AUTH_TOKEN }
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
    }
}