# llm_economist/utils/conversation_thread.py
import threading
import time
import logging
from typing import Optional, List
from .thread_manager import ThreadManager, ThreadState
from .input_interface import InputInterface, TkinterInputInterface
from ..agents.conversation_agent import ConversationAgent
from ..agents.worker import Worker

class ConversationThread:
    """Handles Thread B - Agent Conversations."""
    
    def __init__(self, thread_manager: ThreadManager, input_interface: InputInterface, args=None):
        self.thread_manager = thread_manager
        self.input_interface = input_interface
        self.args = args
        self.logger = logging.getLogger('main')
        
        # Conversation state
        self.conversation_agent: Optional[ConversationAgent] = None
        self.available_workers: List[Worker] = []
        self.is_running = False
        
        # Thread management
        self.thread = None
        self.stop_event = threading.Event()
    
    def set_available_workers(self, workers: List[Worker]):
        """Set the list of available workers to choose from."""
        self.available_workers = workers
    
    def start_conversation_thread(self):
        """Start the conversation thread."""
        if self.thread and self.thread.is_alive():
            self.logger.warning("Conversation thread already running")
            return
        
        self.thread = threading.Thread(target=self._run_conversation_loop, daemon=False)
        self.thread.start()
        self.logger.info("Conversation thread started")
        self.logger.info(f"Thread manager states - A: {self.thread_manager.thread_a_state}, B: {self.thread_manager.thread_b_state}")
    
    def stop_conversation_thread(self):
        """Stop the conversation thread."""
        self.stop_event.set()
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=5)
        self.logger.info("Conversation thread stopped")
    
    def _run_conversation_loop(self):
        """Main conversation loop."""
        self.logger.info("Starting conversation loop")
        
        while not self.stop_event.is_set():
            try:
                # Check if Thread A is paused (show worker selection)
                if self.thread_manager.thread_a_state == ThreadState.PAUSED:
                    if not hasattr(self, '_worker_selection_shown') or not self._worker_selection_shown:
                        self._show_worker_selection()
                        self._worker_selection_shown = True
                else:
                    # Hide worker selection when Thread A is not paused
                    if hasattr(self, '_worker_selection_shown') and self._worker_selection_shown:
                        self._hide_worker_selection()
                        self._worker_selection_shown = False
                
                # Check if Thread B should be running
                if self.thread_manager.thread_b_state == ThreadState.RUNNING:
                    if not self.is_running:
                        self._start_conversation()
                    self._handle_conversation()
                elif self.thread_manager.thread_b_state == ThreadState.PAUSED:
                    if self.is_running:
                        self._pause_conversation()
                elif self.thread_manager.thread_b_state == ThreadState.STOPPED:
                    if self.is_running:
                        self._stop_conversation()
                
                time.sleep(0.1)  # Small delay to prevent busy waiting
                
            except Exception as e:
                self.logger.error(f"Error in conversation loop: {e}")
                time.sleep(1)
        
        self._cleanup()
    
    def _start_conversation(self):
        """Start a new conversation session."""
        self.logger.info(f"Starting conversation. Available workers: {len(self.available_workers) if self.available_workers else 0}")
        
        if not self.available_workers:
            self.logger.warning("No workers available for conversation")
            return
        
        # Let user select a worker
        selected_worker = self._select_worker()
        if not selected_worker:
            self.logger.warning("No worker selected for conversation")
            return
        
        self.logger.info(f"Selected worker: {selected_worker.name}")
        
        # Create conversation agent
        try:
            log_file = f"logs/conversation_{selected_worker.name}_{int(time.time())}.log"
            self.conversation_agent = ConversationAgent(selected_worker, log_file, self.args)
            self.logger.info(f"Created conversation agent for {selected_worker.name}")
        except Exception as e:
            self.logger.error(f"Failed to create conversation agent: {e}")
            return
        
        # Show conversation interface
        if hasattr(self.input_interface, 'show_conversation_interface'):
            self.input_interface.show_conversation_interface()
        
        self.is_running = True
        self.logger.info(f"Started conversation with {selected_worker.name}")
        
        # Send welcome message
        welcome_msg = f"Hello! I'm {selected_worker.name}. I'm a {selected_worker.role} with skill level {selected_worker.v}. How can I help you today?"
        if hasattr(self.input_interface, 'add_message'):
            self.input_interface.add_message("AGENT", welcome_msg)
    
    def _show_worker_selection(self):
        """Show worker selection interface."""
        if not self.available_workers:
            self.logger.warning("No workers available for selection")
            return
        
        if hasattr(self.input_interface, 'show_worker_selection'):
            self.input_interface.show_worker_selection(self.available_workers, self._on_worker_selected)
        else:
            self.logger.warning("Input interface does not support worker selection")
    
    def _hide_worker_selection(self):
        """Hide worker selection interface."""
        if hasattr(self.input_interface, 'hide_worker_selection'):
            self.input_interface.hide_worker_selection()
    
    def _on_worker_selected(self, selected_worker: Worker):
        """Callback when a worker is selected."""
        self.logger.info(f"Worker selected: {selected_worker.name}")
        # Store the selected worker for when Thread B starts
        self.selected_worker = selected_worker
    
    def _select_worker(self) -> Optional[Worker]:
        """Get the selected worker for conversation."""
        if hasattr(self, 'selected_worker') and self.selected_worker:
            return self.selected_worker
        
        # Fallback to first worker if none selected
        if self.available_workers:
            return self.available_workers[0]
        
        return None
    
    def _handle_conversation(self):
        """Handle ongoing conversation."""
        if not self.conversation_agent or not self.is_running:
            return
        
        # Check for user input
        if self.input_interface.is_available():
            user_input = self.input_interface.get_input()
            self.input_interface.add_message("USER", user_input)
            if user_input:
                # Get response from agent
                response = self.conversation_agent.send_message(user_input)
                
                # Display response
                if hasattr(self.input_interface, 'add_message'):
                    self.input_interface.add_message("AGENT", response)
    
    def _pause_conversation(self):
        """Pause the conversation."""
        if hasattr(self.input_interface, 'hide_conversation_interface'):
            self.input_interface.hide_conversation_interface()
        self.logger.info("Conversation paused")
    
    def _stop_conversation(self):
        """Stop the conversation."""
        if self.conversation_agent:
            self.conversation_agent = None
        
        if hasattr(self.input_interface, 'hide_conversation_interface'):
            self.input_interface.hide_conversation_interface()
        
        self.is_running = False
        self.logger.info("Conversation stopped")
    
    def _cleanup(self):
        """Clean up resources."""
        self._stop_conversation()
        if self.input_interface:
            self.input_interface.cleanup()