import streamlit as st
import boto3
import uuid
import json
from requests_aws4auth import AWS4Auth
import requests

# ==============================
# 🔹 공통 설정
# ==============================
region = "ap-northeast-2"
domain_id = "dzd-cjvglgj4d43fmg"

# Boto3 세션 & 인증
session = boto3.Session()
credentials = session.get_credentials().get_frozen_credentials()

auth = AWS4Auth(
    credentials.access_key,
    credentials.secret_key,
    region,
    "datazone",
    session_token=credentials.token
)

# ==============================
# 🔹 1️⃣ 현재 사용자 Bedrock Agents 조회
# ==============================
client_dz = boto3.client("datazone", region_name=region)

# 앱이 로드될 때 ASP.NET이 전달한 ?username=... 값을 읽어옵니다.
query_params = st.query_params

# .get("키", [기본값])[0] -> 'username' 파라미터가 없으면 '게스트'를 사용
user_email = query_params.get("username", ["게스트"])
st.write(f"디버깅: 현재 사용자 이메일 = {user_email}, 길이 = {len(user_email)}")
# 사용자 조회
resp_users = client_dz.search_user_profiles(
    domainIdentifier=domain_id,
    userType="DATAZONE_IAM_USER",
    searchText=user_email
)
items = resp_users.get("items", [])
if not items:
    st.error(f"{user_email} 사용자를 찾을 수 없음")
    st.stop()

user_id = items[0]["id"]

# 구독된 BedrockChatAssetType 조회
url_sub = f"https://datazone.{region}.api.aws/v2/domains/{domain_id}/subscriptions"
params = {"owningUserId": user_id, "status": "APPROVED"}
resp_sub = requests.get(url_sub, auth=auth, params=params)
resp_sub.raise_for_status()
all_data = resp_sub.json()

bedrock_chat_assets = [
    item for item in all_data.get("items", [])
    if item.get("subscribedListing", {}).get("item", {}).get("assetListing", {}).get("entityType") == "BedrockChatAssetType"
]

agent_mapping = {}
for asset in bedrock_chat_assets:
    listing_id = asset["subscribedListing"]["id"]
    listing_name = asset["subscribedListing"]["name"]
    # Alias & Environment 조회
    url_list = f"https://datazone.{region}.api.aws/v2/domains/{domain_id}/listings/{listing_id}"
    resp_list = requests.get(url_list, auth=auth)
    resp_list.raise_for_status()
    data = resp_list.json()
    forms_str = data["item"]["assetListing"].get("forms", "{}")
    forms = json.loads(forms_str)
    bedrock_form = forms.get("BedrockAppCommonForm", {})
    alias_id = bedrock_form.get("sharedAliasOrVersion")
    env_id = bedrock_form.get("environmentId")

    if alias_id and env_id:
        agent_mapping[listing_name] = {
            "alias_id": alias_id,
            "environment_id": env_id
        }

# ==============================
# 🔹 2️⃣ Bedrock Agents 전체 조회 (Agent ID 매핑)
# ==============================
bedrock_client = boto3.client("bedrock-agent", region_name=region)
agents = []
next_token = None
while True:
    params = {"maxResults": 20}
    if next_token:
        params["nextToken"] = next_token
    resp = bedrock_client.list_agents(**params)
    agents.extend(resp.get("agentSummaries", []))
    next_token = resp.get("nextToken")
    if not next_token:
        break

for name, info in agent_mapping.items():
    env_id = info["environment_id"]
    expected_name = f"Bedrock-Agent-{env_id}"
    found_agent = next((a for a in agents if a["agentName"] == expected_name), None)
    if found_agent:
        agent_mapping[name]["agent_id"] = found_agent["agentId"]
    else:
        agent_mapping[name]["agent_id"] = None
    # 환경 ID 제거
    agent_mapping[name].pop("environment_id", None)

if not agent_mapping:
    st.warning("현재 계정에 할당된 Bedrock Agent가 없습니다.")
    st.stop()

# ==============================
# 🔹 3️⃣ Streamlit UI: 콤보박스
# ==============================
st.set_page_config(page_title="그룹웨어 챗봇", layout="centered")
st.title("그룹웨어 챗봇")

selected_agent_name = st.selectbox("사용할 Agent 선택", list(agent_mapping.keys()))
selected_agent = agent_mapping[selected_agent_name]
AGENT_ID = selected_agent["agent_id"]
AGENT_ALIAS_ID = selected_agent["alias_id"]

# 세션 ID 관리
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

# 채팅 기록 관리
if "messages" not in st.session_state:
    st.session_state.messages = []

# 채팅 기록 표시
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 사용자 입력
if prompt := st.chat_input("무엇이 궁금하신가요?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""

        try:
            bedrock_runtime = boto3.client("bedrock-agent-runtime", region_name=region)
            response = bedrock_runtime.invoke_agent(
                agentId=AGENT_ID,
                agentAliasId=AGENT_ALIAS_ID,
                sessionId=st.session_state.session_id,
                inputText=prompt
            )

            # 스트리밍 응답 처리
            for event in response["completion"]:
                if "chunk" in event:
                    chunk = event["chunk"]
                    full_response += chunk["bytes"].decode("utf-8")
                    message_placeholder.markdown(full_response + "▌")

            message_placeholder.markdown(full_response)

        except Exception as e:
            st.error(f"오류가 발생했습니다: {e}")
            full_response = "죄송합니다. 답변 생성 중 문제가 발생했습니다."
            message_placeholder.markdown(full_response)

    st.session_state.messages.append({"role": "assistant", "content": full_response})
