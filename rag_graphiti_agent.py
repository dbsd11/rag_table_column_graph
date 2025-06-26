from langchain_core.messages import AIMessage
from langgraph.graph.state import CompiledStateGraph
from rag_graphiti_chatbot import State
import uuid
from logger import logger

class SystemMessageOutput:
    
    def __init__(self):
        from queue import Queue
        self.message_output_queue = Queue(maxsize=1000)
    
    def append_stdout(self, message: str):
        try:
            self.message_output_queue.put(message, block=True, timeout=10)
        except Exception as e:
            logger.debug('put message queue failed {e}')

    def get_stdout(self, block: bool = True, timeout: int = 10):
        try:
            return self.message_output_queue.get(block=block, timeout=timeout)
        except Exception as e:
            logger.debug('get message queue failed {e}')
            return None

class Agent:
    def __init__(self, graph: CompiledStateGraph):
        self.graph = graph

    def run(self, user_state: State, system_message_output:SystemMessageOutput | None = None):
        return AgentRun({'configurable': {'thread_id': uuid.uuid4().hex}}, user_state, self, system_message_output)

class AgentRun:
    def __init__(self, config, user_state: State, agent: Agent, system_message_output:SystemMessageOutput | None = None):
        self.config = config
        self.user_state = user_state
        self.agent = agent
        if system_message_output != None:
            self.system_message_output = system_message_output
        else:
            self.system_message_output = SystemMessageOutput()
            
        self.system_message_output.append_stdout('Asssistant: Hello, how can I help you about table colume schema and relationships?')
            
    async def process_user_message(self, user_message: str):
        graph_state = {
            'messages': [{'role': 'user', 'content': user_message}],
            'user_name': self.user_state["user_name"],
            'user_node_uuid': self.user_state["user_node_uuid"],
        }

        try:
            async for event in self.agent.graph.astream(
                graph_state,
                config=self.config,
            ):
                for value in event.values():
                    if 'messages' in value:
                        last_message = value['messages'][-1]
                        if isinstance(last_message, AIMessage) and isinstance(
                            last_message.content, str
                        ):
                            self.system_message_output.append_stdout(last_message.content)
        except Exception as e:
            self.system_message_output.append_stdout(f'Error: {e}')