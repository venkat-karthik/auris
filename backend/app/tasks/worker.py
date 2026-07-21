"""
Auris - ARQ Background Task Worker
Handles post-call processing, credit deduction, MinIO uploads, and customer profile updates.
"""
import os
import io
import asyncio
import json
from datetime import UTC, datetime

from loguru import logger
from minio import Minio
from arq.connections import RedisSettings
from arq.cron import cron
from sqlalchemy import select

from app.core.config import (
    REDIS_URL, MINIO_ENDPOINT, MINIO_ACCESS_KEY,
    MINIO_SECRET_KEY, MINIO_BUCKET, MINIO_SECURE,
    DATABASE_URL
)
from app.core.database import AsyncSessionLocal
from app.models.call_run import CallRun
from app.models.agent import Agent
from app.models.organization import Organization
from app.models.campaign import Campaign, CampaignContact
from app.models.integration import Integration
from app.services.customer_memory import upsert_customer


# ── MinIO Helpers ─────────────────────────────────────────────────────────────

def upload_file_to_minio(bucket_name: str, object_name: str, data: bytes, content_type: str = "text/plain") -> str:
    """Uploads bytes to MinIO and returns the storage path."""
    try:
        client = Minio(
            MINIO_ENDPOINT,
            access_key=MINIO_ACCESS_KEY,
            secret_key=MINIO_SECRET_KEY,
            secure=MINIO_SECURE
        )
        if not client.bucket_exists(bucket_name):
            client.make_bucket(bucket_name)
        
        client.put_object(
            bucket_name,
            object_name,
            io.BytesIO(data),
            length=len(data),
            content_type=content_type
        )
        return f"{bucket_name}/{object_name}"
    except Exception as e:
        logger.warning(f"MinIO upload failed: {e}. Falling back to local workspace file.")
        # Local fallback
        os.makedirs("workspace_storage", exist_ok=True)
        local_path = os.path.join("workspace_storage", object_name.replace("/", "_"))
        with open(local_path, "wb") as f:
            f.write(data)
        return local_path


def download_file_from_minio(bucket_name: str, object_name: str) -> bytes:
    """Downloads an object from MinIO as bytes, or reads from local fallback."""
    # Check if it was a local fallback path
    if os.path.exists(object_name):
        with open(object_name, "rb") as f:
            return f.read()
            
    try:
        client = Minio(
            MINIO_ENDPOINT,
            access_key=MINIO_ACCESS_KEY,
            secret_key=MINIO_SECRET_KEY,
            secure=MINIO_SECURE
        )
        response = client.get_object(bucket_name, object_name)
        try:
            return response.read()
        finally:
            response.close()
            response.release_conn()
    except Exception as e:
        logger.error(f"MinIO download failed: {e}")
        # Try finding in local fallback as last resort
        local_name = object_name.replace("/", "_")
        fallback_path = os.path.join("workspace_storage", local_name)
        if os.path.exists(fallback_path):
            with open(fallback_path, "rb") as f:
                return f.read()
        raise


# ── ARQ Worker Tasks ─────────────────────────────────────────────────────────

async def process_call_completion(ctx, call_run_id: int):
    """
    ARQ Background Task:
    1. Loads CallRun, checks duration.
    2. Calculates standard/economy/premium pricing.
    3. Deducts credits from Organization balance.
    """
    logger.info(f"ARQ: Processing completion for call_run={call_run_id}")
    
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(CallRun).where(CallRun.id == call_run_id)
        )
        run = result.scalar_one_or_none()
        if not run:
            logger.error(f"ARQ: CallRun {call_run_id} not found")
            return
            
        result = await db.execute(
            select(Agent).where(Agent.id == run.agent_id)
        )
        agent = result.scalar_one_or_none()
        if not agent:
            logger.error(f"ARQ: Agent {run.agent_id} not found for call_run={call_run_id}")
            return

        result = await db.execute(
            select(Organization).where(Organization.id == run.org_id)
        )
        org = result.scalar_one_or_none()
        if not org:
            logger.error(f"ARQ: Organization {run.org_id} not found")
            return

        # Determine pricing per second (USD)
        price_per_second = org.price_per_second_usd
        if price_per_second is None:
            # Default fallback based on cost tier
            cost_tier = agent.model_config.get("cost_tier", "standard")
            if cost_tier == "economy":
                price_per_second = 0.0004  # $0.024/min
            elif cost_tier == "premium":
                price_per_second = 0.0016  # $0.096/min
            else:
                price_per_second = 0.0008  # $0.048/min (Standard)

        duration = run.duration_seconds or 0.0
        total_cost_usd = duration * price_per_second
        
        # 1 USD = 83 credits (INR) conversion
        total_credits = total_cost_usd * 83.0
        
        # Calculate remaining credits to deduct (subtracting what was already deducted in real-time)
        already_deducted = run.credits_used or 0.0
        credits_to_deduct = max(0.0, total_credits - already_deducted)
        
        run.cost_usd = total_cost_usd
        run.credits_used = total_credits
        
        # Deduct from organization balance
        org.balance_credits = max(0.0, org.balance_credits - credits_to_deduct)
        
        db.add(run)
        db.add(org)
        await db.commit()
        
        logger.info(f"ARQ: Deducted {credits_to_deduct:.2f} remaining credits for call={call_run_id} "
                    f"(total={total_credits:.2f}, already_deducted={already_deducted:.2f}). "
                    f"New balance: {org.balance_credits:.2f}")


async def update_customer_profile(ctx, call_run_id: int):
    """
    ARQ Background Task:
    1. Loads CallRun.
    2. Downloads raw transcript from MinIO or local storage.
    3. Runs LLM customer update summaries.
    4. Upserts CustomerProfile (with spam guard).
    """
    logger.info(f"ARQ: Updating customer profile for call_run={call_run_id}")
    
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(CallRun).where(CallRun.id == call_run_id)
        )
        run = result.scalar_one_or_none()
        if not run:
            logger.error(f"ARQ: CallRun {call_run_id} not found")
            return
            
        if not run.caller_number:
            logger.info(f"ARQ: No caller number for call={call_run_id}, skipping customer profile update.")
            return
            
        if not run.transcript_path:
            logger.info(f"ARQ: No transcript path for call={call_run_id}, skipping update.")
            return

        # Fetch transcript text
        try:
            # Check if path starts with bucket name
            path = run.transcript_path
            if path.startswith(f"{MINIO_BUCKET}/"):
                path = path[len(f"{MINIO_BUCKET}/"):]
                
            transcript_bytes = download_file_from_minio(MINIO_BUCKET, path)
            transcript_text = transcript_bytes.decode("utf-8")
        except Exception as e:
            logger.error(f"ARQ: Failed to download transcript from {run.transcript_path}: {e}")
            return
            
        if not transcript_text.strip():
            logger.info(f"ARQ: Transcript is empty for call={call_run_id}, skipping update.")
            return

        # Trigger customer profile upsert (which has internal spam guard logic)
        try:
            await upsert_customer(
                db=db,
                org_id=run.org_id,
                phone_number=run.caller_number,
                duration_seconds=run.duration_seconds or 0.0,
                transcript=transcript_text
            )
            logger.info(f"ARQ: Successfully upserted customer profile for {run.caller_number}")
        except Exception as e:
            logger.error(f"ARQ: Customer upsert failed for call={call_run_id}: {e}")


async def run_post_call_analysis(ctx, call_run_id: int):
    """
    ARQ Background Task:
    1. Loads CallRun.
    2. Downloads raw transcript from MinIO/local storage if available.
    3. Prompts GPT-4o-mini with full transcript to extract:
       - summary (string)
       - sentiment (positive/neutral/negative)
       - disposition (completed/transferred/voicemail/abandoned/no_answer)
       - key_topics (list of strings)
       - task_completed (boolean)
    4. Writes results to CallRun columns.
    """
    logger.info(f"ARQ: Running post-call analysis for call_run={call_run_id}")
    
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(CallRun).where(CallRun.id == call_run_id))
        run = result.scalar_one_or_none()
        if not run:
            logger.error(f"ARQ: CallRun {call_run_id} not found")
            return

        transcript_text = ""
        if run.transcript_path:
            try:
                path = run.transcript_path
                if path.startswith(f"{MINIO_BUCKET}/"):
                    path = path[len(f"{MINIO_BUCKET}/"):]
                transcript_bytes = download_file_from_minio(MINIO_BUCKET, path)
                transcript_text = transcript_bytes.decode("utf-8")
            except Exception as e:
                logger.error(f"ARQ: Failed to download transcript from {run.transcript_path}: {e}")

        # Defaults
        summary = "No conversation occurred."
        sentiment = "neutral"
        disposition = run.disposition or "no_answer"
        key_topics = []
        task_completed = False

        if transcript_text.strip():
            from openai import AsyncOpenAI
            from app.core.config import OPENAI_API_KEY
            if OPENAI_API_KEY and not OPENAI_API_KEY.startswith("mock"):
                try:
                    client = AsyncOpenAI(api_key=OPENAI_API_KEY)
                    system_prompt = (
                        "You are an expert post-call analysis bot. Review the conversation transcript between the voice agent and the customer.\n"
                        "Extract the following fields:\n"
                        "1. summary: A brief 2-line summary of the call.\n"
                        "2. sentiment: Must be one of: 'positive', 'neutral', 'negative'.\n"
                        "3. disposition: Must be one of: 'completed', 'transferred', 'voicemail', 'abandoned', 'no_answer'. Choose the one that best matches the outcome of the conversation.\n"
                        "4. key_topics: A list of key topics discussed (e.g. ['pricing', 'support']).\n"
                        "5. task_completed: A boolean indicating whether the primary goal/task of the call was successfully completed.\n\n"
                        "Return ONLY a raw JSON object with keys: 'summary', 'sentiment', 'disposition', 'key_topics', 'task_completed'. Do not include markdown code block formatting."
                    )
                    response = await client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": f"Transcript:\n{transcript_text}"}
                        ],
                        temperature=0.3,
                        max_tokens=300
                    )
                    content = response.choices[0].message.content or "{}"
                    if content.startswith("```"):
                        lines = content.splitlines()
                        if lines[0].startswith("```json"):
                            content = "\n".join(lines[1:-1])
                        elif lines[0].startswith("```"):
                            content = "\n".join(lines[1:-1])
                    data = json.loads(content)
                    summary = data.get("summary") or "Conversation occurred."
                    sentiment = data.get("sentiment") or "neutral"
                    disposition = data.get("disposition") or disposition
                    key_topics = data.get("key_topics") or []
                    task_completed = data.get("task_completed") or False
                except Exception as e:
                    logger.error(f"ARQ: LLM post-call analysis failed: {e}")
                    summary = "Call completed with transcript."
                    sentiment = "neutral"
            else:
                logger.warning("ARQ: OPENAI_API_KEY is not configured or mock key used. Using mock analysis fallback.")
                summary = "Call completed. Mock analysis generated."
                sentiment = "positive"
                disposition = "completed"
                key_topics = ["general"]
                task_completed = True

        run.summary = summary
        run.sentiment = sentiment
        run.disposition = disposition
        run.key_topics = key_topics
        run.task_completed = task_completed
        db.add(run)
        await db.commit()

        # Trigger outbound webhook events for call.ended and call.transcript
        try:
            from app.services.webhook_dispatcher import dispatch_call_webhook
            # Run these in background tasks so they do not block the ARQ task worker thread
            asyncio.create_task(dispatch_call_webhook(
                db,
                run.id,
                "call.ended",
                payload_extra={
                    "summary": run.summary,
                    "sentiment": run.sentiment,
                    "disposition": run.disposition,
                    "task_completed": run.task_completed,
                    "duration_seconds": run.duration_seconds,
                    "usage_stats": run.usage_stats
                }
            ))

            transcript_payload = transcript_text
            if not transcript_payload and run.gathered_context:
                transcript_payload = run.gathered_context.get("whatsapp_messages") or run.gathered_context.get("transcript")

            asyncio.create_task(dispatch_call_webhook(
                db,
                run.id,
                "call.transcript",
                payload_extra={
                    "transcript": transcript_payload
                }
            ))
            
            # Dispatch to configured third-party CRMs
            from app.services.crm_sync_service import sync_to_hubspot, sync_to_salesforce
            
            integration_result = await db.execute(
                select(Integration).where(
                    Integration.org_id == run.org_id, 
                    Integration.is_connected == True
                )
            )
            integrations = integration_result.scalars().all()
            
            call_data = {
                "call_id": run.id,
                "caller_number": run.caller_number,
                "summary": run.summary,
                "sentiment": run.sentiment,
                "disposition": run.disposition,
                "transcript": transcript_payload
            }
            
            for integration in integrations:
                credentials = integration.credentials or {}
                if integration.service_name == "hubspot":
                    asyncio.create_task(sync_to_hubspot(credentials, call_data))
                elif integration.service_name == "salesforce":
                    asyncio.create_task(sync_to_salesforce(credentials, call_data))
                    
        except Exception as ex:
            logger.error(f"ARQ: Failed to queue webhook event dispatch or CRM sync: {ex}")
        logger.info(f"ARQ: Successfully saved post-call analysis for call={call_run_id}")


async def update_campaign_contact_status(ctx, call_run_id: int, contact_id: int):
    """
    ARQ Background Task:
    1. Loads CampaignContact by contact_id.
    2. Updates status based on call run's disposition:
       - If call was completed/transferred, set contact status to "completed"
       - If call failed or was no_answer/abandoned/voicemail:
         - If contact.attempts < 3, reset status to "pending" for retry
         - Otherwise, set status to "failed"
    """
    logger.info(f"ARQ: Updating campaign contact={contact_id} status using call_run={call_run_id}")
    async with AsyncSessionLocal() as db:
        # Load contact
        result = await db.execute(select(CampaignContact).where(CampaignContact.id == contact_id))
        contact = result.scalar_one_or_none()
        if not contact:
            logger.error(f"ARQ: CampaignContact {contact_id} not found")
            return

        # Load call run
        run_res = await db.execute(select(CallRun).where(CallRun.id == call_run_id))
        run = run_res.scalar_one_or_none()
        
        disposition = run.disposition if run else "failed"
        
        # Determine contact status
        if disposition in ("completed", "transferred"):
            contact.status = "completed"
        else:  # voicemail, abandoned, no_answer, failed
            if contact.attempts < 3:
                contact.status = "pending"
            else:
                contact.status = "failed"
                
        db.add(contact)
        await db.commit()
        logger.info(f"ARQ: Contact {contact_id} status updated to '{contact.status}' (attempts={contact.attempts})")


async def dial_next_contacts(ctx, campaign_id: int):
    """
    ARQ Background Task:
    1. Loads Campaign, verifies status == "running".
    2. Fetches next batch of pending contacts.
    3. Triggers Telnyx out-dial for each contact in parallel.
    4. Automatically schedules the next batch processing step.
    """
    logger.info(f"ARQ: Processing dialer queue for campaign={campaign_id}")
    
    async with AsyncSessionLocal() as db:
        async with db.begin():
            result = await db.execute(
                select(Campaign).where(Campaign.id == campaign_id)
            )
            campaign = result.scalar_one_or_none()
            if not campaign or campaign.status != "running":
                logger.info(f"ARQ: Campaign={campaign_id} is not active (status={campaign.status if campaign else 'none'})")
                return

            # Check active concurrent calls for this campaign
            active_select = (
                select(CampaignContact)
                .where(CampaignContact.campaign_id == campaign_id, CampaignContact.status == "in_progress")
            )
            active_result = await db.execute(active_select)
            active_calls = active_result.scalars().all()
            
            MAX_CONCURRENT_CALLS = 5
            available_slots = MAX_CONCURRENT_CALLS - len(active_calls)
            
            if available_slots <= 0:
                logger.info(f"ARQ: Campaign={campaign_id} is at maximum concurrency ({len(active_calls)}/{MAX_CONCURRENT_CALLS} active). Deferring next check.")
                defer_check = True
                contacts = []
            else:
                defer_check = False
                batch_size = min(3, available_slots)

                # Fetch up to `batch_size` pending contacts with SKIP LOCKED row-level lock
                contacts_select = (
                    select(CampaignContact)
                    .where(CampaignContact.campaign_id == campaign_id, CampaignContact.status == "pending")
                    .limit(batch_size)
                    .with_for_update(skip_locked=True)
                )
                contacts_result = await db.execute(contacts_select)
                contacts = contacts_result.scalars().all()

                if not contacts:
                    # Check if there are any remaining in-progress contacts
                    check_running = await db.execute(
                        select(CampaignContact)
                        .where(CampaignContact.campaign_id == campaign_id, CampaignContact.status == "in_progress")
                    )
                    if not check_running.scalars().all():
                        campaign.status = "completed"
                        logger.info(f"ARQ: Campaign={campaign_id} completed (all numbers dialed)")
                    return

                # Mark them as in_progress immediately
                for contact in contacts:
                    contact.status = "in_progress"
                    contact.attempts += 1
                    contact.last_attempt_at = datetime.now(UTC)
                    db.add(contact)

        if defer_check:
            redis_pool = ctx.get("redis")
            if redis_pool:
                await redis_pool.enqueue_job("dial_next_contacts", campaign_id, _defer_by=5)
            return

        if contacts:
            # Run dial outs
            from app.services.dialer_service import dial_number
            for contact in contacts:
                success = await dial_number(db, contact.id)
                if not success:
                    # If initiation fails, mark it failed immediately
                    async with AsyncSessionLocal() as session:
                        contact_result = await session.execute(
                            select(CampaignContact).where(CampaignContact.id == contact.id)
                        )
                        c = contact_result.scalar_one_or_none()
                        if c:
                            c.status = "failed"
                            await session.commit()

            # Defer next batch loop check in 5 seconds
            redis_pool = ctx.get("redis")
            if redis_pool:
                await redis_pool.enqueue_job("dial_next_contacts", campaign_id, _defer_by=5)


async def perform_daily_db_backup(ctx):
    """
    ARQ Cron Job:
    1. Runs pg_dump using the DATABASE_URL.
    2. Uploads the compressed dump to MinIO.
    """
    logger.info("ARQ: Starting daily database backup...")
    try:
        # Resolve DB string for pg_dump (replacing asyncpg with standard postgresql)
        db_url = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
        
        # We'll use custom format (-Fc) which is compressed by default
        process = await asyncio.create_subprocess_exec(
            "pg_dump", "-Fc", db_url,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            logger.error(f"ARQ: pg_dump failed: {stderr.decode()}")
            return
            
        logger.info(f"ARQ: pg_dump completed successfully. Output size: {len(stdout)} bytes.")
        
        date_str = datetime.now(UTC).strftime("%Y-%m-%d_%H-%M-%S")
        object_name = f"backups/auris_db_backup_{date_str}.dump"
        
        # Upload directly to MinIO
        path = upload_file_to_minio(MINIO_BUCKET, object_name, stdout, content_type="application/octet-stream")
        logger.info(f"ARQ: Successfully uploaded backup to {path}")
        
    except Exception as e:
        logger.error(f"ARQ: Failed to perform daily database backup: {e}")

# ── ARQ Settings ─────────────────────────────────────────────────────────────

# Parse Redis Settings
try:
    import urllib.parse
    url = urllib.parse.urlparse(REDIS_URL)
    arq_redis_settings = RedisSettings(
        host=url.hostname or "localhost",
        port=url.port or 6379,
        database=int(url.path.lstrip("/")) if url.path else 0,
        password=url.password
    )
except Exception as ex:
    logger.warning(f"Failed to parse REDIS_URL, using default: {ex}")
    arq_redis_settings = RedisSettings()

class WorkerSettings:
    functions = [
        process_call_completion, 
        update_customer_profile, 
        dial_next_contacts,
        run_post_call_analysis,
        update_campaign_contact_status
    ]
    cron_jobs = [
        cron(perform_daily_db_backup, hour={0}, minute=0)
    ]
    redis_settings = arq_redis_settings

