#!/usr/bin/env python3
"""
Simple test script to debug conversation thread issues.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from llm_economist.utils.thread_manager import ThreadManager, ThreadState
from llm_economist.utils.input_interface import TkinterInputInterface
from llm_economist.utils.conversation_thread import ConversationThread
from llm_economist.agents.worker import Worker
import time
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_conversation_thread():
    """Test the conversation thread functionality."""
    print("Testing conversation thread...")
    
    # Create thread manager
    thread_manager = ThreadManager()
    
    # Create input interface
    input_interface = TkinterInputInterface()
    
    # Create mock args
    class MockArgs:
        def __init__(self):
            self.llm = 'gpt-3.5-turbo'
            self.port = 8000
            self.prompt_algo = 'io'
            self.history_len = 10
            self.timeout = 10
            self.bracket_setting = 'three'
            self.service = 'openai'
    
    args = MockArgs()
    
    # Create conversation thread
    conversation_thread = ConversationThread(thread_manager, input_interface, args)
    
    # Create mock workers
    workers = []
    for i in range(3):
        worker = Worker(
            llm=args.llm,
            port=args.port,
            name=f"worker_{i}",
            utility_type='egotistical',
            scenario='rational',
            num_agents=3,
            args=args
        )
        workers.append(worker)
    
    # Set available workers
    conversation_thread.set_available_workers(workers)
    print(f"Set {len(workers)} workers")
    
    # Start conversation thread
    conversation_thread.start_conversation_thread()
    print("Started conversation thread")
    
    # Test Thread A pause (should show worker selection)
    print("Pausing Thread A...")
    thread_manager.pause_thread_a()
    time.sleep(2)
    
    # Test Thread B start (should start conversation)
    print("Starting Thread B...")
    thread_manager.start_thread_b()
    time.sleep(2)
    
    # Test Thread B stop
    print("Stopping Thread B...")
    thread_manager.stop_thread_b()
    time.sleep(1)
    
    # Test Thread A resume
    print("Resuming Thread A...")
    thread_manager.start_thread_a()
    time.sleep(1)
    
    # Cleanup
    conversation_thread.stop_conversation_thread()
    input_interface.cleanup()
    print("Test completed")

if __name__ == "__main__":
    test_conversation_thread()
