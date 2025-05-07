import random

# Constants for probabilities and thresholds
OPEN_WAREHOUSE_PROBABILITY = 0.3
TOP_WAREHOUSE_PERCENTAGE = 0.05

def warehouse_operator(warehouses, stores, current_solution, incompatibilities):
    """
    Modifies the current solution by opening a new warehouse or reassigning stores.
    """
    new_solution = deepcopy_solution(current_solution)

    if should_open_new_warehouse(new_solution, warehouses):
        success = try_open_new_warehouse(new_solution, warehouses, stores, incompatibilities)
    else:
        success = try_reassign_stores(new_solution, warehouses, stores, incompatibilities)

    if success:
        new_solution['total_cost'] = calculate_total_cost(warehouses, stores, new_solution)
        if is_feasible(warehouses, stores, new_solution, incompatibilities):
            return new_solution, True

    return current_solution, False


def deepcopy_solution(solution):
    """Creates a deep copy of the solution."""
    return {
        'open_warehouses': set(solution['open_warehouses']),
        'total_cost': solution['total_cost'],
        'supply_matrix': [row.copy() for row in solution['supply_matrix']]
    }


def should_open_new_warehouse(solution, warehouses):
    """Determines whether to open a new warehouse."""
    return random.random() < OPEN_WAREHOUSE_PROBABILITY and len(solution['open_warehouses']) < len(warehouses)


def try_open_new_warehouse(solution, warehouses, stores, incompatibilities):
    """Attempts to open a new warehouse and assign stores to it."""
    closed_warehouses = [w for w in warehouses if w.id not in solution['open_warehouses']]
    if not closed_warehouses:
        return False

    num_top = max(1, int(len(closed_warehouses) * TOP_WAREHOUSE_PERCENTAGE))
    top_warehouses = sorted(
        closed_warehouses,
        key=lambda w: calculate_potential_savings(w, stores),
        reverse=True
    )[:num_top]

    if not top_warehouses:
        return False

    selected_warehouse = random.choice(top_warehouses)
    solution['open_warehouses'].add(selected_warehouse.id)

    for store in stores:
        assign_store_to_warehouse(store, selected_warehouse, solution, stores, incompatibilities)

    return True


def calculate_potential_savings(warehouse, stores):
    """Calculates potential cost savings for a warehouse."""
    return sum(min(s.demand, warehouse.capacity) * s.supply_costs[warehouse.id] for s in stores) / warehouse.fixed_cost


def assign_store_to_warehouse(store, warehouse, solution, stores, incompatibilities):
    """Assigns a store to a warehouse if compatible and capacity allows."""
    available_capacity = warehouse.capacity - sum(
        solution['supply_matrix'][s.id][warehouse.id] for s in stores
    )
    if available_capacity <= 0:
        return

    assign_qty = min(
        store.demand - sum(solution['supply_matrix'][store.id]),
        available_capacity
    )

    if assign_qty > 0 and is_store_compatible(store, warehouse, solution, stores, incompatibilities):
        solution['supply_matrix'][store.id][warehouse.id] += assign_qty


def is_store_compatible(store, warehouse, solution, stores, incompatibilities):
    """Checks if a store is compatible with a warehouse."""
    for other_store in stores:
        if solution['supply_matrix'][other_store.id][warehouse.id] > 0:
            if (store.id, other_store.id) in incompatibilities or (other_store.id, store.id) in incompatibilities:
                return False
    return True


def try_reassign_stores(solution, warehouses, stores, incompatibilities):
    """Attempts to reassign stores between open warehouses."""
    open_warehouses = [w for w in warehouses if w.id in solution['open_warehouses']]
    if not open_warehouses:
        return False

    assigned_stores = [s for s in stores if sum(solution['supply_matrix'][s.id - 1]) > 0]
    if not assigned_stores:
        return False

    selected_store = random.choice(assigned_stores)
    current_suppliers = [
        w_id for w_id in solution['open_warehouses']
        if solution['supply_matrix'][selected_store.id][w_id] > 0
    ]

    if not current_suppliers:
        return False

    source_warehouse_id = random.choice(current_suppliers)
    source_warehouse = next(w for w in warehouses if w.id == source_warehouse_id)

    target_warehouses = [
        w for w in open_warehouses if w.id != source_warehouse_id and
        is_store_compatible(selected_store, w, solution, stores, incompatibilities)
    ]

    if not target_warehouses:
        return False

    target_warehouse = random.choice(target_warehouses)
    max_move = min(
        solution['supply_matrix'][selected_store.id][source_warehouse_id],
        target_warehouse.capacity - sum(
            solution['supply_matrix'][s.id][target_warehouse.id] for s in stores
        )
    )

    if max_move > 0:
        move_qty = random.randint(1, max_move)
        solution['supply_matrix'][selected_store.id][source_warehouse_id] -= move_qty
        solution['supply_matrix'][selected_store.id][target_warehouse.id] += move_qty
        return True

    return False


def calculate_total_cost(warehouses, stores, solution):
    """
    Calculates the total cost of the solution.
    Includes fixed costs for open warehouses and supply costs for store assignments.
    """
    total_cost = 0

    # Add fixed costs for open warehouses
    for warehouse in warehouses:
        if warehouse.id in solution['open_warehouses']:
            total_cost += warehouse.fixed_cost

    # Add supply costs for store assignments
    for store in stores:
        for warehouse_id, supply_qty in enumerate(solution['supply_matrix'][store.id]):
            if supply_qty > 0:
                total_cost += supply_qty * store.supply_costs[warehouse_id]

    return total_cost


def is_feasible(warehouses, stores, solution, incompatibilities):
    """
    Checks if the solution is feasible.
    Ensures warehouse capacities, store demands, and incompatibility constraints are satisfied.
    """
    # Check warehouse capacity constraints
    for warehouse in warehouses:
        if warehouse.id in solution['open_warehouses']:
            total_supply = sum(
                solution['supply_matrix'][store.id][warehouse.id] for store in stores
            )
            if total_supply > warehouse.capacity:
                return False

    # Check store demand constraints
    for store in stores:
        total_supply = sum(solution['supply_matrix'][store.id])
        if total_supply < store.demand:
            return False

    # Check incompatibility constraints
    for store in stores:
        for other_store in stores:
            if store.id != other_store.id:
                for warehouse_id in solution['open_warehouses']:
                    if (solution['supply_matrix'][store.id][warehouse_id] > 0 and
                        solution['supply_matrix'][other_store.id][warehouse_id] > 0):
                        if (store.id, other_store.id) in incompatibilities or \
                           (other_store.id, store.id) in incompatibilities:
                            return False

    return True