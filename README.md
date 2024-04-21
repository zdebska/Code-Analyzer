## Documentation of Project Implementation for for the 1. task IPP 2023/2024
## Name and surname: Kateryna Zdebska
## Login: xzdebs00

### Task
The script of type filter reads from the standard input the source code in IPPcode24, checks the lexical and syntactic validity of the code and prints the XML representation of the program to the standard output.

### Implementation:
The script represents IPPcode24 source code as tokenized lines. Each line is broken down into tokens, which are then processed and analyzed to perform various tasks such as stripping the from unnecessary characters, syntax validation and statistics counting. Collecting statistics was  The script utilizes data structures such as lists and dictionaries to store and manipulate tokenized code, statistics, and other relevant information.

### Functionality:
My solution starts by checking the arguments given when running the program. If there any for statistics, i save them as dictionary for future use, because the record files for each statistic can be different, so it is important to save the order and belonging to the files correctly.

Then program split the code given in standart input into lists of tokens. Each list represents code line. Parser also delete all comments, empty strings and header for lexical and syntactic analysis of the remaining tokens - instructions.  

The main function for checking instructions `is_valid_instruction(tokens)` divides them into 4 categories depending on the number of arguments according to the rules of the IPPcode24 language. After that the operand set is checked for correspondence to the operating code of the instruction. Subsequently, the operands themselves are checked against a variable, symbol or label. Constants, variables or label names are checked for lexical errors.

Depending on the incoming arguments, the program may or may not compute the statistics and print it in the correct format and files.

As a last step, the program converts the tokens into an XML tree and then prints it to the standard output.

### Features
1. I used regexes in most of my lexical checks. But while checking strings in function `is_valid_string(string)` I ran into a problem that they can contain backslash, but only if it is an escape sequence. For this check I didn't manage to use regex, so I found all indexes where backslashes were in strings and checked 3 characters after them, assuming that the index of the backslash was not further than 3 characters from the end of the string. In this case it meant that it couldn't be an escape sequence because it must contain exactly three characters. So the string check function returned false.
2. During conversion of tokens to xml in function `code_to_xml(tokenized_lines)` it was necessary to define the type of arguments in the instruction. But due to the context dependency there could be confusion when token was "int" "bool" or "string". In this case, the argument type could be either a label or a type. In order to understand which of these was a type, we had to check the operation code of instruction.
```
elif token == "int" or token == "bool" or token == "string":
    if opcode in ["CALL", "LABEL" , "JUMP"]:
        # To avoid confusion with label and type
        type = "label"
    else:
        type = "type"
```
4. While collecting statistics when tokens were passed once, it was impossible to determine whether the jump was forward or undefined. 

```
if tokens[1] in exist_labels: 
    stats["--backjumps"] += 1
else:
    possible_fwjumps.append(tokens[1])
```

Therefore, I had to save all existing labels for later verification of those jumps whose completeness could not be determined 

```
for label in possible_fwjumps:
    if label in exist_labels:
        stats["--fwjumps"] += 1
    else:
        stats["--badjumps"] += 1
```

