from collections import defaultdict
from models.parser import WarehouseParser
from models.solution import InitialSolution

import os
import copy
from Operator.warehouse_operator import(move_to_cheaper_warehouse, operator_swap_store_assignments)
def validate_solution(solution, data):
    # Check store demands are met
    for store_id, assigns in solution.store_assignments.items():
        total = sum(q for _, q in assigns)
        store = data.stores[store_id - 1]
        if total != store.demand:
            return False, f"Store {store_id} demand not met (required: {store.demand}, got: {total})"

    # Check warehouse capacities
    warehouse_usage = defaultdict(int)
    for store_id, assigns in solution.store_assignments.items():
        for w_id, qty in assigns:
            warehouse_usage[w_id] += qty
    
    for w_id, used in warehouse_usage.items():
        warehouse = data.warehouses[w_id - 1]
        if used > warehouse.capacity:
            return False, f"Warehouse {w_id} over capacity (capacity: {warehouse.capacity}, used: {used})"

    # Check incompatibilities
    warehouse_assignments = defaultdict(set)
    for store_id, assigns in solution.store_assignments.items():
        for w_id, _ in assigns:
            warehouse_assignments[w_id].add(store_id)

    for w_id, stores in warehouse_assignments.items():
        for s1 in stores:
            for s2 in stores:
                if s2 in data.incompatibilities.get(s1, set()):
                    return False, f"Incompatible stores {s1} and {s2} both assigned to warehouse {w_id}"

    return True, "Solution is valid"

if __name__ == '__main__':
    input_folder = './inputs'
    output_folder = './output'
    os.makedirs(output_folder, exist_ok=True)

    for file_name in os.listdir(input_folder):
        if not file_name.endswith('.dzn'):
            continue

        input_path = os.path.join(input_folder, file_name)
        print(f"\nProcessing: {file_name}")

        # Parse input file
        parser = WarehouseParser(input_path)
        data = parser.parse()

        # Generate initial solution
        initial_sol = InitialSolution.generate_initial_solution(input_path)
        
        # Validate solution
        is_valid, message = validate_solution(initial_sol, data)
        print(f"Solution validation: {is_valid} - {message}")
        
        if not is_valid:
            print("Warning: Initial solution is invalid!")
            continue

        # Calculate and print cost
        total_cost = initial_sol.compute_fitness()
        print(f"Initial solution cost: {total_cost}")

        # Save solution
        output_path = os.path.join(output_folder, f"sol_{file_name}.txt")
        initial_sol.write_results(output_path)
        print(f"Solution saved to {output_path}")