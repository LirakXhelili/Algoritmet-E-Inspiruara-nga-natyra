from models.parser import WarehouseParser, write_results_to_file
from models.solution import InitialSolution

if __name__ == '__main__':
    input_file = './inputs/wlp14.dzn'  # Adjust the file path as needed
    output_file = './Output/output.txt'  # The output file path

    # Initialize and parse the data
    parser = WarehouseParser(input_file)
    data = parser.parse()

    # Write the results to the output file
    write_results_to_file(data, output_file)
