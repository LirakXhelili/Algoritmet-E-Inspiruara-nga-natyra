from .warehouse import warehouse
from .store import store
from .supply import supply
from .instance_data import InstanceData
import sys
import re

class WarehouseParser:
    def __init__(self, file_path):
        self.file_path = file_path
        
    def parse(self):
        try:
            with open(self.file_path, 'r') as file:
                content = file.read()
                
                try:
                  
                    warehouses_match = re.search(r"Warehouses\s*=\s*(\d+)\s*;", content)
                    stores_match = re.search(r"Stores\s*=\s*(\d+)\s*;", content)
                    
                    if not warehouses_match or not stores_match:
                        raise ValueError("Missing warehouse or store")
                        
                    num_warehouses = int(warehouses_match.group(1))
                    num_stores = int(stores_match.group(1))
                    
                    
                    capacity = self._parse_array(content, "Capacity")
                    fixed_cost = self._parse_array(content, "FixedCost")
                    goods = self._parse_array(content, "Goods")
                    
                    if len(capacity) != num_warehouses:
                        raise ValueError(f"Expected {num_warehouses} capacity values, got {len(capacity)}")
                    if len(fixed_cost) != num_warehouses:
                        raise ValueError(f"Expected {num_warehouses} fixed cost values, got {len(fixed_cost)}")
                    if len(goods) != num_stores:
                        raise ValueError(f"Expected {num_stores} goods values, got {len(goods)}")
                    
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
                    
                    # Convert to dictionary format
                    incompatibilities = {s: set() for s in range(1, num_stores+1)}
                    for s1, s2 in pairs:
                        incompatibilities[s1].add(s2)
                        incompatibilities[s2].add(s1)
                    
                    # Create domain objects
                    warehouses = [
                        warehouse(id=i+1, capacity=capacity[i], fixed_cost=fixed_cost[i])
                        for i in range(num_warehouses)
                    ]
                    
                    stores = [
                        store(id=i+1, demand=goods[i])
                        for i in range(num_stores)
                    ]
                    
                    supplies = [
                        supply(store_id=s+1, warehouse_id=w+1, cost_per_unit=supply_costs[s][w])
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
                    
                except ValueError as e:
                    print(f"Error parsing file: {str(e)}", file=sys.stderr)
                    sys.exit(1)
                    
        except FileNotFoundError:
            print(f"File not found: {self.file_path}", file=sys.stderr)
            sys.exit(1)
            
        except PermissionError:
            print(f"Permission denied when accessing: {self.file_path}", file=sys.stderr)
            sys.exit(1)
            
        except Exception as e:
            print(f"Unexpected error when parsing file: {str(e)}", file=sys.stderr)
            sys.exit(1)
    
    def _parse_array(self, content, name):
        """Helper method to parse array declarations"""
        match = re.search(rf"{name}\s*=\s*\[\s*([^]]+)\]\s*;", content)
        if not match:
            raise ValueError(f"{name} array not found or malformed")
        return [int(x.strip()) for x in match.group(1).split(',') if x.strip()]