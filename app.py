from collections import defaultdict
from models.parser import WarehouseParser
from models.solution import InitialSolution

import os
import copy
from Operator.warehouse_operator import move_to_cheaper_warehouse, operator_swap_store_assignments

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

def optimize_solution_ils(initial_sol, data, max_iter=50):
    """
    Optimize solution using Iterated Local Search
    """
    best_solution, best_cost, iteration_costs = initial_sol.iterated_local_search(
        max_iterations=max_iter,
        perturbation_strength=0.3,
        local_search_iterations=100
    )
    return best_solution

def optimize_solution(initial_sol, data, max_iter=1000):
    current_sol = initial_sol
    best_cost = current_sol.compute_fitness()
    no_improvement_count = 0
    max_no_improvement = 50  # Stop if no improvement for 50 iterations
    
    print(f"Starting optimization with initial cost: {best_cost}")
    
    for iteration in range(max_iter):
        # Apply operator 1 multiple times
        improved1 = False
        for _ in range(5):  # Try operator 1 multiple times per iteration
            new_sol, temp_improved = move_to_cheaper_warehouse(copy.deepcopy(current_sol), data)
            if temp_improved:
                current_sol = new_sol
                improved1 = True
        
        # Apply operator 2 multiple times
        improved2 = False
        for _ in range(5):  # Try operator 2 multiple times per iteration
            new_sol, temp_improved = operator_swap_store_assignments(copy.deepcopy(current_sol), data)
            if temp_improved:
                current_sol = new_sol
                improved2 = True
        
        # Check if improvement was made
        new_cost = current_sol.compute_fitness()
        if new_cost < best_cost:
            improvement = best_cost - new_cost
            best_cost = new_cost
            no_improvement_count = 0
            print(f"Iteration {iteration}: New best cost: {best_cost} (improved by {improvement})")
        else:
            no_improvement_count += 1
            
        # Early termination if no improvements
        if not (improved1 or improved2) or no_improvement_count >= max_no_improvement:
            print(f"Stopping optimization at iteration {iteration} (no improvement for {no_improvement_count} iterations)")
            break
    
    return current_sol

if __name__ == '__main__':
    input_folder = './inputs'
    output_folder = './output'  # Keep original output folder
    output_folder_ils = './output_ILS'  # Add new ILS output folder
    os.makedirs(output_folder, exist_ok=True)
    os.makedirs(output_folder_ils, exist_ok=True)

    # Track results for summary
    results_summary = []

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
        initial_cost = initial_sol.compute_fitness()
        
        # Optimize the solution using Iterated Local Search
        print(f"Using Iterated Local Search optimization...")
        optimized_sol = optimize_solution_ils(initial_sol, data, max_iter=50)
        optimized_cost = optimized_sol.compute_fitness()
        
        # Validate solution
        is_valid, message = validate_solution(optimized_sol, data)
        print(f"Optimized solution validation: {is_valid} - {message}")
        print(f"Initial cost: {initial_cost}")
        print(f"Optimized cost: {optimized_cost}")
        improvement = initial_cost - optimized_cost
        improvement_pct = (improvement / initial_cost) * 100
        print(f"Total improvement: {improvement} ({improvement_pct:.2f}%)")

        # Save solution to original output folder (keep existing format)
        output_path = os.path.join(output_folder, f"opt_{file_name}.txt")
        optimized_sol.write_results(output_path)
        print(f"Solution saved to {output_path}")

        # Save ILS solution to dedicated ILS folder with input file name
        base_name = file_name.replace('.dzn', '')
        output_path_ils = os.path.join(output_folder_ils, f"{base_name}_ILS.txt")
        optimized_sol.write_results(output_path_ils)
        print(f"ILS solution saved to {output_path_ils}")
        
        # Add to summary
        results_summary.append({
            'instance': base_name,
            'initial_cost': initial_cost,
            'ils_cost': optimized_cost,
            'improvement': improvement,
            'improvement_pct': improvement_pct,
            'valid': is_valid
        })

    # Create summary file
    summary_path = os.path.join(output_folder_ils, 'ILS_Results_Summary.txt')
    with open(summary_path, 'w') as f:
        f.write("Iterated Local Search Results Summary\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"{'Instance':<12} {'Initial':<10} {'ILS Cost':<10} {'Improvement':<12} {'%':<8} {'Valid':<6}\n")
        f.write("-" * 70 + "\n")
        
        total_initial = 0
        total_ils = 0
        
        for result in results_summary:
            f.write(f"{result['instance']:<12} {result['initial_cost']:<10} {result['ils_cost']:<10} "
                   f"{result['improvement']:<12} {result['improvement_pct']:<7.2f}% {result['valid']:<6}\n")
            total_initial += result['initial_cost']
            total_ils += result['ils_cost']
        
        f.write("-" * 70 + "\n")
        total_improvement = total_initial - total_ils
        total_improvement_pct = (total_improvement / total_initial) * 100
        f.write(f"{'TOTAL':<12} {total_initial:<10} {total_ils:<10} "
               f"{total_improvement:<12} {total_improvement_pct:<7.2f}%\n")
    
    print(f"\n" + "=" * 50)
    print(f"Original solutions saved to {output_folder}/")
    print(f"ILS Results Summary saved to {summary_path}")
    print(f"All ILS solutions saved to {output_folder_ils}/")
    print(f"Total instances processed: {len(results_summary)}")
    print(f"Overall improvement: {total_improvement_pct:.2f}%")