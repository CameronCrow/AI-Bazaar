# llm_economist/agents/conversation_agent.py
import logging
import time
from typing import Optional, Callable
from .llm_agent import LLMAgent
from ..utils.thread_manager import ThreadManager, ThreadState
from .worker import Worker, GEN_ROLE_MESSAGES

class ConversationAgent(LLMAgent):
    def __init__(self, worker_agent: Worker, conversation_log_file: str, args=None):
        # Copy the worker's LLM configuration
        super().__init__(
            llm_type=worker_agent.llm.model_name if worker_agent.llm else 'None',
            port=0,  # Not needed for conversation
            name=f"{worker_agent.name}_conversation",
            prompt_algo=worker_agent.prompt_algo,
            history_len=worker_agent.history_len,
            timeout=worker_agent.timeout,
            args=args
        )
        
        # Copy the worker's persona and characteristics
        self.original_worker = worker_agent
        self.role = worker_agent.role
        self.utility_type = worker_agent.utility_type
        self.v = worker_agent.v  # skill level
        self.scenario = worker_agent.scenario
        
        # Conversation-specific attributes
        self.conversation_log_file = conversation_log_file
        self.conversation_history = []
        self.is_active = False
        
        # Set up conversation system prompt
        self.base_persona = ""
        self._setup_conversation_prompt()
        
        # Initialize conversation logging
        self._init_conversation_log()
        
        self._send_conversation_prompt()
        
        
    
    def _setup_conversation_prompt(self):
        """Set up the system prompt for conversation mode."""
        if self.role != 'default':
            from .worker import GEN_ROLE_MESSAGES
            self.base_persona = base_persona = GEN_ROLE_MESSAGES.get(self.role, "")
        
        self.system_prompt = ""
        # Get historical messages
        historical_messages = self.get_historical_messages()
        self.system_prompt += historical_messages
        self.system_prompt += "\n\nYou are now in a conversation with a researcher. Respond naturally, based on your economic situation, beliefs, and experiences. You can discuss your economic situation, tax preferences, work habits, and opinions."
        
    
    def get_historical_messages(self) -> str:
        """Get historical messages."""
        return self.worker_agent.get_historical_messages()
    
    def _init_conversation_log(self):
        """Initialize the conversation log file."""
        with open(self.conversation_log_file, 'w') as f:
            f.write(f"=== Conversation Log for {self.name} ===\n")
            f.write(f"Started: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Original Worker: {self.original_worker.name}\n")
            f.write(f"Role: {self.role}\n")
            f.write(f"Utility Type: {self.utility_type}\n")
            f.write("=" * 50 + "\n\n")
            f.write()
    
    def send_message(self, message: str, message_type: str) -> str:
        """Send a message to the agent and get a response."""
        # Log user message
        self._log_message("USER" if not message_type else message_type, message)
        
        # Get response from LLM
        try:
            response, _ = self.llm.send_msg(
                system_prompt=self.system_prompt,
                user_prompt=message,
                temperature=0.8,  # Slightly higher for more natural conversation
                json_format=False
            )
            
            # Log agent response
            self._log_message("AGENT", response)
            
            # Add to conversation history
            self.conversation_history.append({
                'user': message,
                'agent': response,
                'timestamp': time.time()
            })
            
            return response
            
        except Exception as e:
            error_msg = f"Error generating response: {str(e)}"
            self._log_message("ERROR", error_msg)
            return f"{self.name} failed to respond."
    
    def _log_message(self, sender: str, message: str):
        """Log a message to the conversation file."""
        timestamp = time.strftime('%H:%M:%S')
        with open(self.conversation_log_file, 'a') as f:
            f.write(f"[{timestamp}] {sender}: {message}\n\n")
            
    def _send_conversation_prompt(self):
        """Send the conversation prompt to the agent."""
        self.send_message(self.system_prompt, "CONVERSATION_PROMPT")