import asyncio
import httpx
import logging
from typing import List

logger = logging.getLogger("agent_utils")

async def register_with_registry(registry_url: str, agent_data: dict, ttl: int):
    """
    Registers the agent with the registry and sends heartbeats.
    """
    while True:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(f"{registry_url}/register", json=agent_data)
                if response.status_code == 200:
                    logger.info(f"Heartbeat sent to {registry_url}")
                else:
                    logger.error(f"Failed to register: {response.status_code} - {response.text}")
        except Exception as e:
            logger.error(f"Error connecting to registry: {e}")
        
        # Sleep for a portion of the TTL to ensure we re-register before expiration
        await asyncio.sleep(ttl * 0.8)
