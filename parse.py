# Project: IPPcode24 Code Analyzer
# File: parse.py
# Author: Zdebska Kateryna (xzdebs00)
# Date: 2024-03-12
#
# Description: This script is a filter type (parse.py in Python 3.10) 
# that reads the source code in IPPcode24 from standard input, checks the 
# lexical and syntactic correctness of the code, and outputs XML to standard output.

import sys
import xml.etree.ElementTree as ET
import collections
import re

# List of all valid opcodes
OPCODES = ["MOVE", "CREATEFRAME", "PUSHFRAME", "POPFRAME", "DEFVAR", "CALL", "RETURN", "PUSHS", "POPS",
                      "ADD", "SUB", "MUL", "IDIV", "LT", "GT", "EQ", "AND", "OR", "NOT", "INT2CHAR", "STRI2INT",
                      "READ", "WRITE", "CONCAT", "STRLEN", "GETCHAR", "SETCHAR", "TYPE", "LABEL", "JUMP", "JUMPIFEQ",
                      "JUMPIFNEQ", "EXIT", "DPRINT", "BREAK"]


def collect_stats(params):
    '''
    Collect statistics from parameters and return them in a dictionary to maintain the order of the statistics parameters
        Args:
            params: list of parameters
        Returns:
            stats: dictionary of required statistics
    '''
    stats = {}
    current_file = None

    for param in params:
        if param.startswith("--stats="):
            current_file = param.split("=")[1]
            if current_file in stats.keys():
                print(f"Error 12: Duplicate --stats parameter", file=sys.stderr)
                sys.exit(12)
            stats[current_file] = []
        elif param.startswith("--print="):
            # Add a string to statistics
            if not current_file:
                print(f"Error 10: --stats parameter is missing before statistics parameters", file=sys.stderr)
                sys.exit(10)
            stats[current_file].append(["--print",param[8:]])
        elif param == "--eol":
            # Add a new line to statistics
            if not current_file:
                print(f"Error 10: --stats parameter is missing before statistics parameters", file=sys.stderr)
                sys.exit(10)
            stats[current_file].append(["--eol",""])
        elif param in ["--loc", "--comments", "--labels", "--jumps", "--fwjumps", "--backjumps", "--badjumps", "--frequent"]:
            if not current_file:
                print(f"Error 10: --stats parameter is missing before statistics parameters", file=sys.stderr)
                sys.exit(10)
            if param == "--frequent":
                stats[current_file].append(["--frequent"])
            else:
                stats[current_file].append([param])
        else:
            print(f"Error 10: Unknown parameter {param}", file=sys.stderr)
            sys.exit(10)
    return stats

def tokenize(code):
    '''
    Tokenize the code into a list of lists of tokens
        Args:
            code: code lines
        Returns:
            tokenized_lines: list of lists of tokens
    '''
    lines = code.split("\n")
    tokenized_lines = []
    for line in lines:
        line_tokens = line.split()
        tokenized_lines.append(line_tokens)
    return tokenized_lines

def code_to_xml(tokenized_lines):
    '''
    Transform the tokenized code into an XML tree
        Args:
            tokenized_lines: list of lists of tokens
        Returns:
            root: XML tree
    '''
    root = ET.Element("program", language="IPPcode24")
    for i, tokens in enumerate(tokenized_lines, start=1):    
        opcode = tokens[0].upper()
        instruction = ET.SubElement(root, "instruction", order=str(i), opcode=opcode)
        for idx, token in enumerate(tokens[1:], start=1):
            if "@" in token:
                if token.startswith("GF") or token.startswith("LF") or token.startswith("TF"):
                    type = "var"
                else:
                    type, token = token.split("@", 1)
                    if not token:
                        # For empty string
                        token = ""
            elif token == "int" or token == "bool" or token == "string":
                if opcode in ["CALL", "LABEL" , "JUMP"]:
                    # To avoid confusion with label and type
                    type = "label"
                else:
                    type = "type"   
            else:
                type = "label"
            arg = ET.SubElement(instruction, f"arg{idx}", type=type)
            arg.text = token
    return ET.ElementTree(root)

def delete_not_instructions(tokenized_lines):
    '''
    Delete all comments and empty lines from the tokenized code
        Args:
            tokenized_lines: list of lists of tokens
        Returns:
            cleaned_list: list of lists of tokens without comments and empty lines
    '''
    cleaned_list = []
    for tokens in tokenized_lines:
        cleaned_sublist = []
        for token in tokens:
            if "#" in token:
                # Separate the comment from the rest of the line
                token = token.split("#")[0]
                cleaned_sublist.append(token)
                break
            if token[0] == "#":
                break
            cleaned_sublist.append(token)
        # Remove empty strings
        cleaned_sublist = [token.strip() for token in cleaned_sublist if token.strip()]
        if cleaned_sublist:
            cleaned_list.append(cleaned_sublist)
    return cleaned_list

def define_stats(code):
    '''
    Define the statistics dictionary and initialize it with zeros and already conunts comments
        Args:
            code: code lines
        Returns:
            statistics: dictionary of all statistics
    '''
    statistics = {
        "--loc": 0,
        "--comments": 0,
        "--labels": 0,
        "--jumps": 0,
        "--fwjumps": 0,
        "--backjumps": 0,
        "--badjumps": 0,
        "--frequent": collections.Counter(),
    }
    
    for line in code:
        if "#" in line:
            statistics["--comments"] += 1
    return statistics

def is_valid_variable_identifier(identifier):
    '''
    Check if the variable identifier is valid
        Args:
            identifier: variable identifier
        Returns:
            True if the variable identifier is valid, False otherwise
    '''
    parts = identifier.split('@')
    if len(parts) != 2:
        # Contain more than one @
        return False
    memory_frame, variable_name = parts
    return memory_frame in ["GF", "LF", "TF"] and is_valid_variable_name(variable_name)


def is_valid_constant(constant):
    '''
    Check if the constant is valid
        Args:
            constant: constant
        Returns:
            True if the constant is valid, False otherwise
    '''
    if constant.startswith("int@"):
        if re.match(r"^[-+]?[0-9]+$", constant[4:]) is not None:
            # Check if the number is in the correct format - integer
            return True
        elif re.match(r"^[-+]?0x[0-9A-Fa-f]+$", constant[4:]) is not None:
            # Check if the number is in the correct format - hexadecimal
            return True
        elif re.match(r"^[-+]?0o[0-7]+$", constant[4:]) is not None:
            # Check if the number is in the correct format - octal
            return True
        return False
    if constant.startswith("bool@"):
        return constant[5:] in ["true", "false"]
    if constant.startswith("string@"):
        return is_valid_string(constant[7:])
    if constant.startswith("nil@"):
        return constant[4:] == "nil"
    return False

def is_valid_string(string):
    '''
    Check if the string is valid
        Args:
            string: string
        Returns:
            True if the string is valid, False otherwise
    '''
    if not string:
        # Empty string
        return True
    if ('"' in string or '#' in string):
        return False
    
    indexes = []
    index = -1
    while True:
        index = string.find("\\", index + 1)
        if index == -1:
            # No more backslashes
            break
        indexes.append(index)
    if not indexes:
        return True
    for index in indexes:
        if index + 3 > len(string):
            # After backslash cannot be less than 3 characters
            return False
        elif not re.match(r'\\[0-9]{3}$', string[index:index + 4]):
            # After backslash must be 3 digits
            return False
        else:
            continue
    return True

def is_valid_variable_name(name):
    '''
    Check if the variable name is valid
        Args:
            name: variable name
        Returns:
            True if the variable name is valid, False otherwise
    '''
    pattern = r"^[A-Za-z_\-&%*$!?][A-Za-z0-9_\-&%*$!?]*$"
    return re.match(pattern, name) is not None

def is_valid_symbol(symbol):
    '''
    Check if the symbol is valid
        Args:
            symbol: symbol
        Returns:
            True if the symbol is valid, False otherwise
    '''
    return is_valid_variable_identifier(symbol) or is_valid_constant(symbol)

def is_valid_type(type):
    '''
    Check if the type is valid
        Args:
            type: type
        Returns:
            True if the type is valid, False otherwise
    '''
    return type in ["int", "bool", "string", "nil"]

def is_valid_instruction(tokens):
    '''
    Check if the instruction is valid
        Args:
            tokens: list of tokens representing the instruction
        Returns:
            True if the instruction is valid, False otherwise
    '''
    opcode = tokens[0].upper()
    if opcode == ".IPPCODE24":
        return False
    if opcode not in OPCODES:
        print(f"Error 22: Unknown or incorrect opcode {opcode} in the source code", file=sys.stderr)
        sys.exit(22)    
    if opcode in ["CREATEFRAME", "PUSHFRAME", "POPFRAME", "RETURN", "BREAK"]:
        # No arguments
        return len(tokens) == 1
    elif opcode in ["DEFVAR", "CALL", "PUSHS", "POPS", "WRITE", "LABEL", "JUMP", "EXIT", "DPRINT"]:
        if (len(tokens) == 2):
            match opcode:
                case "DEFVAR" | "POPS":
                    # One argument - variable
                    return is_valid_variable_identifier(tokens[1])
                case "CALL" |"LABEL" | "JUMP":
                    # One argument - label
                    return is_valid_variable_name(tokens[1])
                case "PUSHS" | "WRITE" | "EXIT" | "DPRINT":
                    # One argument - symbol
                    return is_valid_symbol(tokens[1])
    elif opcode in ["MOVE", "INT2CHAR", "READ", "STRLEN", "TYPE", "NOT"]:
        if (len(tokens) == 3):
            match opcode:
                case "MOVE"|"INT2CHAR"|"STRLEN"|"TYPE"| "NOT":
                    # Two arguments - variable and symbol
                    return is_valid_variable_identifier(tokens[1]) and is_valid_symbol(tokens[2])
                case "READ":
                    # Two arguments - variable and type
                    return is_valid_variable_identifier(tokens[1]) and is_valid_type(tokens[2])
    else:
        if (len(tokens) == 4):
            if opcode in ["JUMPIFEQ", "JUMPIFNEQ"]:
                # Three arguments - label and two symbols
                return is_valid_variable_name(tokens[1]) and is_valid_symbol(tokens[2]) and is_valid_symbol(tokens[3])
            else:
                # Three arguments - variable and two symbols
                return is_valid_variable_identifier(tokens[1]) and is_valid_symbol(tokens[2]) and is_valid_symbol(tokens[3])
    return False

def set_stats(tokenized_lines, stats):
    '''
    Set the statistics dictionary with the required values
        Args:
            tokenized_lines: list of lists of tokens
            stats: dictionary of all statistics
        Returns:
            stats: dictionary of all statistics filled with values
    '''
    exist_labels = []
    possible_fwjumps = []
    for tokens in tokenized_lines:
        opcode = tokens[0].upper()
        stats["--loc"] += 1
        stats["--frequent"][opcode] += 1
        if opcode == "LABEL":
            exist_labels.append(tokens[1])
        if opcode in ["CALL", "JUMP", "JUMPIFEQ", "JUMPIFNEQ"]:
            stats["--jumps"] += 1
            if tokens[1] in exist_labels:
                stats["--backjumps"] += 1
            else:
                possible_fwjumps.append(tokens[1])
    stats["--labels"] = len(set(exist_labels))
    for label in possible_fwjumps:
        if label in exist_labels:
            stats["--fwjumps"] += 1
        else:
            stats["--badjumps"] += 1
    return stats
        
def print_stats(stats, arg_stats):
    '''
    Print the statistics to the files
        Args:
            stats: dictionary of all statistics with values
            arg_stats: dictionary of required statistics
    '''
    for file_name, file_stats in arg_stats.items():
        with open(file_name, "w") as file:
            if file_stats:
                for stat in file_stats:
                    if stat[0] == "--print":
                        file.write(f"{stat[1]}\n")
                    elif stat[0] == "--eol":
                        file.write("\n")
                    elif stat[0] == "--frequent":
                        frequent_opcodes = [opcode for opcode, count in stats["--frequent"].items() if count == max(stats["--frequent"].values())]
                        file.write(",".join(sorted(frequent_opcodes)))
                        file.write("\n")
                    else:
                        file.write(f"{stats[stat[0]]}\n")


if __name__ == "__main__":
    # Flag for check if the script was run with the --stats parameter
    flag_stats = False
    if len(sys.argv) == 2 and sys.argv[1] == "--help":
        print("This script is a filter type (parse.py in Python 3.10) that reads the source code in IPPcode24 from standard input, checks the lexical and syntactic correctness of the code, and outputs XML to standard output.\n Usage: python parse.py < input_file.src > output.xml")
        sys.exit(0)
    if len(sys.argv) != 1:
        arg_stats = collect_stats(sys.argv[1:])
        flag_stats = True

    input_code = sys.stdin.read()
    if not input_code:
        print("Error 21: Incorrect or missing header in the source code.", file=sys.stderr)
        sys.exit(21)
    
    tokenized_lines = tokenize(input_code)
    tokenized_lines = delete_not_instructions(tokenized_lines)
    
    # Check if the first line is .IPPcode24
    if tokenized_lines[0][0] != ".IPPcode24":
        print("Error 21: Incorrect or missing header in the source code.", file=sys.stderr)
        sys.exit(21)
    # Remove the first element (.IPPcode24) from tokenized_lines
    tokenized_lines = tokenized_lines[1:]      
        
    if not all(is_valid_instruction(line) for line in tokenized_lines):
        print("Error 23: Lexical or syntactic error in the source code.", file=sys.stderr)
        sys.exit(23)
        
    # Collect statistics and write them to the files
    if flag_stats:
        stats = define_stats(input_code)
        stats = set_stats(tokenized_lines, stats)
        print_stats(stats, arg_stats)

    # Transform the tokenized code into an XML tree and print it to the standard output
    xml_output = code_to_xml(tokenized_lines)
    ET.indent(xml_output, space="\t", level=0)
    xml_output.write(sys.stdout.buffer, encoding='UTF-8', xml_declaration=True)
    
    
    