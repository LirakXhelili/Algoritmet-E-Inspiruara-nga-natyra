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

	def write_results(self):
		triplets = []
		for store_id in sorted(self.store_assignments.keys()):
			for(w_id,q) in self.store_assignments[store_id]:
				triplets.append((store_id,w_id,q))

	

		with open("initial_solution.txt", "w") as f:
			f.write("{")
			f.write(", ".join(f"({s},{w},{q})" for s,w,q in triplets))
			f.write("}")
		# print("Solution written successfully. ")
	
	def compute_fitness(self, instance_data):
			
			total_fixed_cost = 0
			total_supply_cost = 0
			used_warehouses = set()

			for store_id, assignments in self.store_assignments.items():
				for (warehouse_id, quantity) in assignments:
					if quantity > 0:
						used_warehouses.add(warehouse_id)
						# Access supply cost from instance data
						supply_cost = instance_data.stores[store_id - 1].supply_costs[warehouse_id - 1]
						total_supply_cost += quantity * supply_cost

			# Sum fixed costs of warehouses used
			for w in instance_data.warehouses:
				if w.id in used_warehouses:
					total_fixed_cost += w.fixed_cost

			total_cost = total_fixed_cost + total_supply_cost
			# Return negative cost because we want to maximize fitness
			return total_cost

	
	@staticmethod
	def generate_initial_solution(input_file: str):
		warehouse_parser = parser.WarehouseParser(input_file) 
		data: instance_data.InstanceData = warehouse_parser.parse()  
		data.describe() 

		warehouse_info = {
			w.id: {
				'capacity' : w.capacity,
				'remaining' : w.capacity,
				'fixed_cost' : w.fixed_cost,
				'assigned_stores':set()
			} for w in data.warehouses
		}

		incompatibilities = data.incompatibilities
		stores_sorted = sorted(data.stores, key=lambda s:len(incompatibilities.get(s.id,set())), reverse=True)

		# incompatibilities = defaultdict(set)
		# for store_pair in data.incompatibilities:
		# 	s1,s2 = store_pair
		# 	incompatibilities[s1].add(s2)
		# 	incompatibilities[s2].add(s1)
		
		# stores_sorted = sorted(data.stores, key=lambda s:len(incompatibilities.get(s.id,set())),reverse=True)

		store_supplies = defaultdict(list)
		for supply in data.supply_data:
			store_id = supply.store_id
			w_id = supply.warehouse_id
			total_cost = supply.cost * data.stores[store_id-1].demand
			if len(warehouse_info[w_id]['assigned_stores'])==0:
				total_cost+=warehouse_info[w_id]['fixed_cost']
			store_supplies[store_id].append((w_id,supply.cost,total_cost))


		for store_id in store_supplies:
				store_supplies[store_id].sort(key=lambda x: (x[2],x[1]))

		store_assignments = defaultdict(list)

		for store in stores_sorted:
			store_id = store.id
			remaining_demand = store.demand
			store_incompatibilities = incompatibilities.get(store_id,set())

			for w_id, unit_cost, total_cost in store_supplies[store_id]:
				if remaining_demand<=0:
					break
				warehouse = warehouse_info[w_id]
				if warehouse['remaining']<=0:
					continue

				if store_incompatibilities & warehouse['assigned_stores']:
					continue

				alloc = min(remaining_demand, warehouse['remaining'])
				store_assignments[store_id].append((w_id,alloc))
				warehouse['remaining']-=alloc
				warehouse['assigned_stores'].add(store_id)
				remaining_demand-=alloc
			
			if remaining_demand > 0:
				for w_id, warehouse in warehouse_info.items():
					if remaining_demand<=0:
						break
					if warehouse['remaining']<=0:
						continue
					if store_incompatibilities&warehouse['assigned_stores']:
						continue

					alloc = min(remaining_demand,warehouse['remaining'])
					store_assignments[store_id].append((w_id,alloc))
					warehouse['remaining']-=alloc
					warehouse['assigned_stores'].add(store_id)
					remaining_demand-=alloc
			
			if remaining_demand>0:
				raise ValueError(f"Store {store_id} demand not met. Remaining: {remaining_demand}")
			
			

		used_warehouses = [w_id for w_id, w in warehouse_info.items() if len(w['assigned_stores']) > 0]
		unused_warehouses = [w_id for w_id, w in warehouse_info.items() if len(w['assigned_stores']) == 0]
	

		return InitialSolution(used_warehouses, unused_warehouses, store_assignments)
			