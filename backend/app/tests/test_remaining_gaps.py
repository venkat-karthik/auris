import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, UTC, timedelta
from sqlalchemy import select
import httpx
import io

from app.models.agent import Agent
from app.models.call_run import CallRun
from app.models.phone_number import PhoneNumber
from app.models.knowledge_base import KnowledgeBaseDocument
from app.services.pipeline.stt.vad import VADProcessor
from app.services.pipeline.frame import Frame, FrameType
from app.services.rag_service import ingest_document

@pytest.mark.asyncio
async def test_call_run_enrichment_and_filtering(client, db_session, test_org, test_user, override_auth, auth_headers):
    # Setup agents and runs
    agent1 = Agent(org_id=test_org.id, created_by=test_user.id, name="Agent 1")
    agent2 = Agent(org_id=test_org.id, created_by=test_user.id, name="Agent 2")
    db_session.add_all([agent1, agent2])
    await db_session.flush()

    run1 = CallRun(
        org_id=test_org.id,
        agent_id=agent1.id,
        transport="webrtc",
        call_type="inbound",
        status="completed",
        caller_number="+1111111111",
        called_number="+2222222222",
        disposition="completed",
        summary="A nice chat about pricing",
        sentiment="positive",
        key_topics=["pricing"],
        task_completed=True,
        created_at=datetime.now(UTC) - timedelta(days=2)
    )
    run2 = CallRun(
        org_id=test_org.id,
        agent_id=agent2.id,
        transport="twilio",
        call_type="outbound",
        status="failed",
        caller_number="+3333333333",
        called_number="+4444444444",
        disposition="no_answer",
        summary="No answer",
        sentiment="neutral",
        key_topics=[],
        task_completed=False,
        created_at=datetime.now(UTC)
    )
    db_session.add_all([run1, run2])
    await db_session.commit()

    # 1. Test enriched detail response
    response = await client.get(f"/calls/{run1.id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["summary"] == "A nice chat about pricing"
    assert data["sentiment"] == "positive"
    assert data["key_topics"] == ["pricing"]
    assert data["task_completed"] is True

    # 2. Test dedicated analysis endpoint
    response = await client.get(f"/calls/{run1.id}/analysis", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["call_id"] == run1.id
    assert data["summary"] == "A nice chat about pricing"
    assert data["sentiment"] == "positive"

    # 3. Test GET /calls filtering by agent_id
    response = await client.get(f"/calls?agent_id={agent2.id}", headers=auth_headers)
    assert response.status_code == 200
    runs = response.json()
    assert len(runs) == 1
    assert runs[0]["id"] == run2.id

    # 4. Test filtering by call_type
    response = await client.get("/calls?call_type=inbound", headers=auth_headers)
    assert response.status_code == 200
    runs = response.json()
    assert len(runs) == 1
    assert runs[0]["id"] == run1.id


@pytest.mark.asyncio
async def test_webhook_lifecycle_dispatcher(db_session, test_org, test_user):
    agent = Agent(
        org_id=test_org.id,
        created_by=test_user.id,
        name="Webhook Agent",
        model_config={"server_url": "https://customer.server/webhook"}
    )
    db_session.add(agent)
    await db_session.flush()

    run = CallRun(
        org_id=test_org.id,
        agent_id=agent.id,
        transport="twilio",
        call_type="inbound",
        status="running",
        caller_number="+15555555555",
        created_at=datetime.now(UTC)
    )
    db_session.add(run)
    await db_session.commit()

    from app.services.webhook_dispatcher import dispatch_call_webhook

    with patch("httpx.AsyncClient.post") as mock_post:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_post.return_value = mock_resp

        # Dispatch started event
        await dispatch_call_webhook(db_session, run.id, "call.started")
        mock_post.assert_called_once()
        called_args, called_kwargs = mock_post.call_args
        import json
        sent_payload = json.loads(called_kwargs["content"].decode("utf-8"))
        assert sent_payload["event"] == "call_started"
        assert sent_payload["call"]["id"] == run.id


@pytest.mark.asyncio
async def test_docx_kb_ingestion(db_session):
    # Setup dummy DOCX bytes
    docx_file = io.BytesIO()
    import docx
    doc = docx.Document()
    doc.add_paragraph("Auris platform contains state of the art RAG systems.")
    doc.save(docx_file)
    docx_bytes = docx_file.getvalue()

    # Stub the openai embedding client call
    with patch("app.services.rag_service.chunk_text") as mock_chunk, \
         patch("app.services.rag_service.pypdf", None):
        mock_chunk.return_value = ["Auris platform contains state of the art RAG systems."]

        # Ingest document
        await ingest_document(db_session, 999, docx_bytes, "test_doc.docx")
        mock_chunk.assert_called_once_with("Auris platform contains state of the art RAG systems.")


@pytest.mark.asyncio
async def test_webrtc_vad_fallback():
    # Verify that VADProcessor uses RMS when webrtcvad is missing or fails
    processor = VADProcessor(threshold=300.0, silence_limit_ms=100.0, onset_limit_ms=30.0)
    assert processor.vad is None  # Since we commented out webrtcvad, it must fall back to RMS

    # Mock emitting
    emitted = []
    async def mock_emit(frame):
        emitted.append(frame)
    processor.emit = mock_emit

    # 1. Emit CALL_START
    await processor.process_frame(Frame(type=FrameType.CALL_START))
    assert len(emitted) == 1
    assert emitted[0].type == FrameType.CALL_START

    # 2. Emit silent audio frame (low amplitude)
    silent_audio = b"\x00\x00" * 160  # 10ms frame
    await processor.process_frame(Frame(type=FrameType.AUDIO_IN, data=silent_audio))
    assert not processor.is_speaking

    # 3. Emit loud audio frame (exceeds threshold)
    loud_audio = b"\xff\x7f" * 160
    # Process multiple frames to exceed onset limit of 30ms
    for _ in range(4):
        await processor.process_frame(Frame(type=FrameType.AUDIO_IN, data=loud_audio))

    assert processor.is_speaking
    # Confirm we emitted USER_SPEAKING
    speaking_events = [f for f in emitted if f.type == FrameType.USER_SPEAKING]
    assert len(speaking_events) >= 1


@pytest.mark.asyncio
async def test_twilio_number_provisioning_endpoints(client, db_session, test_org, test_user, override_auth, auth_headers):
    # Ensure organization has sufficient credit balance
    test_org.balance_credits = 1000.0
    db_session.add(test_org)
    await db_session.commit()

    # Mock Twilio Client available numbers and creation
    with patch("app.routes.phone_numbers.config.TWILIO_ACCOUNT_SID", "ACreal_sid"), \
         patch("twilio.rest.Client") as mock_client_class:
        
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        # Mock Search
        mock_number_record = MagicMock()
        mock_number_record.phone_number = "+15005550006"
        mock_number_record.locality = "Dallas"
        mock_number_record.rate_center = "TX"
        mock_client.available_phone_numbers().local.list.return_value = [mock_number_record]

        # Mock Buy
        mock_incoming_record = MagicMock()
        mock_incoming_record.sid = "PN12345"
        mock_client.incoming_phone_numbers.create.return_value = mock_incoming_record

        # 1. Test Search route
        response = await client.get("/phone-numbers/search?area_code=500", headers=auth_headers)
        assert response.status_code == 200
        results = response.json()
        assert len(results) == 1
        assert results[0]["phone_number"] == "+15005550006"
        assert results[0]["region"] == "Dallas, TX"

        # 2. Test Buy route
        response = await client.post(
            "/phone-numbers/buy",
            json={"phone_number": "+15005550006", "label": "Twilio Office Line"},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["phone_number"] == "+15005550006"
        assert data["label"] == "Twilio Office Line"
