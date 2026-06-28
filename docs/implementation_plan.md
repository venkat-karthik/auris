# Visual Workflow Builder UI & Core Gaps Implementation

## Goal Description

Complete the remaining high‑priority features for **Auris**:
1. Warm call transfer (human hand‑off) – frontend button and backend endpoint.
2. Voicemail detection service (OpenAI Whisper with Google fallback).
3. Call recording upload/download endpoints and storage handling.
4. (Optional) Hook the new endpoints into existing UI.

## User Review Required

> [!NOTE]
> No user decisions are pending at this time. The plan follows the design preferences already captured.

## Open Questions

> [!NOTE]
> None.

## Proposed Changes

---
### Frontend (Next.js / React)

#### [MODIFY] src/app/calls/page.tsx
- Add a **Transfer to Agent** button in the action column of the call list.
- On click, open a small modal to select a target agent (dropdown of agents fetched from `/agents`).
- Submit a POST request to `/api/v1/calls/{call_id}/warm_transfer` with `{ target_agent_id, whisper_url? }`.
- Show a success/error toast.

---
### Backend (FastAPI / Python)

#### [MODIFY] backend/app/core/config.py
- Add `RECORDINGS_DIR` env var with default `"/app/recordings"`.
- Ensure the directory exists at startup (create if missing).

#### [MODIFY] backend/app/routes/calls.py
- Import `warm_transfer` from `app.services.transfer_manager` and `RECORDINGS_DIR`.
- Add request model `WarmTransferRequest` with `target_agent_id: int` and optional `whisper_url: Optional[str]`.
- Implement `POST /{call_id}/warm_transfer` that:
  1. Validates the call belongs to the org.
  2. Calls `await warm_transfer(call_id, req.target_agent_id, req.whisper_url)`.
  3. Returns `{ success: bool }`.
- Add `POST /{call_id}/recording` to accept `UploadFile` (audio), store under `RECORDINGS_DIR` as `<call_id>_<filename>`.
- Update `CallRun.recording_path` with the absolute path (or relative to `RECORDINGS_DIR`).
- Add `GET /{call_id}/recording` returning a `FileResponse` if the file exists.
- Include proper error handling and permissions.

#### [NEW] backend/app/services/voicemail_detection.py
- Service class `VoicemailDetector` with method `async def detect(audio_bytes: bytes) -> dict`.
- Try OpenAI Whisper via `openai.Audio.transcribe` (requires `OPENAI_API_KEY`).
- On failure or if Whisper not available, fallback to Google Speech‑to‑Text using `google.cloud.speech` (requires `GOOGLE_APPLICATION_CREDENTIALS`).
- Return `{ "is_voicemail": bool, "transcript": str }`.
- Add simple unit‑testable structure (no external network call in tests – will be mocked).

#### [MODIFY] backend/app/services/dialer_service.py (or pipeline integration point)
- After outbound audio is captured, call `VoicemailDetector.detect` and store result in `CallRun.voicemail` (as `'true'`/`'false'`).

#### [MODIFY] backend/app/models/call_run.py
- Ensure `voicemail` column can store `'true'`/`'false'` (already present).

---
### Infrastructure

#### [MODIFY] docker-compose.yml
- Add a volume `recordings:/app/recordings`.
- Ensure `ffmpeg` service exists for possible audio conversion (already referenced in plan).

#### [DOC] docs/recording_storage.md
- Document how to switch from local volume to S3/DB BLOB storage.

---
### Tests

#### [NEW] backend/tests/test_warm_transfer.py
- Mock `transfer_manager.warm_transfer` and verify endpoint returns success and updates DB.

#### [NEW] backend/tests/test_recording_endpoints.py
- Upload a dummy audio file, verify file is saved and downloadable.

#### [NEW] backend/tests/test_voicemail_detection.py
- Mock OpenAI and Google clients, test fallback logic.

## Verification Plan

### Automated Tests
- Run `pytest` covering the new backend services and endpoints.
- Run `npm test` for frontend button interaction (React Testing Library).

### Manual Verification
- Start dev servers (`npm run dev` & `uvicorn backend/app/main:app --reload`).
- In the Calls UI, click **Transfer to Agent**, select an agent, and confirm the call bridges (check Twilio console).
- Trigger an outbound call that ends in voicemail, ensure the UI marks the call with a voicemail flag.
- Record a call, then download via the new endpoint and play locally.
- Verify the recordings are persisted under the Docker volume.

---
