class store:
    id=0
    demand = 0
    supply_costs = []

    def __init__(self,id,demand,supply_costs):
        self.id = id
        self.demand = demand
        self.supply_costs = supply_costs if supply_costs is not None else []

    def __repr__(self):
        return f"Store(id={self.id}, demand={self.demand}, supply_cost={self.supply_costs})"
