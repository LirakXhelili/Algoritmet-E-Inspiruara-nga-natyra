import random
import copy
from collections import defaultdict



def move_to_cheaper_warehouse(solution, data):
    new_solution = copy.deepcopy(solution)
    supply_matrix = new_solution['supply_matrix']
    open_warehouses = set(new_solution['open_warehouses'])

    store_idx = random.randint(0,len(data.stores)-1)
    store = data.stores[store_idx]
    current_supply = supply_matrix[store_idx]

    current_suppliers = [(wh_idx,q)for wh_idx, q in enumerate(current_supply) if q>0]
    if not current_suppliers:
        return solution, False
    
    wh_from, qty_from = random.choice(current_suppliers)
    current_cost = store.supply_costs[wh_from]
    candidates = [
        (wh_idx, cost) for wh_idx, cost in enumerate(store.supply_costs)
        if cost < current_cost and wh_idx != wh_from
    ]
    candidates.sort(key=lambda x: x[1])

    for wh_to, cost_to in candidates:
            if wh_to not in open_warehouses:
                continue

            used = sum(supply_matrix[s][wh_to] for s in range(len(data.stores)))
            capacity = data.warehouses[wh_to].capacity
            if used + qty_from > capacity:
                continue

            stores_at_wh_to = [s for s in range(len(data.stores)) if supply_matrix[s][wh_to] > 0]
            incompatible = any(
                data.stores[s].id in data.incompatibilities.get(store.id, set())
                for s in stores_at_wh_to
            )
            if incompatible:
                continue

            supply_matrix[store_idx][wh_from] = 0
            supply_matrix[store_idx][wh_to] += qty_from
            if wh_to + 1 not in new_solution['open_warehouses']:
                new_solution['open_warehouses'].append(wh_to + 1)


            still_used = any(supply_matrix[s][wh_from] > 0 for s in range(len(data.stores)))
            if not still_used:
                new_solution['open_warehouses'].remove(wh_from + 1)

            return new_solution, True

    return solution, False

def operator_swap_store_assignments(solution, data):
   
    new_solution = copy.deepcopy(solution)
    supply_matrix = new_solution['supply_matrix']
    open_warehouses = set(new_solution['open_warehouses'])

    s1_idx, s2_idx = random.sample(range(len(data.stores)), 2)
    s1, s2 = data.stores[s1_idx], data.stores[s2_idx]

    w1 = next((w for w in range(len(data.warehouses)) if supply_matrix[s1_idx][w] > 0), None)
    w2 = next((w for w in range(len(data.warehouses)) if supply_matrix[s2_idx][w] > 0), None)

    if w1 is None or w2 is None or w1 == w2:
        return solution, False
    
    used_w1 = sum(supply_matrix[s][w1] for s in range(len(data.stores)))
    used_w2 = sum(supply_matrix[s][w2] for s in range(len(data.stores)))

    cap_w1 = data.warehouses[w1].capacity
    cap_w2 = data.warehouses[w2].capacity

    new_w1_usage = used_w1 - s1.demand + s2.demand
    new_w2_usage = used_w2 - s2.demand + s1.demand

    if new_w1_usage > cap_w1 or new_w2_usage > cap_w2:
        return solution, False
    
    stores_w1 = [s for s in range(len(data.stores)) if supply_matrix[s][w1] > 0 and s != s1_idx]
    stores_w2 = [s for s in range(len(data.stores)) if supply_matrix[s][w2] > 0 and s != s2_idx]

    if any(s2.id in data.incompatibilities.get(data.stores[s].id, set()) for s in stores_w1):
        return solution, False
    if any(s1.id in data.incompatibilities.get(data.stores[s].id, set()) for s in stores_w2):
        return solution, False
    
    supply_matrix[s1_idx][w1] = 0
    supply_matrix[s2_idx][w2] = 0
    supply_matrix[s1_idx][w2] = s1.demand
    supply_matrix[s2_idx][w1] = s2.demand

    if w2 + 1 not in new_solution['open_warehouses']:
        new_solution['open_warehouses'].append(w2 + 1)
    if w1 + 1 not in new_solution['open_warehouses']:
        new_solution['open_warehouses'].append(w1 + 1)

    if not any(supply_matrix[s][w1] > 0 for s in range(len(data.stores))):
        if w1 + 1 in new_solution['open_warehouses']:
            new_solution['open_warehouses'].remove(w1 + 1)
    if not any(supply_matrix[s][w2] > 0 for s in range(len(data.stores))):
        if w2 + 1 in new_solution['open_warehouses']:
            new_solution['open_warehouses'].remove(w2 + 1)

    return new_solution, True


    # for w1 in range(len(data.warehouses)):
    #     if supply_matrix[s1_idx][w1] > 0 and supply_matrix[s2_idx][w1] == 0:
    #         qty = supply_matrix[s1_idx][w1]
    #         used = sum(supply_matrix[s][w1] for s in range(len(data.stores)))
    #         capacity = data.warehouses[w1].capacity

    #         if used - qty + s2.demand > capacity:
    #             continue

    #         stores_assigned = [s for s in range(len(data.stores)) if supply_matrix[s][w1] > 0]
    #         if any(s2.id in data.incompatibilities.get(data.stores[s].id, set()) for s in stores_assigned):
    #             continue

    #         for w in range(len(data.warehouses)):
    #             supply_matrix[s2_idx][w] = 0
    #         supply_matrix[s2_idx][w1] = s2.demand

    #         return new_solution, True

    # return solution, False
