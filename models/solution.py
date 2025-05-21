import random
from models import parser
from models import instance_data
from models import warehouse
from models import store
from models import supply
from collections import defaultdict

class InitialSolution:
	def __init__(self, used_warehouses, unused_warehouses, store_assignments):
		self.used_warehouses = used_warehouses
		self.unused_warehouses = unused_warehouses
		self.store_assignments = store_assignments  

	# def write_results(self):
	# 	triplets = []
	# 	for store_id in sorted(self.store_assignments.keys()):
	# 		for(w_id,q) in self.store_assignments[store_id]:
	# 			triplets.append((store_id,w_id,q))

	

		# with open("initial_solution.txt", "w") as f:
		# 	f.write(f"{len(self.used_warehouses)}\n")
		# 	for warehouse_id in self.used_warehouses:
		# 		assigned_stores = [s for s, w in self.store_assignments.items() if w == warehouse_id]
		# 		f.write(f"{warehouse_id} {len(assigned_stores)}\n")
		# 		f.write(" ".join(map(str, assigned_stores)) + "\n")

		# print("Initial solution ")

	def write_results(self):
		triples = []
		for store_id in sorted(self.store_assignments.keys()):
			for (w_id, q) in self.store_assignments[store_id]:
				triples.append((store_id, w_id, q))
    
		with open("initial_solution.txt", "w") as f:
			f.write("{")
			f.write(", ".join(f"({s}, {w}, {q})" for s, w, q in triples))
			f.write("}")
		print("Solution written successfully.")

	@staticmethod
	def generate_initial_solution(input_file: str):
		warehouse_parser = parser.WarehouseParser(input_file) 
		data: instance_data.InstanceData = warehouse_parser.parse()  
		data.describe() 

		incompatible_stores = data.incompatibilities  # Already fixed earlier

		store_supplies = defaultdict(list)
		for supply in data.supply_data:
			store_supplies[supply.store_id].append((supply.warehouse_id, supply.cost))
		for store_id in store_supplies:
			store_supplies[store_id].sort(key=lambda x: x[1])

		store_assignments = defaultdict(list)
		warehouse_capacity = {w.id: w.capacity for w in data.warehouses}  # Changed from warehouse_data
		warehouse_assigned_stores = defaultdict(set)

		stores = data.stores[:]  # Changed from store_data
		random.shuffle(stores)

		for store in stores:
			store_id = store.id
			remaining_demand = store.demand
			supplies = store_supplies.get(store_id, [])

			for (w_id, cost) in supplies:
				if remaining_demand <= 0:
					break
				if warehouse_capacity[w_id] <= 0:
					continue

				# Check incompatibility
				incompatible = any(s in incompatible_stores[store_id] for s in warehouse_assigned_stores[w_id])
				if incompatible:
					continue

				alloc = min(remaining_demand, warehouse_capacity[w_id])
				if alloc <= 0:
					continue

				store_assignments[store_id].append((w_id, alloc))
				warehouse_capacity[w_id] -= alloc
				warehouse_assigned_stores[w_id].add(store_id)
				remaining_demand -= alloc

			if remaining_demand > 0:
				raise ValueError(f"Store {store_id} demand not met. Remaining: {remaining_demand}")

		used_warehouses = [w_id for w_id in warehouse_capacity if warehouse_capacity[w_id] < data.warehouses[w_id-1].capacity]
		unused_warehouses = [w.id for w in data.warehouses if w.id not in used_warehouses]  # Changed from warehouse_data

		return InitialSolution(used_warehouses, unused_warehouses, store_assignments)
			# for supply in data.supply_data:
			# 	if supply.store_id != store.store_id:
			# 		continue

			# 	w_id = supply.warehouse_id
			# 	if warehouse_capacity[w_id] >= store.demand and supply.cost < min_cost:
			# 		min_cost = supply.cost
			# 		best_warehouse = w_id

			
			# if best_warehouse is not None:
			# 	store_assignments[store.store_id] = best_warehouse
			# 	warehouse_capacity[best_warehouse] -= store.demand  
			# 	used_warehouses.add(best_warehouse)  
			# 	unused_warehouses.discard(best_warehouse) 

		
		# return InitialSolution(list(used_warehouses), list(unused_warehouses), store_assignments)
