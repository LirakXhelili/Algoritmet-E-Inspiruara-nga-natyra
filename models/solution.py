import random
from models import parser
from models import instance_data
from models import warehouse
from models import store
from models import supply

class InitialSolution:
	def __init__(self, used_warehouses, unused_warehouses, store_assignments):
		self.used_warehouses = used_warehouses
		self.unused_warehouses = unused_warehouses
		self.store_assignments = store_assignments  

	def write_results(self):
		with open("initial_solution.txt", "w") as f:
			f.write(f"{len(self.used_warehouses)}\n")
			for warehouse_id in self.used_warehouses:
				assigned_stores = [s for s, w in self.store_assignments.items() if w == warehouse_id]
				f.write(f"{warehouse_id} {len(assigned_stores)}\n")
				f.write(" ".join(map(str, assigned_stores)) + "\n")

		print("Initial solution ")

	@staticmethod
	def generate_initial_solution(input_file: str):
		
		warehouse_parser = parser.WarehouseParser(input_file) 
		data: instance_data.InstanceData = warehouse_parser.parse()  
		data.describe() 

		store_assignments = {}
		used_warehouses = set()
		unused_warehouses = set(w.warehouse_id for w in data.warehouse_data)

		warehouse_capacity = {w.warehouse_id: w.capacity for w in data.warehouse_data}

		stores = data.store_data[:]  
		random.shuffle(stores)  

		for store in stores:
			min_cost = float('inf')
			best_warehouse = None

			
			for supply in data.supply_data:
				if supply.store_id != store.store_id:
					continue

				w_id = supply.warehouse_id
				if warehouse_capacity[w_id] >= store.demand and supply.cost < min_cost:
					min_cost = supply.cost
					best_warehouse = w_id

			
			if best_warehouse is not None:
				store_assignments[store.store_id] = best_warehouse
				warehouse_capacity[best_warehouse] -= store.demand  
				used_warehouses.add(best_warehouse)  
				unused_warehouses.discard(best_warehouse) 

		
		return InitialSolution(list(used_warehouses), list(unused_warehouses), store_assignments)
