# llm_economist/utils/input_interface.py
from abc import ABC, abstractmethod
from typing import Optional
import tkinter as tk

class InputInterface(ABC):
    """Abstract base class for input interfaces."""
    
    @abstractmethod
    def get_input(self) -> Optional[str]:
        """Get input from the user. Returns None if no input available."""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if input is available."""
        pass
    
    @abstractmethod
    def cleanup(self):
        """Clean up resources."""
        pass

class TkinterInputInterface(InputInterface):
    """Tkinter-based input interface."""
    
    def __init__(self):
        import tkinter as tk
        from tkinter import ttk, scrolledtext
        
        self.root = tk.Tk()
        self.root.title("Agent Conversation")
        self.root.geometry("600x400")
        
        # Worker selection area (initially hidden)
        self.worker_selection_frame = ttk.Frame(self.root)
        self.worker_selection_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(self.worker_selection_frame, text="Select an agent to converse with:", 
                 font=("Arial", 10, "bold")).pack(anchor=tk.W)
        
        self.worker_var = tk.StringVar()
        self.worker_dropdown = ttk.Combobox(self.worker_selection_frame, textvariable=self.worker_var, 
                                           state="readonly", width=50)
        self.worker_dropdown.pack(fill=tk.X, pady=(5, 0))
        
        self.select_button = ttk.Button(self.worker_selection_frame, text="Select Agent", 
                                       command=self._select_worker)
        self.select_button.pack(pady=(5, 0))
        
        # Input area (initially hidden)
        self.input_frame = ttk.Frame(self.root)
        self.input_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.input_entry = ttk.Entry(self.input_frame)
        self.input_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.send_button = ttk.Button(self.input_frame, text="Send", command=self._send_message)
        self.send_button.pack(side=tk.RIGHT, padx=(5, 0))
        
        # Conversation display
        self.conversation_text = scrolledtext.ScrolledText(self.root, wrap=tk.WORD)
        self.conversation_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Message queue
        self.message_queue = []
        self.input_entry.bind('<Return>', lambda e: self._send_message())
        
        # Worker selection callback
        self.worker_selection_callback = None
        self.available_workers = []
        
        # Initially hide both interfaces
        self.input_frame.pack_forget()
        self.worker_selection_frame.pack_forget()
        self.root.withdraw()
    
    def show(self):
        """Show the input interface."""
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()
    
    def hide(self):
        """Hide the input interface."""
        self.root.withdraw()
    
    def _send_message(self):
        """Send the current message."""
        message = self.input_entry.get().strip()
        if message:
            self.message_queue.append(message)
            self.input_entry.delete(0, tk.END)
    
    def get_input(self) -> Optional[str]:
        """Get input from the user."""
        if self.message_queue:
            return self.message_queue.pop(0)
        return None
    
    def is_available(self) -> bool:
        """Check if input is available."""
        return len(self.message_queue) > 0
    
    def add_message(self, sender: str, message: str):
        """Add a message to the conversation display."""
        self.conversation_text.insert(tk.END, f"{sender}: {message}\n\n")
        self.conversation_text.see(tk.END)
    
    def show_worker_selection(self, workers, callback):
        """Show worker selection interface."""
        self.available_workers = workers
        self.worker_selection_callback = callback
        
        # Populate dropdown with worker options
        worker_options = []
        for worker in workers:
            worker_info = f"{worker.name} - {worker.role} (Skill: {worker.v:.1f})"
            worker_options.append(worker_info)
        
        self.worker_dropdown['values'] = worker_options
        if worker_options:
            self.worker_var.set(worker_options[0])  # Set default selection
        
        # Show worker selection frame
        import tkinter as tk
        self.worker_selection_frame.pack(fill=tk.X, padx=10, pady=5)
        self.show()
    
    def hide_worker_selection(self):
        """Hide worker selection interface."""
        self.worker_selection_frame.pack_forget()
        self.hide()
    
    def _select_worker(self):
        """Handle worker selection."""
        selected_text = self.worker_var.get()
        if selected_text and self.worker_selection_callback:
            # Find the worker that matches the selected text
            for worker in self.available_workers:
                worker_info = f"{worker.name} - {worker.role} (Skill: {worker.v:.1f})"
                if worker_info == selected_text:
                    self.worker_selection_callback(worker)
                    break
    
    def show_conversation_interface(self):
        """Show the conversation interface."""
        import tkinter as tk
        self.worker_selection_frame.pack_forget()
        self.input_frame.pack(fill=tk.X, padx=10, pady=5)
        self.show()
    
    def hide_conversation_interface(self):
        """Hide the conversation interface."""
        self.input_frame.pack_forget()
        self.hide()
    
    def cleanup(self):
        """Clean up resources."""
        if self.root:
            self.root.destroy()
