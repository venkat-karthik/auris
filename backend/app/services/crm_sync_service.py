"""
Auris - CRM Sync Service
Handles pushing post-call analysis data to external CRMs like HubSpot and Salesforce.
"""
import httpx
from loguru import logger
from typing import Dict, Any

async def sync_to_hubspot(credentials: Dict[str, Any], call_data: Dict[str, Any]) -> None:
    """
    Syncs the call analysis and transcript to HubSpot CRM as an Engagement Note.
    """
    auth_token = credentials.get("auth_token")
    if not auth_token or auth_token == "demo_token":
        logger.info(f"CRM Sync [HubSpot]: Mocked successful sync for call {call_data.get('call_id')}")
        return

    # In a real environment, we'd hit the HubSpot API
    hubspot_url = "https://api.hubapi.com/engagements/v1/engagements"
    headers = {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "engagement": {
            "active": True,
            "type": "CALL"
        },
        "associations": {
            # Typically you'd lookup the contactId based on caller_number
            "contactIds": []
        },
        "metadata": {
            "body": f"Auris Call Summary:\n{call_data.get('summary')}\n\nTranscript:\n{call_data.get('transcript')}",
            "status": "COMPLETED"
        }
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(hubspot_url, json=payload, headers=headers)
            if resp.is_success:
                logger.info(f"CRM Sync [HubSpot]: Successfully pushed call {call_data.get('call_id')}")
            else:
                logger.error(f"CRM Sync [HubSpot]: Failed with status {resp.status_code}")
    except Exception as e:
        logger.error(f"CRM Sync [HubSpot]: Exception during sync - {e}")


async def sync_to_salesforce(credentials: Dict[str, Any], call_data: Dict[str, Any]) -> None:
    """
    Syncs the call analysis to Salesforce as a Task/Activity record.
    """
    auth_token = credentials.get("auth_token")
    instance_url = credentials.get("instance_url", "https://yourInstance.salesforce.com")
    
    if not auth_token or auth_token == "demo_token":
        logger.info(f"CRM Sync [Salesforce]: Mocked successful sync for call {call_data.get('call_id')}")
        return

    sf_url = f"{instance_url}/services/data/v52.0/sobjects/Task/"
    headers = {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "Subject": f"Auris Voice AI Call - {call_data.get('disposition')}",
        "Status": "Completed",
        "Priority": "Normal",
        "Description": f"Summary: {call_data.get('summary')}\n\nSentiment: {call_data.get('sentiment')}\n\nTranscript: {call_data.get('transcript')}"
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(sf_url, json=payload, headers=headers)
            if resp.is_success:
                logger.info(f"CRM Sync [Salesforce]: Successfully pushed call {call_data.get('call_id')}")
            else:
                logger.error(f"CRM Sync [Salesforce]: Failed with status {resp.status_code}")
    except Exception as e:
        logger.error(f"CRM Sync [Salesforce]: Exception during sync - {e}")
