# CONSUMER
from llm_economist.market_core.market_core import Ledger, Market, Order
from typing import List, Dict


# class ConsumerAgent(LLMAgent):
#     def __init__(self, llm: str, port: int, name: str,
#                  income_stream: float, ces_params: Dict[str, float],
#                  **kwargs):
#         super().__init__(llm, port, name, **kwargs)
#         
#         self.income = income_stream
#         self.ces_params = ces_params  # CES utility parameters
#         self.inventory = {}  # Consumer's goods inventory
#         
#         self.system_prompt = self._create_system_prompt()
#         
#     def _create_system_prompt(self):
#         return f"""You are {self.name}, a consumer with income {self.income}.
# Your goal is to maximize utility by purchasing goods optimally.
# 
# CES utility parameters: {self.ces_params}
# Current inventory: {self.inventory}
# 
# Use JSON format for responses."""
#     
#     def submit_orders(self, market: Market, timestep: int) -> List[Order]:
#         """Submit orders based on CES utility maximization"""
#         # Get available quotes
#         quotes = self._get_available_quotes(market)
#         
#         # LLM decides on optimal consumption bundle
#         prompt = f"""Based on available goods and prices:
# {quotes}
# 
# Your income: {self.income}
# CES utility parameters: {self.ces_params}
# 
# Choose optimal consumption to maximize utility.
# Respond with: {{"orders": [{{"good": "good1", "quantity": q1, "max_price": p1}}, ...]}}"""
#         
#         response = self.act_llm(timestep, ['orders'], self._parse_orders)
#         orders_data = response[0]
#         
#         orders = []
#         for order_data in orders_data:
#             order = Order(
#                 consumer_id=self.name,
#                 firm_id="any",  # Would need to determine preferred firm
#                 good=order_data['good'],
#                 quantity=order_data['quantity'],
#                 max_price=order_data['max_price']
#             )
#             orders.append(order)
#             
#         return orders
    
class FixedConsumerAgent():
    def __init__(self, name: str, income_stream: float, ledger: 'Ledger', market: 'Market', ces_params: Dict[str, float]=None, goods: List[str]=None):
        self.name = name
        self.income = income_stream
        self.ces_params = ces_params
        self.ledger = ledger
        self.market = market
        
        # Initialize cash in ledger (starting with 0, will receive income)
        self.ledger.credit(self.name, 0.0)
        
        # Initialize empty inventory in ledger - will be populated as consumer buys goods
        for good in goods:
            self.ledger.add_good(self.name, good, 0.0)
        
        # Reference the ledger's inventory directly - no separate copy
        self.inventory = self.ledger.agent_inventories[self.name]
    
    @property
    def cash(self) -> float:
        """Get current cash from ledger"""
        return self.ledger.agent_money[self.name]
    
    def receive_income(self, timestep: int = None):
        """Receive income payment"""
        self.ledger.credit(self.name, self.income)
    
    def submit_order(self, firm_id: str, good: str, quantity: float, max_price: float) -> Order:
        """Submit an order to purchase goods"""
        order = Order(
            consumer_id=self.name,
            firm_id=firm_id,
            good=good,
            quantity=quantity,
            max_price=max_price
        )
        self.market.submit_order(order)
        return order
    
    def make_orders(self, timestep: int) -> List[Order]:
        "Make fixed list of orders"
        quotes = self.market.quotes
        orders = []
        # Budget is evenly spread among its goods (perfect substitution)
        budget_per_good = self.cash / len(self.inventory)
        for good in self.inventory:
            for quote in quotes:
                if quote.good == good:
                    quantity = min(budget_per_good / quote.price, quote.quantity_available)
                    orders.append(self.submit_order(quote.firm_id, good, quantity, quote.price))
                    break
        return orders
    
    