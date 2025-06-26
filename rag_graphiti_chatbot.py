import asyncio
from typing_extensions import TypedDict
from typing import Annotated
from langgraph.graph import add_messages
from langchain_core.messages import AIMessage, SystemMessage
from graphiti_core import Graphiti
from graphiti_core.edges import EntityEdge
from graphiti_core.nodes import EpisodeType
from graphiti_core.llm_client import OpenAIClient
from datetime import datetime, timezone

def edges_to_facts_string(entities: list[EntityEdge]):
    return '-' + '\n- '.join([edge.fact for edge in entities])

class State(TypedDict):
    messages: Annotated[list, add_messages]
    user_name: str
    user_node_uuid: str
    
class Chatbot:
    def __init__(self, llm: OpenAIClient, graphiti: Graphiti):
        self.llm = llm
        self.graphiti = graphiti
    
    async def generate_chatbot_response(self, state: State):
        facts_string = None
        if len(state['messages']) > 0:
            last_message = state['messages'][-1]
            graphiti_query = f'{"TableColumnQueryBot" if isinstance(last_message, AIMessage) else state["user_name"]}: {last_message.content}'
            # search graphiti using Jess's node uuid as the center node
            # graph edges (facts) further from the Jess node will be ranked lower
            edge_results = await asyncio.create_task(self.graphiti.search(
                graphiti_query, center_node_uuid=state['user_node_uuid'], num_results=5
            ))
            facts_string = edges_to_facts_string(edge_results)

        system_message = SystemMessage(
            content=f"""You are a skillfull table column relationship manager. Review information about the user and their prior conversation below and respond accordingly.
            Keep responses short and concise. And remember, always be helpful!

            Things you'll need to know about the user in order to generate a helpful response:
            - need query table

            Ensure that you ask the user for the above if you don't already know.
            
            Facts about the user and their conversation:
            {facts_string or 'No facts about the user and their conversation'}"""
        )

        messages = [system_message] + state['messages']

        response = await asyncio.create_task(self.llm.ainvoke(messages))

        # add the response to the graphiti graph.
        # this will allow us to use the graphiti search later in the conversation
        # we're doing async here to avoid blocking the graph execution
        asyncio.create_task(
            self.graphiti.add_episode(
                name='Chatbot Response',
                episode_body=f'{state["user_name"]}: {state["messages"][-1]}\nTableColumnQueryBot: {response.content}',
                source=EpisodeType.message,
                reference_time=datetime.now(timezone.utc),
                source_description='Chatbot',
            )
        )

        return {'messages': [response]}