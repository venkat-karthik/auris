# Recording and Voicemail Storage Architecture

Auris handles call recording and voicemail detection using a dual-backend storage model (MinIO/S3 or local persistent disk) and external speech analytics services.

## Storage Backends

The platform supports two storage backends configurable via the `STORAGE_BACKEND` environment variable:

1. **Local Persistent Storage** (`STORAGE_BACKEND=local`):
   - Used during local development and lightweight deployments.
   - Recordings are saved to the directory specified by `RECORDINGS_DIR` (defaults to `/app/recordings`).
   - In dockerized deployments, this directory is mounted to a persistent Docker volume (`recordings_data`).

2. **Object Storage** (`STORAGE_BACKEND=minio` or `s3`):
   - Used for production or highly scalable deployments.
   - Recordings and transcripts are uploaded to MinIO or AWS S3 buckets.
   - The bucket name is configured via `MINIO_BUCKET` (defaults to `auris-audio`).

## Directory Layout in Object Storage

- **Call Recordings**: `recordings/{call_run_id}_recording.mp3`
- **Call Transcripts**: `transcripts/{call_run_id}.txt`

## Endpoints

- `POST /api/v1/calls/{call_id}/recording`: Uploads raw audio file.
- `GET /api/v1/calls/{call_id}/recording`: Downloads/streams the raw call audio as MP3.
- `GET /api/v1/calls/{call_id}/transcript`: Downloads call transcription segments from storage.

## Voicemail Detection

Voicemail detection is performed inline on outbound campaigns:
1. When an outbound call starts streaming, the first 5 seconds of audio are accumulated in memory.
2. The accumulated PCM stream is sent to the `VoicemailDetector` service.
3. The service transcribes the snippet via OpenAI Whisper (falling back to Google Speech-to-Text).
4. A keyword analyzer checks for standard voicemail cues (e.g. *"please leave a message"*).
5. The boolean classification is saved to the `voicemail` field in the database.
