from models.parser import WarehouseParser
from models.solution import InitialSolution

if __name__ == '__main__':
    input_file = './inputs/wlp01.dzn'  # Adjust the file path as needed
    output_file = './Output/output.txt'  # The output file path

    # Initialize and parse the data
    parser = WarehouseParser(input_file)
    data = parser.parse()

    initial_sol = InitialSolution.generate_initial_solution(input_file)
    initial_sol.write_results()

    # # Write the results to the output file
    # write_results_to_file(data, output_file)
