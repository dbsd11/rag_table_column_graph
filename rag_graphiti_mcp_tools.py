from rag_graphiti_client import client, llm
from rag_graphiti_table_index import TableIndex
tableIndex = TableIndex(client.driver, llm)

from logger import logger

from graphiti_core.search.search_config_recipes import EDGE_HYBRID_SEARCH_RRF  
import copy
table_column_search_config = copy.deepcopy(EDGE_HYBRID_SEARCH_RRF)
table_column_search_config.limit = 200
table_column_search_config.reranker_min_score = 0.1

from langchain_core.tools import tool
@tool
async def get_table_columns(query: str) -> str:
    """Search the graphiti graph for table columns"""
    
    table_names = await get_table_names(query)
    if len(table_names) == 0:
        return ""
    
    try:
        edge_results = []
        for table_name in table_names:
            query = f"{table_name} has column"
            search_results = await client.search_(
                query,
                config = table_column_search_config,
                center_node_uuid=None,
            )
            edge_results += search_results.edges
        from rag_graphiti_chatbot import edges_to_facts_string
        return edges_to_facts_string(edge_results)
    except Exception as e:
        logger.exception(f"search error {e}")
        return ""

async def get_table_names(query: str) -> list[str]:
    """Search the graphiti graph for table names"""
    try:
        search_results = await tableIndex.search_table_names(query)
        return search_results
    except Exception as e:
        logger.exception(f"search error {e}")
        return []