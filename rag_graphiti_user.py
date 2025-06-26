from datetime import datetime, timezone
from logger import logger

from graphiti_core.search.search_config_recipes import NODE_HYBRID_SEARCH_RRF  
from graphiti_core.nodes import EpisodeType

from rag_graphiti_client import client

async def query_user(user_name: str) -> str:
    nl = None
    try:
        nl = await client._search(user_name, NODE_HYBRID_SEARCH_RRF)
    except Exception as e:
        logger.exception(f'Error searching graphiti: {e}')
    if nl != None and len(nl.nodes) > 0:
        return nl.nodes[0].uuid
    else:
        return None

async def create_user(user_name: str) -> str:
    user_name = 'tcq'
    user_node_uuid = await query_user(user_name)
    if user_node_uuid == None:
        # let's get Jess's node uuid
        await client.add_episode(
            name='User Creation',
            episode_body=(f'{user_name} is interested in query table column relationships'),
            source=EpisodeType.text,
            reference_time=datetime.now(timezone.utc),
            source_description='TableColumnQueryBot',
        ) # wait for the node to be created
        nl = await client._search(user_name, NODE_HYBRID_SEARCH_RRF)
        user_node_uuid = nl.nodes[0].uuid
    logger.info(f'User node uuid: {user_node_uuid}')  
    return user_node_uuid