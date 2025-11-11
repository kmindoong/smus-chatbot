# app/services/bedrock_service.py

import json
import requests # ⭐️ [신규]
import traceback 
from datetime import datetime, timezone
from app.core.config import settings
from app.services.dynamodb_service import save_message, create_session
# ⭐️ [수정] Boto3 세션에서 필요한 모든 클라이언트 임포트
from app.services.boto3_session import (
    bedrock_agent_client, 
    bedrock_agent_mgmt_client, 
    datazone_client, 
    get_datazone_auth_signer
)

# ⭐️ [신규] Jupyter Notebook 로직을 FastAPI 함수로 이식
def get_available_agents(user_email: str) -> dict:
    """
    DataZone API를 호출하여 해당 사용자가 구독(공유)한 
    Bedrock Agent 목록을 조회합니다. (search_shared_app.ipynb 로직 기반)
    """
    if not user_email:
        print("[AGENT_LIST] Error: User email is missing.")
        return {}
        
    domain_id = settings.DATAZONE_DOMAIN_ID
    region = settings.AWS_REGION
    dz_auth_signer = get_datazone_auth_signer() # DataZone API 서명자

    agent_mapping = {}

    try:
        # 1. DataZone에서 이메일로 사용자 ID 조회 (Notebook Cell 5)
        print(f"[AGENT_LIST] Searching DataZone user: {user_email}")
        resp_users = datazone_client.search_user_profiles(
            domainIdentifier=domain_id,
            userType="DATAZONE_IAM_USER", # ⭐️ 환경에 따라 DATAZONE_SSO_USER 일 수 있음
            searchText=user_email,
            maxResults=1
        )
        items = resp_users.get("items", [])
        if not items:
            print(f"[AGENT_LIST] User not found in DataZone: {user_email}")
            return {}
        
        user_id = items[0].get("id")
        if not user_id:
            print(f"[AGENT_LIST] User ID not found for: {user_email}")
            return {}

        # 2. DataZone API로 구독된 Bedrock 챗봇 애셋 조회 (Notebook Cell 7)
        print(f"[AGENT_LIST] Fetching subscriptions for user: {user_id}")
        url_sub = f"https://datazone.{region}.api.aws/v2/domains/{domain_id}/subscriptions"
        params_sub = {"owningUserId": user_id, "status": "APPROVED"}
        resp_sub = requests.get(url_sub, auth=dz_auth_signer, params=params_sub)
        resp_sub.raise_for_status()
        
        bedrock_chat_assets = [
            item for item in resp_sub.json().get("items", [])
            if item.get("subscribedListing", {}).get("item", {}).get("assetListing", {}).get("entityType") == "BedrockChatAssetType"
        ]
        
        if not bedrock_chat_assets:
            print("[AGENT_LIST] No approved 'BedrockChatAssetType' subscriptions found.")
            return {}

        # 3. Bedrock Agent 전체 목록 조회 (ID 매핑용) (Notebook Cell 11)
        print("[AGENT_LIST] Fetching all Bedrock agents...")
        all_bedrock_agents = []
        paginator = bedrock_agent_mgmt_client.get_paginator('list_agents')
        for page in paginator.paginate(maxResults=20):
            all_bedrock_agents.extend(page.get("agentSummaries", []))

        # 4. 구독 목록을 순회하며 Agent ID/Alias ID 추출 (Notebook Cell 9 + 11)
        print(f"[AGENT_LIST] Mapping {len(bedrock_chat_assets)} assets...")
        for asset in bedrock_chat_assets:
            try:
                listing_name = asset["subscribedListing"]["name"]
                listing_id = asset["subscribedListing"]["id"]

                # 4-1. Listing 상세 조회로 Alias/Env ID 가져오기 (Cell 9)
                url_list = f"https://datazone.{region}.api.aws/v2/domains/{domain_id}/listings/{listing_id}"
                resp_list = requests.get(url_list, auth=dz_auth_signer)
                resp_list.raise_for_status()
                
                forms_str = resp_list.json()["item"]["assetListing"].get("forms", "{}")
                forms = json.loads(forms_str)
                bedrock_form = forms.get("BedrockAppCommonForm", {})
                
                alias_id = bedrock_form.get("sharedAliasOrVersion")
                env_id = bedrock_form.get("environmentId")

                if not (alias_id and env_id):
                    print(f"[AGENT_LIST] Skipping '{listing_name}': Missing aliasId or envId.")
                    continue

                # 4-2. Env ID로 실제 Agent ID 찾기 (Cell 11)
                expected_agent_name = f"Bedrock-Agent-{env_id}"
                found_agent = next((a for a in all_bedrock_agents if a["agentName"] == expected_agent_name), None)
                
                if found_agent:
                    agent_mapping[listing_name] = {
                        "agent_id": found_agent["agentId"],
                        "alias_id": alias_id
                    }
                    print(f"[AGENT_LIST] Mapped '{listing_name}' -> {found_agent['agentId']}")
                else:
                    print(f"[AGENT_LIST] Warning: Agent '{expected_agent_name}' not found for listing '{listing_name}'.")

            except Exception as item_error:
                print(f"[AGENT_LIST] Error processing asset '{asset.get('subscribedListing',{}).get('name')}': {item_error}")
                
        print(f"[AGENT_LIST] Mapping complete. Found {len(agent_mapping)} agents.")
        return agent_mapping

    except Exception as e:
        print("--- !!! ERROR IN get_available_agents !!! ---")
        traceback.print_exc()
        return {} # 오류 발생 시 빈 목록 반환

# ⭐️ [수정] stream_agent_response 함수 시그니처 변경
def stream_agent_response( 
    user_sub: str, 
    session_id: str | None, 
    message_text: str,
    agent_id: str,         # ⭐️ [추가]
    agent_alias_id: str    # ⭐️ [추가]
):
    """
    [수정] Bedrock Agent의 'invoke_agent' (동기)를 호출하고,
    sessionId가 정규식(regex) 제약 조건을 만족하도록 수정합니다.
    """
    
    is_new_chat = False
    session_id_to_use = session_id 
    
    if not session_id:
        is_new_chat = True
        # ⭐️ (수정) .isoformat()이 '+00:00'을 생성하므로, 'Z'로 대체합니다.
        session_id_to_use = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
    
    try:
        # --- (이하 DB 저장 및 Bedrock 호출 로직은 기존과 동일) ---
        save_message(
            session_id=session_id_to_use, 
            role='user', 
            content=message_text
        )
        if is_new_chat:
            create_session(
                user_id=user_sub, 
                session_id=session_id_to_use, 
                title=message_text
            )

        if is_new_chat:
            yield json.dumps({"sessionId": session_id_to_use}) + "\n"
            
        # ⭐️ [수정] 하드코딩된 settings 대신 파라미터 사용
        response = bedrock_agent_client.invoke_agent( 
            agentId=agent_id,
            agentAliasId=agent_alias_id,
            sessionId=session_id_to_use, 
            inputText=message_text
        )
        
        # --- 스트리밍 응답 처리 (수정 불필요) ---
        full_bot_response = ""
        stream = response.get('completion') 
        if stream:
            for event in stream:
                if 'chunk' in event:
                    chunk = event['chunk']
                    if 'bytes' in chunk:
                        decoded_chunk = chunk['bytes'].decode('utf-8')
                        full_bot_response += decoded_chunk
                        yield decoded_chunk 
        
        if full_bot_response:
            save_message(
                session_id=session_id_to_use,
                role='bot',
                content=full_bot_response
            )
            
    except Exception as e:
        print("--- !!! ERROR IN bedrock_service.stream_agent_response !!! ---")
        traceback.print_exc()
        raise e