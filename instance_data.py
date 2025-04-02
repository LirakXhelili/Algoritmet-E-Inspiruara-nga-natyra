from typing import List, Dict, Tuple,Set
from .warehouse import warehouse
from .store import store
from .supply import supply

class InstanceData:
    def __init__(
        self,
        num_warehouses: int,
        num_stores: int,
        warehouses: List[warehouse],
        stores: List[store],
        supply: List[supply],
        incompatibilities: Dict[int, Set[int]] 
    ):
        
        self.num_warehouses = num_warehouses
        self.num_stores = num_stores
        self.warehouses = warehouses
        self.stores = stores
        self.supply = supply
        self.incompatibilities = incompatibilities

    def describe(self):
        print(f"{self.num_warehouses} warehouses, {self.num_stores} stores.")
