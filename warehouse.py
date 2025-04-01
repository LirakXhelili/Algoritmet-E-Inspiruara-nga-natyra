class warehouse:
    warehouse_id=0
    capacity = 0
    fixed_cost = 0

    def __init__(self,warehouse_id,capacity,fixed_cost):
        self.warehouse_id = warehouse_id
        self.capacity = capacity
        self.fixed_cost = fixed_cost