from typing import List, Dict, Tuple
from .warehouse import warehouse
from .store import store

class InstanceData:
    def __init__(self, num_warehouses: int, num_stores: int, 
                 warehouses: List[warehouse], stores: List[store], 
                 supply_cost: Dict[Tuple[int, int], int], incompatibilities: List[Tuple[int, int]]):
        self.num_warehouses = num_warehouses
        self.num_stores = num_stores
        self.warehouses = warehouses
        self.stores = stores
        self.supply_cost = supply_cost
        self.incompatibilities = incompatibilities

    def describe(self):
        print(f"{self.num_warehouses} warehouses, {self.num_stores} stores.")
