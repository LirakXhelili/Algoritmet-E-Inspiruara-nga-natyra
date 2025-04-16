import re
import sys
from models.warehouse import warehouse  
from models.store import store
from models.supply import supply
from models.instance_data import InstanceData

# class warehouse:
#     def __init__(self, id, capacity, fixed_cost):
#         self.id = id
#         self.capacity = capacity
#         self.fixed_cost = fixed_cost

# class store:
#     def __init__(self, id, demand):
#         self.id = id
#         self.demand = demand

# class supply:
#     def __init__(self, store_id, warehouse_id, cost):
#         self.store_id = store_id
#         self.warehouse_id = warehouse_id
#         self.cost = cost

class InstanceData:
    def __init__(self, num_warehouses, num_stores, warehouses, stores, supply, incompatibilities):
        self.num_warehouses = num_warehouses
        self.num_stores = num_stores
        self.warehouse_data = warehouses
        self.store_data = stores
        self.supply_data = supply
        self.incompatibilities = incompatibilities

    def describe(self):
        print(f"Number of Warehouses: {self.num_warehouses}")
        print(f"Number of Stores: {self.num_stores}")
        print(f"Warehouses: {self.warehouse_data}")
        print(f"Stores: {self.store_data}")


class WarehouseParser:
    def __init__(self, file_path):
        self.file_path = file_path

    def parse(self):
        try:
            with open(self.file_path, 'r') as file:
                content = file.read()

                # Debug: Print the content to verify file is loaded correctly
                print("File content loaded successfully:")
                print(content[:1000])  # Print only the first 1000 characters for clarity

                # Adjust regex to handle extra spaces or potential newline characters
                warehouses_match = re.search(r"Warehouses\s*=\s*(\d+)\s*;", content)
                stores_match = re.search(r"Stores\s*=\s*(\d+)\s*;", content)

                if not warehouses_match or not stores_match:
                    raise ValueError("Missing warehouse or store data")

                num_warehouses = int(warehouses_match.group(1))
                num_stores = int(stores_match.group(1))

                print(f"Parsed warehouses: {num_warehouses}, stores: {num_stores}")

                # Parse the arrays for Capacity, FixedCost, Goods, etc.
                capacity = self._parse_array(content, "Capacity")
                fixed_cost = self._parse_array(content, "FixedCost")
                goods = self._parse_array(content, "Goods")

                if len(capacity) != num_warehouses:
                    raise ValueError(f"Expected {num_warehouses} capacity values, got {len(capacity)}")
                if len(fixed_cost) != num_warehouses:
                    raise ValueError(f"Expected {num_warehouses} fixed cost values, got {len(fixed_cost)}")
                if len(goods) != num_stores:
                    raise ValueError(f"Expected {num_stores} goods values, got {len(goods)}")

                # Parse the supply cost data
                supply_cost_match = re.search(r"SupplyCost\s*=\s*\[\s*([^]]+)\]\s*;", content, re.DOTALL)
                if not supply_cost_match:
                    raise ValueError("SupplyCost matrix not found or malformed")

                supply_lines = [line.strip() for line in supply_cost_match.group(1).split('|') if line.strip()]
                if len(supply_lines) != num_stores:
                    raise ValueError(f"Expected {num_stores} supply cost rows, got {len(supply_lines)}")

                supply_costs = []
                for line in supply_lines:
                    row = [int(x.strip()) for x in line.split(',') if x.strip()]
                    if len(row) != num_warehouses:
                        raise ValueError(f"Expected {num_warehouses} supply costs per row, got {len(row)}")
                    supply_costs.append(row)

                # Parse incompatibilities
                incompat_match = re.search(r"Incompatibilities\s*=\s*(\d+)\s*;", content)
                if not incompat_match:
                    raise ValueError("Incompatibilities count not found")
                num_incompat = int(incompat_match.group(1))

                pairs_match = re.search(r"IncompatiblePairs\s*=\s*\[\s*([^]]+)\]\s*;", content)
                if not pairs_match:
                    raise ValueError("IncompatiblePairs not found or malformed")

                pairs_str = pairs_match.group(1)
                pairs = []
                for pair in pairs_str.split('|'):
                    pair = pair.strip()
                    if pair and pair != ' ':
                        store1, store2 = map(int, [x.strip() for x in pair.split(',')])
                        if store1 < 1 or store1 > num_stores or store2 < 1 or store2 > num_stores:
                            raise ValueError(f"Invalid store ID in incompatible pair: {store1}, {store2}")
                        pairs.append((store1, store2))

                if len(pairs) != num_incompat:
                    raise ValueError(f"Expected {num_incompat} incompatible pairs, got {len(pairs)}")

                # Convert to dictionary format for incompatibilities
                incompatibilities = {s: set() for s in range(1, num_stores + 1)}
                for s1, s2 in pairs:
                    incompatibilities[s1].add(s2)
                    incompatibilities[s2].add(s1)

                # Create warehouse, store, and supply objects
                warehouses = [
                    warehouse(id=i + 1, capacity=capacity[i], fixed_cost=fixed_cost[i])
                    for i in range(num_warehouses)
                ]

                stores = [
                    store(id=i + 1, demand=goods[i])
                    for i in range(num_stores)
                ]

                supplies = [
                    supply(store_id=s + 1, warehouse_id=w + 1, cost=supply_costs[s][w])
                    for s in range(num_stores)
                    for w in range(num_warehouses)
                ]

                return InstanceData(
                    num_warehouses=num_warehouses,
                    num_stores=num_stores,
                    warehouses=warehouses,
                    stores=stores,
                    supply=supplies,
                    incompatibilities=incompatibilities
                )

        except FileNotFoundError:
            print(f"File not found: {self.file_path}")
            sys.exit(1)
        except PermissionError:
            print(f"Permission denied: {self.file_path}")
            sys.exit(1)
        except Exception as e:
            print(f"Error parsing file: {str(e)}")
            sys.exit(1)

    def _parse_array(self, content, name):
        """Helper method to parse array declarations"""
        match = re.search(rf"{name}\s*=\s*\[\s*([^]]+)\]\s*;", content)
        if not match:
            raise ValueError(f"{name} array not found or malformed")
        return [int(x.strip()) for x in match.group(1).split(',') if x.strip()]

# def write_results_to_file(data: InstanceData, output_file: str):
#     """Write the results to the output.txt file in the Output folder"""
#     try:
#         with open(output_file, 'w') as file:
#             file.write(f"Number of Warehouses: {data.num_warehouses}\n")
#             file.write(f"Number of Stores: {data.num_stores}\n")

#             file.write("\nWarehouses:\n")
#             for warehouse in data.warehouse_data:
#                 file.write(f"Warehouse {warehouse.id} - Capacity: {warehouse.capacity}, Fixed Cost: {warehouse.fixed_cost}\n")

#             file.write("\nStores:\n")
#             for store in data.store_data:
#                 file.write(f"Store {store.id} - Demand: {store.demand}\n")

#             file.write("\nSupply Costs:\n")
#             for supply in data.supply_data:
#                 file.write(f"Store {supply.store_id} - Warehouse {supply.warehouse_id} - Cost: {supply.cost}\n")

#             file.write("\nIncompatibilities:\n")
#             for store_id, incompatible_stores in data.incompatibilities.items():
#                 file.write(f"Store {store_id} - Incompatible with stores: {', '.join(map(str, incompatible_stores))}\n")

#         print(f"Results successfully written to {output_file}")

#     except Exception as e:
#         print(f"Error writing results to {output_file}: {str(e)}")


    def write_results(self):
        triples = []
        for store_id in sorted(self.store_assignments.keys()):
            for (w_id, q) in self.store_assignments[store_id]:
                triples.append((store_id, w_id, q))
        
        with open("initial_solution.txt", "w") as f:
            f.write("{")
            f.write(", ".join(f"({s}, {w}, {q})" for s, w, q in triples))
            f.write("}")
        print("Solution written in triple format.")