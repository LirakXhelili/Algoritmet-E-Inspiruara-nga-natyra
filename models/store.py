class store:
    id=0
    demand = 0
    supply_costs = []

    def __init__(self,id,demand,supply_costs):
        self.id = id
        self.demand = demand
        self.supply_costs = supply_costs