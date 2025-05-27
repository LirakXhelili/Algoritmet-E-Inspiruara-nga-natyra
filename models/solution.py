import random
import copy
from models import parser
from models import instance_data
from models import warehouse
from models import store
from models import supply
from collections import defaultdict



class InitialSolution:
    def __init__(self, used_warehouses, unused_warehouses, store_assignments,warehouse_info, data):
        self.used_warehouses = used_warehouses
        self.unused_warehouses = unused_warehouses
        self.store_assignments = store_assignments
        self.data = data
        self.supply_matrix = self.convert_assignments_to_matrix()
        self.warehouse_info = warehouse_info
        

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

        return InitialSolution(used_warehouses, unused_warehouses, store_assignments,warehouse_info, data)

    def deep_copy(self):
        """Create a deep copy of the solution"""
        return InitialSolution(
            used_warehouses=copy.deepcopy(self.used_warehouses),
            unused_warehouses=copy.deepcopy(self.unused_warehouses),
            store_assignments=copy.deepcopy(self.store_assignments),
            warehouse_info=copy.deepcopy(self.warehouse_info),
            data=self.data  # Data doesn't need deep copy as it's read-only
        )

    def local_search(self, max_iterations=100):
        """
        Local search using the existing operators
        Returns: (improved_solution, final_cost)
        """
        from Operator.warehouse_operator import move_to_cheaper_warehouse, operator_swap_store_assignments
        
        current_solution = self.deep_copy()
        current_cost = current_solution.compute_fitness()
        no_improvement_count = 0
        max_no_improvement = 20
        
        for iteration in range(max_iterations):
            improved = False
            
            # Apply operator 1 multiple times
            for _ in range(3):
                new_sol, temp_improved = move_to_cheaper_warehouse(current_solution.deep_copy(), self.data)
                if temp_improved:
                    new_cost = new_sol.compute_fitness()
                    if new_cost < current_cost:
                        current_solution = new_sol
                        current_cost = new_cost
                        improved = True
            
            # Apply operator 2 multiple times
            for _ in range(3):
                new_sol, temp_improved = operator_swap_store_assignments(current_solution.deep_copy(), self.data)
                if temp_improved:
                    new_cost = new_sol.compute_fitness()
                    if new_cost < current_cost:
                        current_solution = new_sol
                        current_cost = new_cost
                        improved = True
            
            if improved:
                no_improvement_count = 0
            else:
                no_improvement_count += 1
                
            # Early termination if no improvements
            if no_improvement_count >= max_no_improvement:
                break
        
        return current_solution, current_cost

    def perturbation(self, strength=0.3):
        """
        Perturbation operator to escape local optima
        strength: percentage of assignments to perturb (0.0 to 1.0)
        """
        perturbed_solution = self.deep_copy()
        
        # Get all store assignments
        all_assignments = []
        for store_id, assignments in perturbed_solution.store_assignments.items():
            for w_id, qty in assignments:
                all_assignments.append((store_id, w_id, qty))
        
        # Determine how many assignments to perturb
        num_to_perturb = max(1, int(len(all_assignments) * strength))
        assignments_to_perturb = random.sample(all_assignments, num_to_perturb)
        
        for store_id, old_w_id, qty in assignments_to_perturb:
            # Remove current assignment
            perturbed_solution.store_assignments[store_id].remove((old_w_id, qty))
            perturbed_solution.warehouse_info[old_w_id]['remaining'] += qty
            perturbed_solution.warehouse_info[old_w_id]['assigned_stores'].discard(store_id)
            
            # Find alternative warehouses for this store
            store_incompatibilities = self.data.incompatibilities.get(store_id, set())
            available_warehouses = []
            
            for wh in self.data.warehouses:
                w_id = wh.id
                if w_id == old_w_id:
                    continue
                    
                # Check capacity and incompatibilities
                if perturbed_solution.warehouse_info[w_id]['remaining'] >= qty:
                    if not (store_incompatibilities & perturbed_solution.warehouse_info[w_id]['assigned_stores']):
                        cost = qty * self.data.stores[store_id-1].supply_costs[w_id-1]
                        available_warehouses.append((w_id, cost))
            
            if available_warehouses:
                # Choose randomly among available warehouses (not necessarily the cheapest)
                # This adds more diversification
                if random.random() < 0.7:  # 70% chance to choose randomly
                    new_w_id, _ = random.choice(available_warehouses)
                else:  # 30% chance to choose the cheapest
                    available_warehouses.sort(key=lambda x: x[1])
                    new_w_id, _ = available_warehouses[0]
                
                # Make new assignment
                perturbed_solution.store_assignments[store_id].append((new_w_id, qty))
                perturbed_solution.warehouse_info[new_w_id]['remaining'] -= qty
                perturbed_solution.warehouse_info[new_w_id]['assigned_stores'].add(store_id)
                
                # Update used/unused warehouses (FIXED: safe list operations)
                if new_w_id in perturbed_solution.unused_warehouses:
                    perturbed_solution.unused_warehouses.remove(new_w_id)
                if new_w_id not in perturbed_solution.used_warehouses:
                    perturbed_solution.used_warehouses.append(new_w_id)
                    
                if len(perturbed_solution.warehouse_info[old_w_id]['assigned_stores']) == 0:
                    if old_w_id in perturbed_solution.used_warehouses:
                        perturbed_solution.used_warehouses.remove(old_w_id)
                    if old_w_id not in perturbed_solution.unused_warehouses:
                        perturbed_solution.unused_warehouses.append(old_w_id)
            else:
                # If no alternative found, revert the assignment
                perturbed_solution.store_assignments[store_id].append((old_w_id, qty))
                perturbed_solution.warehouse_info[old_w_id]['remaining'] -= qty
                perturbed_solution.warehouse_info[old_w_id]['assigned_stores'].add(store_id)
        
        return perturbed_solution

    def iterated_local_search(self, max_iterations=50, perturbation_strength=0.3, local_search_iterations=100):
        """
        Iterated Local Search algorithm
        
        Args:
            max_iterations: Maximum number of ILS iterations
            perturbation_strength: Strength of perturbation (0.0 to 1.0)
            local_search_iterations: Maximum iterations for each local search
            
        Returns:
            best_solution: The best solution found
            best_cost: Cost of the best solution
            iteration_costs: List of costs at each iteration for analysis
        """
        print(f"Starting Iterated Local Search with {max_iterations} iterations...")
        
        # Initialize with local search on current solution
        current_solution, current_cost = self.local_search(local_search_iterations)
        best_solution = current_solution.deep_copy()
        best_cost = current_cost
        
        iteration_costs = [current_cost]
        no_improvement_count = 0
        max_no_improvement = max_iterations // 4  # Allow 25% of iterations without improvement
        
        print(f"Initial local search result: {current_cost}")
        
        for iteration in range(max_iterations):
            # Perturbation
            perturbed_solution = current_solution.perturbation(perturbation_strength)
            
            # Local search on perturbed solution
            local_optimum, local_cost = perturbed_solution.local_search(local_search_iterations)
            
            # Acceptance criterion (accept if better than current)
            if local_cost < current_cost:
                current_solution = local_optimum
                current_cost = local_cost
                no_improvement_count = 0
                print(f"Iteration {iteration + 1}: Accepted new solution with cost {local_cost}")
                
                # Update best solution if this is the best so far
                if local_cost < best_cost:
                    best_solution = local_optimum.deep_copy()
                    best_cost = local_cost
                    print(f"*** NEW BEST SOLUTION: {best_cost} ***")
            else:
                no_improvement_count += 1
                
            iteration_costs.append(local_cost)
            
            # Adaptive perturbation strength
            if no_improvement_count > 5:
                perturbation_strength = min(0.5, perturbation_strength * 1.1)  # Increase perturbation
            elif no_improvement_count == 0:
                perturbation_strength = max(0.1, perturbation_strength * 0.9)  # Decrease perturbation
            
            # Early termination if no improvement for too long
            if no_improvement_count >= max_no_improvement:
                print(f"Stopping ILS at iteration {iteration + 1} due to no improvement for {no_improvement_count} iterations")
                break
        
        print(f"ILS completed. Best cost: {best_cost}")
        return best_solution, best_cost, iteration_costs