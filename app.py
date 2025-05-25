from collections import defaultdict
from models.parser import WarehouseParser
from models.solution import InitialSolution
import os
import copy
from Operator.warehouse_operator import(move_to_cheaper_warehouse, operator_swap_store_assignments)
def validate_solution(solution: dict, data):
   
    for store_idx, store in enumerate(data.stores):
        total = sum(solution['supply_matrix'][store_idx])
        if total != store.demand:
            return False, f"Store {store.id} demand not met (required: {store.demand}, got: {total})"

   
    warehouse_usage = [0] * len(data.warehouses)
    for store_idx in range(len(data.stores)):
        for wh_idx in range(len(data.warehouses)):
            warehouse_usage[wh_idx] += solution['supply_matrix'][store_idx][wh_idx]

    for wh_idx, used in enumerate(warehouse_usage):
        warehouse = data.warehouses[wh_idx]
        if used > warehouse.capacity:
            return False, f"Warehouse {warehouse.id} over capacity (capacity: {warehouse.capacity}, used: {used})"

   
    warehouse_assignments = defaultdict(set)
    for store_idx in range(len(data.stores)):
        for wh_idx in range(len(data.warehouses)):
            if solution['supply_matrix'][store_idx][wh_idx] > 0:
                warehouse_assignments[wh_idx].add(data.stores[store_idx].id)

    for wh_idx, stores in warehouse_assignments.items():
        for s1 in stores:
            for s2 in stores:
                if s2 in data.incompatibilities.get(s1, set()):
                    return False, f"Incompatible stores {s1} and {s2} both assigned to warehouse {data.warehouses[wh_idx].id}"

    
    open_warehouses = set(solution['open_warehouses'])
    for wh_idx in range(len(data.warehouses)):
        if wh_idx + 1 not in open_warehouses:
            # warehouse closed, check no supply from it
            for store_idx in range(len(data.stores)):
                if solution['supply_matrix'][store_idx][wh_idx] > 0:
                    return False, f"Store {data.stores[store_idx].id} supplied from closed warehouse {data.warehouses[wh_idx].id}"

    return True, "Solution is valid"


def save_solution_to_file(solution, file_name,format='triples'):

    if format == 'triples':
        triples = []
        for store_idx in range(len(solution['supply_matrix'])):
            for wh_idx in range(len(solution['supply_matrix'][store_idx])):
                q = solution['supply_matrix'][store_idx][wh_idx]
                if q > 0:
                    triples.append((store_idx+1, wh_idx+1, q))
        

        with open(file_name, "w") as f:
            f.write("{")
            f.write(", ".join(f"({s}, {w}, {q})" for s, w, q in triples))
            f.write("}")
    else:
         with open(file_name, "w") as f:
            f.write("[")
            f.write(" ".join(
                "(" + ",".join(map(str, row)) + ")" 
                for row in solution['supply_matrix']
            ))
            f.write("]")

    print(f"Solution saved to {file_name}")

def calculate_total_cost(solution, data):
    total_cost = 0

    for warehouse in data.warehouses:
        if warehouse.id in solution['open_warehouses']:
            total_cost += warehouse.fixed_cost

    for store_idx, store in enumerate(data.stores):
        for wh_idx in range(len(data.warehouses)):
            qty = solution['supply_matrix'][store_idx][wh_idx]
            if qty > 0:
                total_cost += qty * store.supply_costs[wh_idx]

    return total_cost




if __name__ == '__main__':
    input_folder = './inputs'  
    output_folder = './Output'  
    os.makedirs(output_folder,exist_ok=True)

    for file_name in os.listdir(input_folder):
        if not file_name.endswith('.dzn'):
            continue

        input_path = os.path.join(input_folder, file_name)
        print(f"\nProcessing: {file_name}")

        
    parser = WarehouseParser(input_path)
    data = parser.parse()

    initial_sol = InitialSolution.generate_initial_solution(input_path)

   
    current_solution = {
        'open_warehouses': list(initial_sol.used_warehouses),  
        'total_cost': 0, 
        'supply_matrix': [[0 for _ in range(len(data.warehouses))] for _ in range(len(data.stores))]
       
    }
    for store_id in initial_sol.store_assignments:
        for (w_id, q) in initial_sol.store_assignments[store_id]:
            current_solution['supply_matrix'][store_id-1][w_id-1] = q
    
    is_valid, message = validate_solution(current_solution, data)
    print(f"Initial solution validation: {message}")
    if not is_valid:
        raise ValueError("Initial solution is invalid")

 
    save_solution_to_file(current_solution, "./Output/initial_solution.txt")


print("\n=== APPLYING OPERATORS ===")

new_solution_1, success_1 = move_to_cheaper_warehouse(current_solution, data)
if success_1:
    cost_1 = calculate_total_cost(new_solution_1, data)
    is_valid, msg = validate_solution(new_solution_1, data)
    print(f"[Move to Cheaper] Cost: {cost_1}, Valid: {is_valid}, Message: {msg}")
    save_solution_to_file(new_solution_1, "./Output/solution_after_operator1.txt")
else:
    print("Operator 1: No move applied.")


new_solution_2, success_2 = operator_swap_store_assignments(current_solution, data)
if success_2:
    cost_2 = calculate_total_cost(new_solution_2, data)
    is_valid, msg = validate_solution(new_solution_2, data)
    print(f"[Swap Stores] Cost: {cost_2}, Valid: {is_valid}, Message: {msg}")
    save_solution_to_file(new_solution_2, "./Output/solution_after_operator2.txt")
else:
    print("Operator 2: No swap applied.")
  
    # optimized_solution, success = warehouse_operator(
    #     data.warehouses,  
    #     data.stores,      
    #     current_solution,    
    #     data.incompatibilities 
    # )

  
    # if success:
    #     is_valid,message = validate_solution(optimized_solution,data)
    #     print("Optimized solution validation: {message}")
        
    #     if not is_valid:
    #         raise ValueError("Optimized solution is invalid")
        
    #     opening_cost = sum(
    #         w.fixed_cost for w in data.warehouses 
    #         if w.id in optimized_solution['open_warehouses']
    #     )
        
    #     supply_cost = 0
    #     for store_idx in range(len(data.stores)):
    #         for wh_idx in range(len(data.warehouses)):
    #             q = optimized_solution['supply_matrix'][store_idx][wh_idx]
    #             if q > 0:
    #                 supply_cost += q * data.supply_data[store_idx * len(data.warehouses) + wh_idx].cost
    #     optimized_solution['total_cost'] = opening_cost + supply_cost
    #     print(f"Optimized solution cost: {optimized_solution['total_cost']}")
    #     save_solution_to_file(optimized_solution, "./Output/optimized_solution.txt")
    # else:
    #     print("No improvement was made to the solution.")

