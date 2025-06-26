from pydantic import BaseModel, Field

class Entities(BaseModel):
    """Identifying information about entities."""

    table_names: list[str] = Field(
        ...,
        description="All the table names that appear in the text.",
    )
    
from langchain_core.prompts import ChatPromptTemplate
entity_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are extracting reference table names from the text. output field name: table_names",
        ),
        (
            "human",
            "Use the given format to extract information from the following "
            "input: {question}",
        ),
    ]
)

from neo4j import Driver
from langchain_openai import ChatOpenAI  
import os
from logger import logger
class TableIndex:
    def __init__(self, driver: Driver, llm: ChatOpenAI):
        self.driver = driver
        self.llm = llm
        self.entity_chain = entity_prompt | self.llm.with_structured_output(Entities)
        self.database = os.environ["DEFAULT_DATABASE"]
    
    async def _create_fulltext_index(self, tx):
        query = '''
        CREATE FULLTEXT INDEX `fulltext_entity_id` IF NOT EXISTS 
        FOR (n:Table) 
        ON EACH [n.name, n.table_comment]
        OPTIONS {
            indexConfig: {
                `fulltext.eventually_consistent`: false
            }
        };
        '''
        await tx.run(query)
        
    async def _drop_old_index(self, tx):
        query = '''
        DROP INDEX `fulltext_entity_id`;
        '''
        await tx.run(query)
        
    async def refresh_index(self):
        # Call the function to drop_old_index_and_embeding
        try:
            async with self.driver.session(database=self.database) as session:
                await session.execute_write(self._drop_old_index)
                logger.info("drop_old_index successfully.")
        except Exception as e:
            logger.error("Error drop_old_index {e}")
            pass

        # Call the function to create the index
        try:
            async with self.driver.session(database=self.database) as session:
                await session.execute_write(self._create_fulltext_index)
                logger.info("Fulltext index created successfully.")
        except Exception as e:
            logger.error(f"Error creating fulltext index: {e}")
            pass
        
    async def _index_search(self, tx, index_query):
        query = """CALL db.index.fulltext.queryNodes('fulltext_entity_id', $index_query, {limit:2})
                YIELD node,score
                RETURN node.name as name LIMIT 2
                """
        table_names = []
        result = await tx.run(query, index_query=index_query)
        async for el in result:
            table_names.append(el['name'])
        return table_names
    
    async def search_table_names(self, query: str) -> list[str]:
        entities = self.entity_chain.invoke(query)
        results = []
        for entity in entities.table_names:
            table_name_splits = entity.split(".")
            query = ' AND '.join(list(map(lambda table_name_split : table_name_split.strip(), table_name_splits)))
            async with self.driver.session(database=self.database) as session:
                result = await session.execute_read(self._index_search, query)
                results += result
        logger.info(f"results: {results}")
        return results