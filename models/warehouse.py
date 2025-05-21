class warehouse:
    id=0
    capacity = 0
    fixed_cost = 0

    def __init__(self,id,capacity,fixed_cost):
        self.id = id
        self.capacity = capacity
        self.fixed_cost = fixed_cost
        
    def __str__(self):
        return f"Warehouse(id={self.id}, capacity={self.capacity}, fixed_cost={self.fixed_cost})"
        
    def __repr__(self):
        return self.__str__()