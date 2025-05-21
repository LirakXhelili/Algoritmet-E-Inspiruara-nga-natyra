from models.parser import WarehouseParser
from models.solution import InitialSolution
from operator_functions.warehouse_operator import warehouse_operator  # Correct import for the operator function

def save_solution_to_file(solution, file_name):
    """
    Saves the solution to a file in a readable format.
    :param solution: The solution dictionary to save.
    :param file_name: The name of the file to save the solution to.
    """
    with open(file_name, "w") as f:
        f.write("{\n")
        f.write(f"  'open_warehouses': {solution['open_warehouses']},\n")
        f.write(f"  'total_cost': {solution['total_cost']},\n")
        f.write("  'supply_matrix': [\n")
        for row in solution['supply_matrix']:
            f.write(f"    {row},\n")
        f.write("  ]\n")
        f.write("}\n")
    print(f"Solution saved to {file_name}")

if __name__ == '__main__':
    input_file = './inputs/wlp01.dzn'  
    output_file = './Output/output.txt'  

    
    parser = WarehouseParser(input_file)
    data = parser.parse()

    # Generate the initial solution
    initial_sol = InitialSolution.generate_initial_solution(input_file)

    # Convert the initial solution to the format expected by the operator
    current_solution = {
        'open_warehouses': list(initial_sol.used_warehouses),  # Convert set to list for saving
        'total_cost': 0,  # Placeholder, will be calculated by the operator
        'supply_matrix': [[0 for _ in range(len(data.warehouses))] for _ in range(len(data.stores))]
        # Initialize a 2D list with zeros (stores × warehouses)
    }

    # Save the current solution to a file
    save_solution_to_file(current_solution, "current_solution.txt")

    # Run the warehouse operator to optimize the solution
    optimized_solution, success = warehouse_operator(
        data.warehouses,  # List of warehouses
        data.stores,      # List of stores
        current_solution,     # Initial solution
        data.incompatibilities  # Incompatibility constraints
    )

    # Debugging: Print the results
    print("Optimized solution:", optimized_solution)
    print("Was optimization successful?", success)

    # Check if the operator succeeded
    if success:
        print("Optimized solution found:")
        print(optimized_solution)

        # Save the optimized solution to a file
        save_solution_to_file(optimized_solution, "optimized_solution.txt")
    else:
        print("No improvement was made to the solution.")
