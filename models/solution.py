import random
from models import parser
from models import instance_data
from models import warehouse
from models import store
from models import supply
from collections import defaultdict

class InitialSolution:
    def __init__(self, used_warehouses, unused_warehouses, store_assignments, data):
        self.used_warehouses = used_warehouses
        self.unused_warehouses = unused_warehouses
        self.store_assignments = store_assignments
        self.data = data
        self.supply_matrix = self.convert_assignments_to_matrix()

    def write_results(self, filename="initial_solution.txt"):
        triplets = []
        for store_id in sorted(self.store_assignments.keys()):
            for (w_id, q) in self.store_assignments[store_id]:
                triplets.append((store_id, w_id, q))

        with open(filename, "w") as f:
            f.write("{")
            f.write(", ".join(f"({s},{w},{q})" for s,w,q in triplets))
            f.write("}")

    def convert_assignments_to_matrix(self):
        n_stores = len(self.data.stores)
        n_warehouses = len(self.data.warehouses)
        matrix = [[0]*n_warehouses for _ in range(n_stores)]
        
        for store_id, assigns in self.store_assignments.items():
            store_idx = store_id - 1  # Convert to 0-based index
            for w_id, qty in assigns:
                wh_idx = w_id - 1  # Convert to 0-based index
                matrix[store_idx][wh_idx] = qty
        return matrix

    def compute_fitness(self):
        total_cost = 0
        open_warehouses = set()
        
        # Calculate supply costs
        for store_id, assigns in self.store_assignments.items():
            store_idx = store_id - 1
            store = self.data.stores[store_idx]
            for w_id, qty in assigns:
                wh_idx = w_id - 1
                total_cost += qty * store.supply_costs[wh_idx]
                open_warehouses.add(w_id)
        
        # Add opening costs
        for w_id in open_warehouses:
            wh_idx = w_id - 1
            total_cost += self.data.warehouses[wh_idx].fixed_cost
            
        return total_cost

    @staticmethod
    def generate_initial_solution(input_file: str):
        warehouse_parser = parser.WarehouseParser(input_file)
        data = warehouse_parser.parse()
        
        warehouse_info = {
            w.id: {
                'capacity': w.capacity,
                'remaining': w.capacity,
                'fixed_cost': w.fixed_cost,
                'assigned_stores': set()
            } for w in data.warehouses
        }

        incompatibilities = data.incompatibilities
        stores_sorted = sorted(data.stores, key=lambda s: len(incompatibilities.get(s.id, set())), reverse=True)

        # Prepare store supply options sorted by cost
        store_supply_options = defaultdict(list)
        for store in data.stores:
            for wh in data.warehouses:
                cost = store.supply_costs[wh.id - 1]  # 0-based index
                store_supply_options[store.id].append((wh.id, cost))
            
            # Sort by increasing cost
            store_supply_options[store.id].sort(key=lambda x: x[1])

        store_assignments = defaultdict(list)
        
        for store in stores_sorted:
            store_id = store.id
            remaining_demand = store.demand
            store_incompatibilities = incompatibilities.get(store_id, set())

            for w_id, unit_cost in store_supply_options[store_id]:
                if remaining_demand <= 0:
                    break
                    
                wh_info = warehouse_info[w_id]
                
                # Check capacity and incompatibilities
                if wh_info['remaining'] <= 0:
                    continue
                if store_incompatibilities & wh_info['assigned_stores']:
                    continue
                
                # Allocate as much as possible
                alloc = min(remaining_demand, wh_info['remaining'])
                store_assignments[store_id].append((w_id, alloc))
                wh_info['remaining'] -= alloc
                wh_info['assigned_stores'].add(store_id)
                remaining_demand -= alloc

            if remaining_demand > 0:
                raise ValueError(f"Store {store_id} demand not met. Remaining: {remaining_demand}")

        used_warehouses = [w_id for w_id, w in warehouse_info.items() if len(w['assigned_stores']) > 0]
        unused_warehouses = [w_id for w_id, w in warehouse_info.items() if len(w['assigned_stores']) == 0]

        return InitialSolution(used_warehouses, unused_warehouses, store_assignments, data)