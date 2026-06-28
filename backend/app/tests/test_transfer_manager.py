import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.transfer_manager import warm_transfer
from app.models.call_run import CallRun
from app.models.agent import Agent

@pytest.mark.asyncio
@patch("app.services.transfer_manager.AsyncSessionLocal")
async def test_warm_transfer_call_not_found(mock_session_local):
    mock_db = AsyncMock()
    
    # Mock execute returning a synchronous result mock that returns None
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute = AsyncMock(return_value=mock_result)
    
    mock_session_local.return_value.__aenter__.return_value = mock_db

    result = await warm_transfer(1, 2)
    assert result is False


@pytest.mark.asyncio
@patch("app.services.transfer_manager.AsyncSessionLocal")
async def test_warm_transfer_success(mock_session_local):
    mock_db = AsyncMock()
    
    mock_call = MagicMock(spec=CallRun)
    mock_call.id = 1
    mock_call.recording_path = None
    
    mock_agent = MagicMock(spec=Agent)
    mock_agent.id = 2
    mock_agent.phone_number = "+1234567890"

    # Set up mock result objects for the successive execute queries
    mock_call_result = MagicMock()
    mock_call_result.scalar_one_or_none.return_value = mock_call
    
    mock_agent_result = MagicMock()
    mock_agent_result.scalar_one_or_none.return_value = mock_agent
    
    mock_db.execute = AsyncMock()
    mock_db.execute.side_effect = [mock_call_result, mock_agent_result]
    mock_session_local.return_value.__aenter__.return_value = mock_db

    result = await warm_transfer(1, 2)
    
    assert result is True
    assert mock_call.recording_path.startswith("conf-")
    mock_db.commit.assert_called_once()
