from datetime import datetime, timezone
import asyncio
from logger import logger

from graphiti_core import Graphiti

from graphiti_core.utils.maintenance.node_operations import (
    extract_attributes_from_nodes,
    extract_nodes,
)
from graphiti_core.utils.maintenance.edge_operations import (
    build_episodic_edges,
    resolve_extracted_edges,
)
from graphiti_core.utils.bulk_utils import (
    add_nodes_and_edges_bulk,
)
from graphiti_core.nodes import EpisodeType, EpisodicNode, EntityNode
from graphiti_core.edges import EntityEdge
async def add_table_column_nodes (
        client: Graphiti,
        center_node_uuid: str,
        schema_name: str,
        table_name: str,
        table_comment: str,
        columns: list,        
    ):
        start = datetime.now(timezone.utc)
        now = datetime.now(timezone.utc)
        
        previous_episodes = []

        episode:EpisodicNode = await EpisodicNode.get_by_uuid(client.driver, center_node_uuid)

        # Extract entities as nodes
        extracted_nodes = []
        for column in columns:
            extracted_nodes.append(EntityNode(
                name = schema_name + "." + table_name + "." + column["column_name"],
                group_id = episode.group_id,
                labels = ["Column"],
                created_at = now,
                attributes = {
                    "schema_name": schema_name,
                    "table_name": table_name,
                    "column_name": column["column_name"],
                    "column_comment": column["column_comment"],
                    "data_type": column["data_type"],
                }
            ))
        
        table_node = EntityNode(
            name = schema_name + "." + table_name,
            group_id = episode.group_id,
            labels = ["Table"],
            created_at = now,
            attributes = {
                "schema_name": schema_name,
                "table_name": table_name,
                "table_comment": table_comment,
            }
        )
        
        nodes = [table_node] + extracted_nodes
        
        episodic_edges = build_episodic_edges([table_node], episode, now)
        
        edges = []
        for extracted_node in extracted_nodes:
            edges.append(EntityEdge(
                name = "has_column",
                fact = table_node.name + " has column " + extracted_node.name,
                source_node_uuid = table_node.uuid,
                target_node_uuid = extracted_node.uuid,
                group_id = extracted_node.group_id,
                created_at = extracted_node.created_at
            ))
                
        (resolved_edges, invalidated_edges) = await resolve_extracted_edges(
                client.clients,
                edges,
                episode,
                nodes,
                {},
                ({('Entity', 'Entity'): []}),
            )
        entity_edges = resolved_edges
        
        hydrated_nodes = await extract_attributes_from_nodes(
            client.clients, nodes, episode, previous_episodes, None
        )

        await add_nodes_and_edges_bulk(
            client.driver, [episode], episodic_edges, hydrated_nodes, entity_edges, client.embedder
        )

        end = datetime.now(timezone.utc)
        logger.info(f'Completed add_episode in {(end - start) * 1000} ms')

async def ingest_table_column_graph_data(client: Graphiti, center_node_uuid: str):
    from pathlib import Path
    script_dir = Path.cwd()
    
    table_structures_dir = script_dir / 'table_structures'
    csv_files = list(table_structures_dir.glob('*.csv'))

    for csv_file in csv_files:
        with open(csv_file, 'r', encoding='utf-8') as file:
            # 跳过标题行
            next(file)
            # 读取所有行
            rows = [line.strip().split(',') for line in file]
        
            # 为每个表创建一个episode
            if rows:
                schema_name = rows[0][0]  # SCHEMA_NAME在第一列
                table_name = rows[0][1]  # TABLE_NAME在第二列
                table_comment = rows[0][2]  # TABLE_COMMENT在第三列
                
                # 构建表结构信息
                columns = [{
                    'column_name': row[3],  # COLUMN_NAME
                    'column_comment': row[4],  # COLUMN_COMMENT
                    'data_type': row[5]  # DATA_TYPE
                } for row in rows]
                
                await add_table_column_nodes(
                    client = client,
                    center_node_uuid = center_node_uuid,
                    schema_name = schema_name,
                    table_name = table_name,
                    table_comment = table_comment,
                    columns = columns,
                )

async def run():
    # clear database
    from graphiti_core.utils.maintenance.graph_data_operations import clear_data
    from rag_graphiti_client import client, llm 
    await clear_data(client.driver)
    
    # create user
    from rag_graphiti_user import create_user
    await create_user("tcq")
    
    # create table index
    from rag_graphiti_table_index import TableIndex
    tableIndex = TableIndex(client.driver, llm)
    await tableIndex.refresh_index()
    
    # create total node edge index
    await client.build_indices_and_constraints()
    
    # ingest graph data
    from graphiti_core.search.search_config import SearchConfig,EpisodeSearchConfig,EpisodeSearchMethod,EpisodeReranker
    episode_search_result = await client.search_('Table Column Relationships', config = SearchConfig(
        episode_config=EpisodeSearchConfig(
            search_methods=[
                EpisodeSearchMethod.bm25,
            ],
            reranker=EpisodeReranker.rrf,
        )
    ))
    if episode_search_result.episodes == None or len(episode_search_result.episodes) == 0 or episode_search_result.episodes[0].name != 'Table Column Relationships':
        add_result = await client.add_episode(
            name='Table Column Relationships',
            episode_body='table column relationships',
            source=EpisodeType.text,
            source_description='TableColumnRelationships',
            reference_time=datetime.now(timezone.utc),
        )
        center_node_uuid = add_result.episode.uuid
    else:
        center_node_uuid = episode_search_result.episodes[0].uuid
    await ingest_table_column_graph_data(client, center_node_uuid)

if __name__ == "__main__":     
    asyncio.run(run())
