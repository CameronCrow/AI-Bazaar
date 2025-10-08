# FIRM
from llm_economist.market_core.market_core import Ledger, Market, Quote
from typing import List, Dict

# lass FirmAgent(LLMAgent):
#    def __init__(self, llm: str, port: int, name: str, 
#                 goods: List[str], initial_cash: float, 
#                 policy: str = "profit_maximizing"):
#        super().__init__(llm, port, name) #! EXPAND THIS
#        
#        self.goods = goods  # List of goods this firm can produce
#        self.cash = initial_cash
#        self.policy = policy
#        self.inventory = {good: 0.0 for good in goods}
#        self.supplies = {good: 0.0 for good in goods}  # Input goods needed
#        
#        # CES production parameters
#        self.production_function = self._setup_production_function()
#        
#        self.system_prompt = self._create_system_prompt()
#    
#    #! WHAT IS THIS?    
#    def _setup_production_function(self):
#        """Setup CES production function parameters"""
#        # This would be configurable based on firm type
#        return {
#            'elasticity': 0.5,  # CES elasticity parameter
#            'efficiency': 1.0,  # Total factor productivity
#            'input_shares': {good: 1.0/len(self.goods) for good in self.goods}
#        }
#    
#    def _create_system_prompt(self):
#        return f"""You are {self.name}, a firm that produces {', '.join(self.goods)}.
# our goal is to maximize profit by:
# . Purchasing supplies at competitive prices
# . Setting optimal prices for your products
# . Producing efficiently given your supplies
# 
# urrent inventory: {self.inventory}
# urrent cash: {self.cash}
# roduction policy: {self.policy}
# 
# se JSON format for responses: {{"action": "value"}}"""
#    
#    def set_price(self, market: Market, timestep: int) -> Dict[str, float]:
#        """Decide on prices for today based on market conditions"""
#        # Get market information
#        market_info = self._get_market_info(market)
#        
#        # LLM decides on prices
#        prompt = f"""Based on current market conditions:
# market_info}
# 
# et optimal prices for your goods. Consider your costs, competition, and demand.
# espond with: {{"prices": {{"good1": price1, "good2": price2, ...}}}}"""
#        
#        response = self.act_llm(timestep, ['prices'], self._parse_prices)
#        return response[0]
#    
#    def purchase_supplies(self, market: Market, timestep: int) -> List[Order]:
#        """Purchase supplies based on production needs"""
#        orders = []
#        
#        # Analyze current inventory and production needs
#        prompt = f"""You need supplies to produce goods. Current supplies: {self.supplies}
# vailable quotes: {self._get_supply_quotes(market)}
# 
# ecide how much of each supply to purchase. Consider your cash: {self.cash}
# espond with: {{"purchases": {{"supply_good": quantity, ...}}}}"""
#        
#        response = self.act_llm(timestep, ['purchases'], self._parse_purchases)
#        purchases = response[0]
#        
#        # Create orders for supplies
#        for good, quantity in purchases.items():
#            if good in self.supplies and quantity > 0:
#                order = Order(
#                    consumer_id=self.name,
#                    firm_id="supplier",  # Would need to determine supplier
#                    good=good,
#                    quantity=quantity,
#                    max_price=999.0  # Would need better price discovery
#                )
#                orders.append(order)
#                
#        return orders
#    
#    def produce_goods(self, timestep: int) -> Dict[str, float]:
#        """Produce goods based on available supplies"""
#        # CES production function
#        if not self.supplies:
#            return {}
#            
#        # Calculate production based on supplies
#        # This is a simplified CES function
#        total_supplies = sum(self.supplies.values())
#        if total_supplies == 0:
#            return {}
#            
#        # Distribute production across goods based on efficiency
#        production = {}
#        for good in self.goods:
#            efficiency = self.production_function['efficiency']
#            production[good] = efficiency * (total_supplies / len(self.goods))
#            
#        # Update inventory
#        for good, quantity in production.items():
#            self.inventory[good] += quantity
#            
#        return production
#    
#    def post_quotes(self, prices: Dict[str, float]) -> List[Quote]:
#        """Post quotes to market with current prices"""
#        quotes = []
#        for good, price in prices.items():
#            if good in self.inventory and self.inventory[good] > 0:
#                quote = Quote(
#                    firm_id=self.name,
#                    good=good,
#                    price=price,
#                    quantity_available=self.inventory[good]
#                )
#                quotes.append(quote)
#        return quotes
    
    

class FixedFirmAgent():
    def __init__(self, name: str, 
                 goods: List[str], initial_cash: float, ledger: Ledger, market: Market):
        self.name = name
        self.goods = goods  # List of goods this firm can produce
        
        self.ledger = ledger
        self.market = market
        # self.policy = policy
        self.ledger.credit(self.name, initial_cash)
        
        # Initialize inventory in ledger
        self.ledger.add_good(self.name, "supply", 0.0)
        for good in goods:
            self.ledger.add_good(self.name, good, 0.0)
            
        # Reference the ledger's inventory directly - no separate copy
        self.inventory = self.ledger.agent_inventories[self.name]
        
    @property
    def cash(self) -> float:
        """Get current cash from ledger"""
        return self.ledger.agent_money[self.name]
    
    @property
    def supplies(self) -> float:
        """Get current supply amount from ledger inventory"""
        return self.inventory["supply"]

    def set_price(self, price: int, timestep: int = None) -> Dict[str, float]:
        """Set fixed prices for goods"""
        return {good: price for good in self.goods}

    def purchase_supplies(self, quantity_to_purchase: float, unit_price: float, timestep: int) -> float:
        """Purchases aggregate supply"""
        cost = quantity_to_purchase * unit_price
        # Only spend what we can afford
        total_cost = min(cost, self.cash)
        total_quantity = total_cost / unit_price
        
        # Deduct cost and add supply to ledger
        self.ledger.credit(self.name, -total_cost)
        self.ledger.add_good(self.name, "supply", total_quantity)
                
        return total_quantity
    
    def produce_goods(self, timestep: int):
        """Produce goods evenly given available supplies"""
        production = {}
        supply_available = self.supplies
        
        if supply_available <= 0:
            return
            
        # Calculate production for each good
        production_per_good = supply_available / len(self.goods)
        
        for good in self.goods:
            # Add produced goods to inventory via ledger
            self.ledger.add_good(self.name, good, production_per_good)
            
        # Consume all supplies used in production
        self.ledger.add_good(self.name, "supply", -supply_available)
                    
    
    def post_quotes(self, prices: Dict[str, float]) -> List[Quote]:
        """Post quotes to market with current prices"""
        quotes = []
        for good, price in prices.items():
            if good in self.inventory and self.inventory[good] > 0:
                quote = Quote(
                    firm_id=self.name,
                    good=good,
                    price=price,
                    quantity_available=self.inventory[good]
                )
                quotes.append(quote)
                self.market.post_quote(quote)
        return quotes