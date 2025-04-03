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

        print('\nWarehouse capacities and opening costs:')
        for i, w in enumerate(self.warehouses):
            print(f'Warehouse {i}: Capacity = {w.capacity}, Opening Cost = {w.fixed_cost}')
        

        print('\nStore demands:')
        for i, s in enumerate(self.stores):
            print(f'Store {i} requires {s.demand} units of goods')
        

        print('\nSample supply costs (first 5 entries):')
        for i, s in enumerate(self.supply[:5]):
            print(f'Supply {i}: Store {s.store_id} to Warehouse {s.warehouse_id} costs {s.cost_per_unit} per unit')
        

        print('\nStore incompatibilities:')
        for store_id, incompatible_stores in self.incompatibilities.items():
            if incompatible_stores:  
                incompatible_list = ', '.join(f'store {x}' for x in sorted(incompatible_stores)[:-1])
                last_incompatible = sorted(incompatible_stores)[-1] if incompatible_stores else ''
                
                if incompatible_list:
                    print(f'Store {store_id} cannot be served with {incompatible_list}, and store {last_incompatible}.')
                else:
                    print(f'Store {store_id} cannot be served with store {last_incompatible}.')
