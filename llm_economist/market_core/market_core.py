# LEDGER
class Ledger:
    def __init__(self):
        self.agent_money = {}  # agent_id -> money amount
        self.agent_inventories = {}  # agent_id -> {good: quantity}
    
    def credit(self, agent_id: str, amount: float):
        """Add money to agent's account"""
        if agent_id not in self.agent_money:
            self.agent_money[agent_id] = 0
        self.agent_money[agent_id] += amount
    
    def transfer_money(self, from_agent: str, to_agent: str, amount: float):
        """Transfer money between agents"""
        if self.agent_money.get(from_agent, 0) < amount:
            raise ValueError(f"Insufficient funds: {from_agent} has {self.agent_money.get(from_agent, 0)}")
        self.credit(from_agent, -amount)
        self.credit(to_agent, amount)
    
    def transfer_good(self, from_agent: str, to_agent: str, good: str, quantity: float):
        """Transfer goods between agents"""
        if from_agent not in self.agent_inventories:
            self.agent_inventories[from_agent] = {}
        if to_agent not in self.agent_inventories:
            self.agent_inventories[to_agent] = {}
        
        available = self.agent_inventories[from_agent].get(good, 0)
        if available < quantity:
            raise ValueError(f"Insufficient inventory: {from_agent} has {available} {good}")
        
        self.agent_inventories[from_agent][good] -= quantity
        self.agent_inventories[to_agent][good] = self.agent_inventories[to_agent].get(good, 0) + quantity
        
    def add_good(self, to_agent: str, good: str, quantity: float):
        if to_agent not in self.agent_inventories:
            self.agent_inventories[to_agent] = {}
        self.agent_inventories[to_agent][good] = self.agent_inventories[to_agent].get(good, 0) + quantity



# MARKET 
from collections import deque
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class Order:
    consumer_id: str
    firm_id: str
    good: str
    quantity: float
    max_price: float  # willingness to pay

@dataclass
class Quote:
    firm_id: str
    good: str
    price: float
    quantity_available: float

class Market:
    def __init__(self):
        self.orders = deque()  # Queue of pending orders
        self.quotes = []  # List of current quotes
        
    def submit_order(self, order: Order):
        """Add order to the queue"""
        self.orders.append(order)
        
    def post_quote(self, quote: Quote):
        """Post a quote to the market"""
        # Remove existing quote from same firm for same good
        self.quotes = [q for q in self.quotes if not (q.firm_id == quote.firm_id and q.good == quote.good)]
        self.quotes.append(quote)
        
    def clear(self, ledger: Ledger):
        """Match orders with quotes and execute trades"""
        filled_orders = []
        
        while self.orders:
            order = self.orders.popleft()
            filled = self._fill_order(order, ledger)
            if filled:
                filled_orders.append(order)
                
        return filled_orders
    
    def _fill_order(self, order: Order, ledger: Ledger) -> bool:
        """Try to fill a single order"""
        # Find best matching quote
        best_quote = None
        for quote in self.quotes:
            if (quote.firm_id == order.firm_id and 
                quote.good == order.good and 
                quote.price <= order.max_price and
                quote.quantity_available > 0):
                    best_quote = quote
                    break
                    
        if best_quote is None:
            return False
            
        # Determine quantity to trade
        quantity = min(order.quantity, best_quote.quantity_available)
        total_cost = best_quote.price * quantity
        
        # Check if consumer can afford it
        if ledger.agent_money.get(order.consumer_id, 0) < total_cost:
            quantity = ledger.agent_money.get(order.consumer_id, 0) / best_quote.price
            total_cost = best_quote.price * quantity
            
        # Execute the trade
        ledger.transfer_money(order.consumer_id, order.firm_id, total_cost)
        ledger.transfer_good(order.firm_id, order.consumer_id, order.good, quantity)
        
        # Update the quote's available quantity
        best_quote.quantity_available -= quantity
        
        return True