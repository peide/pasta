import sys

YELLOW = '\33[93m'
RED = '\033[91m'
END = '\033[0m'
   
def print_error_and_exit(message): 
    print(RED + "Error: " + message + END)
    sys.exit(-1)

def print_waring(message):
    print(YELLOW + "Warning: " + message + END)