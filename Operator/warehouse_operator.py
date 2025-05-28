from collections import defaultdict

def move_to_cheaper_warehouse(solution, data):
    """
    Operator 1: Move store assignments to cheaper warehouses
    Returns: (updated solution, improvement_made)
    """
    improved = False
    
    for store_id in list(solution.store_assignments.keys()):
     
        current_assigns = solution.store_assignments[store_id].copy()
        
        for w_from, qty in current_assigns:
            current_cost = qty * solution.data.stores[store_id-1].supply_costs[w_from-1]
       
            for wh in solution.data.warehouses:
                w_to = wh.id
                if w_to == w_from:
                    continue
                
            
                if solution.warehouse_info[w_to]['remaining'] < qty:
                    continue 
                store_incompat = solution.data.incompatibilities.get(store_id, set())
                if store_incompat & solution.warehouse_info[w_to]['assigned_stores']:
                    continue 
                new_cost = qty * solution.data.stores[store_id-1].supply_costs[w_to-1]
                
                if new_cost < current_cost:
                
                    solution.store_assignments[store_id].remove((w_from, qty))
                    solution.store_assignments[store_id].append((w_to, qty))
                  
                    solution.warehouse_info[w_from]['remaining'] += qty
                    solution.warehouse_info[w_from]['assigned_stores'].discard(store_id)
                    solution.warehouse_info[w_to]['remaining'] -= qty
                    solution.warehouse_info[w_to]['assigned_stores'].add(store_id)
                    
                  
                    if len(solution.warehouse_info[w_from]['assigned_stores']) == 0:
                        if w_from in solution.used_warehouses:
                            solution.used_warehouses.remove(w_from)
                        if w_from not in solution.unused_warehouses:
                            solution.unused_warehouses.append(w_from)
                    if w_to in solution.unused_warehouses:
                        solution.unused_warehouses.remove(w_to)
                    if w_to not in solution.used_warehouses:
                        solution.used_warehouses.append(w_to)
                    
                    improved = True
                    break 
        
    return solution, improved

def operator_swap_store_assignments(solution, data):
    """
    Operator 2: Swap assignments between two stores to reduce costs
    Returns: (updated solution, improvement_made)
    """
    improved = False
    store_ids = list(solution.store_assignments.keys())
    
    for i in range(len(store_ids)):
        for j in range(i+1, len(store_ids)):
            s1, s2 = store_ids[i], store_ids[j]
            
          
            if s2 in data.incompatibilities.get(s1, set()):
                continue
                
          
            for a1 in solution.store_assignments[s1].copy():
                w1, q1 = a1
                for a2 in solution.store_assignments[s2].copy():
                    w2, q2 = a2
                    
                    if w1 == w2:
                        continue 
                    wh1_cap = solution.warehouse_info[w1]['remaining'] + q1 >= q2
                    wh2_cap = solution.warehouse_info[w2]['remaining'] + q2 >= q1
                    
                    if wh1_cap and wh2_cap:
                      
                        current_cost = (
                            q1 * solution.data.stores[s1-1].supply_costs[w1-1] +
                            q2 * solution.data.stores[s2-1].supply_costs[w2-1]
                        )
                        
                    
                        new_cost = (
                            q2 * solution.data.stores[s1-1].supply_costs[w1-1] +
                            q1 * solution.data.stores[s2-1].supply_costs[w2-1]
                        )
                        
                        if new_cost < current_cost:
                          
                            solution.store_assignments[s1].remove((w1, q1))
                            solution.store_assignments[s2].remove((w2, q2))
                            solution.store_assignments[s1].append((w2, q2))
                            solution.store_assignments[s2].append((w1, q1))
                            
                          
                            solution.warehouse_info[w1]['remaining'] += q1 - q2
                            solution.warehouse_info[w2]['remaining'] += q2 - q1
                            
                          
                            solution.warehouse_info[w1]['assigned_stores'].discard(s1)
                            solution.warehouse_info[w1]['assigned_stores'].add(s2)
                            solution.warehouse_info[w2]['assigned_stores'].discard(s2)
                            solution.warehouse_info[w2]['assigned_stores'].add(s1)
                            
                            improved = True
                            break  
                
                if improved:
                    break
            if improved:
                break
        if improved:
            break
    
    return solution, improved
