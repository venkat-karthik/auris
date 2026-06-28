"""
Auris - ARQ Background Task Worker
Handles post-call processing, credit deduction, MinIO uploads, and customer profile updates.
"""
import os
import io
import asyncio
from datetime import UTC, datetime
from loguru import logger
from minio import Minio
from arq.connections import RedisSettings
from sqlalchemy import select

from app.core.config import (
    REDIS_URL, MINIO_ENDPOINT, MINIO_ACCESS_KEY,
    MINIO_SECRET_KEY, MINIO_BUCKET, MINIO_SECURE,
)
from app.core.database import AsyncSessionLocal
from app.models.call_run import CallRun
from app.models.agent import Agent
from app.models.organization import Organization
from app.models.campaign import Campaign, CampaignContact
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
            redis_pool = ctx.get("redis")
            if redis_pool:
                await redis_pool.enqueue_job("dial_next_contacts", campaign_id, _defer_by=5)
            return

        batch_size = min(3, available_slots)

        # Fetch up to `batch_size` pending contacts to call in this batch
        contacts_select = (
            select(CampaignContact)
            .where(CampaignContact.campaign_id == campaign_id, CampaignContact.status == "pending")
            .limit(batch_size)
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
                await db.commit()
                logger.info(f"ARQ: Campaign={campaign_id} completed (all numbers dialed)")
            return

        # Mark them as in_progress immediately to avoid double dialing
        for contact in contacts:
            contact.status = "in_progress"
            contact.attempts += 1
            contact.last_attempt_at = datetime.now(UTC)
            db.add(contact)
        await db.commit()

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
    functions = [process_call_completion, update_customer_profile, dial_next_contacts]
    redis_settings = arq_redis_settings
