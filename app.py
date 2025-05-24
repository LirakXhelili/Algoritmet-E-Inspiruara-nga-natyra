from collections import defaultdict
from models.parser import WarehouseParser
from models.solution import InitialSolution
from operator_functions.warehouse_operator import warehouse_operator  

def validate_solution(solution: dict, data):
    # Validate store demands
    for store_idx, store in enumerate(data.stores):
        total = sum(solution['supply_matrix'][store_idx])
        if total != store.demand:
            return False, f"Store {store.id} demand not met (required: {store.demand}, got: {total})"

    # Validate warehouse capacity
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

if __name__ == '__main__':
    input_file = './inputs/wlp01.dzn'  
    output_file = './Output/output.txt'  

    
    parser = WarehouseParser(input_file)
    data = parser.parse()

    initial_sol = InitialSolution.generate_initial_solution(input_file)

   
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
