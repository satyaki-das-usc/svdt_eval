import re
from typing import List

replacement_dict = {
    "good": {
        "good": "unk",
        "Good": "Unk"
    },
    "bad": {
        "bad": "unk",
        "Bad": "Unk"
    }
}

reverse_replacement_dict = {
    "good": {
        "good": "unk2",
        "Good": "Unk2"
    },
    "bad": {
        "bad": "unk2",
        "Bad": "Unk2"
    }
}

# keywords up to C11 and C++17; immutable set
keywords = frozenset({
    '__asm', '__builtin', '__cdecl', '__declspec', '__except', '__export',
    '__far16', '__far32', '__fastcall', '__finally', '__import', '__inline',
    '__int16', '__int32', '__int64', '__int8', '__leave', '__optlink',
    '__packed', '__pascal', '__stdcall', '__system', '__thread', '__try',
    '__unaligned', '_asm', '_Builtin', '_Cdecl', '_declspec', '_except',
    '_Export', '_Far16', '_Far32', '_Fastcall', '_finally', '_Import',
    '_inline', '_int16', '_int32', '_int64', '_int8', '_leave', '_Optlink',
    '_Packed', '_Pascal', '_stdcall', '_System', '_try', 'alignas', 'alignof',
    'and', 'and_eq', 'asm', 'auto', 'bitand', 'bitor', 'bool', 'break', 'case',
    'catch', 'char', 'char16_t', 'char32_t', 'class', 'compl', 'const',
    'const_cast', 'constexpr', 'continue', 'decltype', 'default', 'delete',
    'do', 'double', 'dynamic_cast', 'else', 'enum', 'explicit', 'export',
    'extern', 'false', 'final', 'float', 'for', 'friend', 'goto', 'if',
    'inline', 'int', 'long', 'mutable', 'namespace', 'new', 'noexcept', 'not',
    'not_eq', 'nullptr', 'operator', 'or', 'or_eq', 'override', 'private',
    'protected', 'public', 'register', 'reinterpret_cast', 'return', 'short',
    'signed', 'sizeof', 'static', 'static_assert', 'static_cast', 'struct',
    'switch', 'template', 'this', 'thread_local', 'throw', 'true', 'try',
    'typedef', 'typeid', 'typename', 'union', 'unsigned', 'using', 'virtual',
    'void', 'volatile', 'wchar_t', 'while', 'xor', 'xor_eq', 'NULL'
})

# holds known non-user-defined functions; immutable set
main_set = frozenset({'main'})
# arguments in main function; immutable set
main_args = frozenset({'argc', 'argv'})

def clean_gadget(gadget: List[str]):
    """
    change a list of code statements to their symbolic representations
    Args:
        gadget: a list of code statements

    Returns:

    """
    # dictionary; map function name to symbol name + number
    fun_symbols = {}
    # dictionary; map variable name to symbol name + number
    var_symbols = {}

    fun_count = 1
    var_count = 1

    # regular expression to catch multi-line comment
    # rx_comment = re.compile('\*/\s*$')
    # regular expression to find function name candidates
    rx_fun = re.compile(r'\b([_A-Za-z]\w*)\b(?=\s*\()')
    # regular expression to find variable name candidates
    # rx_var = re.compile(r'\b([_A-Za-z]\w*)\b(?!\s*\()')
    rx_var = re.compile(
        r'\b([_A-Za-z]\w*)\b(?:(?=\s*\w+\()|(?!\s*\w+))(?!\s*\()')

    # final cleaned gadget output to return to interface
    cleaned_gadget = []

    for line in gadget:
        # process if not the header line and not a multi-line commented line
        # if rx_comment.search(line) is None:
        # remove all string literals (keep the quotes)
        nostrlit_line = re.sub(r'".*?"', '""', line)
        # remove all character literals
        nocharlit_line = re.sub(r"'.*?'", "''", nostrlit_line)
        # replace any non-ASCII characters with empty string
        ascii_line = re.sub(r'[^\x00-\x7f]', r'', nocharlit_line)

        # return, in order, all regex matches at string list; preserves order for semantics
        user_fun = rx_fun.findall(ascii_line)
        user_var = rx_var.findall(ascii_line)

        # Could easily make a "clean gadget" type class to prevent duplicate functionality
        # of creating/comparing symbol names for functions and variables in much the same way.
        # The comparison frozenset, symbol dictionaries, and counters would be class scope.
        # So would only need to pass a string list and a string literal for symbol names to
        # another function.
        for fun_name in user_fun:
            if len({fun_name}.difference(main_set)) != 0 and len({fun_name}.difference(keywords)) != 0:
                # DEBUG
                # print('comparing ' + str(fun_name + ' to ' + str(main_set)))
                # print(fun_name + ' diff len from main is ' + str(len({fun_name}.difference(main_set))))
                # print('comparing ' + str(fun_name + ' to ' + str(keywords)))
                # print(fun_name + ' diff len from keywords is ' + str(len({fun_name}.difference(keywords))))
                ###
                # check to see if function name already in dictionary
                if fun_name not in fun_symbols.keys():
                    fun_symbols[fun_name] = 'FUN' + str(fun_count)
                    fun_count += 1
                # ensure that only function name gets replaced (no variable name with same
                # identifier); uses positive lookforward
                ascii_line = re.sub(r'\b(' + fun_name + r')\b(?=\s*\()',
                                    fun_symbols[fun_name], ascii_line)

        for var_name in user_var:
            # next line is the nuanced difference between fun_name and var_name
            if len({var_name}.difference(keywords)) != 0 and len({var_name}.difference(main_args)) != 0:
                # DEBUG
                # print('comparing ' + str(var_name + ' to ' + str(keywords)))
                # print(var_name + ' diff len from keywords is ' + str(len({var_name}.difference(keywords))))
                # print('comparing ' + str(var_name + ' to ' + str(main_args)))
                # print(var_name + ' diff len from main args is ' + str(len({var_name}.difference(main_args))))
                ###
                # check to see if variable name already in dictionary
                if var_name not in var_symbols.keys():
                    var_symbols[var_name] = 'VAR' + str(var_count)
                    var_count += 1
                # ensure that only variable name gets replaced (no function name with same
                # identifier); uses negative lookforward
                ascii_line = re.sub(
                    r'\b(' + var_name +
                    r')\b(?:(?=\s*\w+\()|(?!\s*\w+))(?!\s*\()',
                    var_symbols[var_name], ascii_line)

        cleaned_gadget.append(ascii_line)
    # return the list of cleaned lines
    return "".join(cleaned_gadget)

def get_delabeled_processed_func(gadget: List[str], label_text):
    rev_label_text = "bad" if label_text == "good" else "good"
    
    delabeled_gadget = [] + gadget
    for key, value in replacement_dict[label_text].items():
        for i in range(len(delabeled_gadget)):
            delabeled_gadget[i] = delabeled_gadget[i].replace(key, value)
    for key, value in reverse_replacement_dict[rev_label_text].items():
        for i in range(len(delabeled_gadget)):
            delabeled_gadget[i] = delabeled_gadget[i].replace(key, value)
    
    return "".join(delabeled_gadget)

def replace_leading_spaces_with_tabs(gadget: List[str], tab_width=2):
    result = []

    for line in gadget:
        leading_spaces = len(line) - len(line.lstrip())
        tabs = leading_spaces // tab_width
        spaces = leading_spaces % tab_width
        result.append("\t" * tabs + " " * spaces + line.lstrip())

    return "".join(result)

if __name__ == "__main__":
    print("No main function implemented.")