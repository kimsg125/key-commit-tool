import re
from copy import deepcopy

def parse_round_function(func_str, state, block_names, ad_names, ad_counts, ad_start_index):
    expr = func_str.strip()
    # Replace state variables with their previous round values
    for block_index, state_block in enumerate(state):
        for state_var_index, state_var in enumerate(state_block):
            expr = expr.replace(f"{block_names[block_index]}{state_var_index}", state_var)
    
    # Replace associated data variables with their indexed values
    for i, (ad_name, ad_count) in enumerate(zip(ad_names, ad_counts)):
        for ad_num in range(ad_count):
            if f"{ad_name}{ad_num}" in expr:
                expr = expr.replace(f"{ad_name}{ad_num}", f"{ad_name}_{ad_start_index[i]}")
                ad_start_index[i] += 1
    
    return expr, ad_start_index

def generate_equations(round_functions, block_names, ad_names, ad_counts, num_blocks, num_rounds):
    # Initialize state variables for each block type
    state = []
    for block_name, count in zip(block_names, num_blocks):
        state.append([f"{block_name}_{i}" for i in range(count)])
    
    ad_start_index = [0] * len(ad_names)  # Initialize the starting index for each associated data type
    
    # Generate equations for each round
    for round_num in range(1, num_rounds + 1):
        new_state = [None] * sum(num_blocks)
        func_index = 0
        
        for block_type_index, block_name in enumerate(block_names):
            for block_index in range(num_blocks[block_type_index]):
                expr, ad_start_index = parse_round_function(round_functions[func_index], state, block_names, ad_names, ad_counts, ad_start_index)
                flat_index = sum(num_blocks[:block_type_index]) + block_index
                new_state[flat_index] = expr
                func_index += 1
        
        # Update the state with the new state for the next round
        state = []
        start_idx = 0
        for count in num_blocks:
            state.append(new_state[start_idx:start_idx + count])
            start_idx += count

    return new_state

def extract_variables(expression, block_names, ad_names):
    variables = set()
    parts = re.split(r'\+|\(|\)', expression)
    for part in parts:
        for name in block_names + ad_names:
            if part.startswith(name):
                variables.add(part)
    return variables

def remove_outer_A(expr):
    if expr.startswith("A(") and expr.endswith(")"):
        nested_level = 0
        for i, char in enumerate(expr[2:-1]):
            if char == '(':
                nested_level += 1
            elif char == ')':
                nested_level -= 1
            if nested_level == 0:
                return expr[2:-1]
    return expr

def remove_known_values(expr, known_values):
    parts = re.split(r'(\+|\(|\))', expr)
    new_parts = []
    nested_level = 0
    skip_next_plus = False

    for part in parts:
        if part == '(':
            nested_level += 1
        elif part == ')':
            nested_level -= 1
        
        if nested_level == 0 and part.strip() in known_values:
            skip_next_plus = True
            continue

        if skip_next_plus:
            skip_next_plus = False
            if part == '+':
                continue
        
        new_parts.append(part)

    new_expr = ''.join(new_parts).strip('+')
    return new_expr

def solve_equation(equations, known_values, unknown_values, block_names, ad_names):
    new_equations = []
    for eq in equations:
        if '=' in eq:
            lhs, rhs = eq.split('=')
            rhs = rhs.strip()
            new_equations.append(rhs)
        else:
            new_equations.append(eq.strip())

    simplified_equations = deepcopy(new_equations)
    
    for i, rhs in enumerate(simplified_equations):
        # While loop to repeatedly simplify the equation
        while True:
            old_rhs = rhs
            # Remove known values outside of A
            rhs = remove_known_values(rhs, known_values)
            # Remove outer A if present
            rhs = remove_outer_A(rhs)
            if rhs == old_rhs:
                break
        
        simplified_equations[i] = rhs
    
    single_unknown = []
    for i, rhs1 in enumerate(simplified_equations):
        for j, rhs2 in enumerate(simplified_equations):
            if i != j and rhs1 in rhs2:
                remaining = rhs2.replace(rhs1, '').strip()
                variables = extract_variables(remaining, block_names, ad_names)
                unknowns = variables & unknown_values
                if len(unknowns) == 1 and list(unknowns)[0] not in single_unknown:
                    single_unknown.append(list(unknowns)[0])

    return single_unknown

def analyze_security(equations, block_names, ad_names, num_blocks, ad_counts, num_rounds):
    known_values = set()
    unknown_values = set()
    
    # Initialize known values and unknown values
    for name in block_names:
        for i in range(num_blocks[block_names.index(name)]):
            known_values.add(f"{name}_{i}")
    
    for name in ad_names:
        for i in range(ad_counts[ad_names.index(name)] * num_rounds):
            unknown_values.add(f"{name}_{i}")
    
    num_before = len(known_values)
    
    while True:
        single_unknown = None
        for eq in equations:
            if '=' in eq:
                rhs = eq.split('=')[1].strip()
            else:
                rhs = eq.strip()
            variables = extract_variables(rhs, block_names, ad_names)
            unknowns = variables & unknown_values
            if len(unknowns) == 1:
                single_unknown = list(unknowns)[0]
                break
        
        if single_unknown:
            unknown_values.remove(single_unknown)
            known_values.add(single_unknown)
            continue
        
        solved_value = solve_equation(equations, known_values, unknown_values, block_names, ad_names)
        if len(solved_value) != 0:
            for value in solved_value:
                unknown_values.remove(value)
                known_values.add(value)
            continue
        
        break
    
    if not unknown_values:
        return 64 * (sum(num_blocks) - (len(known_values) - num_before))  # All unknowns resolved
    return unknown_values  # Return unresolved unknowns

def find_minimum_rounds(block_names, ad_names, num_blocks, ad_counts, round_functions):
    num_rounds = 1
    while True:
        equations = generate_equations(round_functions, block_names, ad_names, ad_counts, num_blocks, num_rounds)
        
        # Initialize unknown_values for the current num_rounds
        unknown_values = set()
        for name in ad_names:
            for i in range(ad_counts[ad_names.index(name)] * num_rounds):
                unknown_values.add(f"{name}_{i}")

        # Check if all equations contain at least one unknown value
        all_contain_unknown = all(any(var in extract_variables(eq, block_names, ad_names) for var in unknown_values) for eq in equations)

        if all_contain_unknown:
            return num_rounds
        
        num_rounds += 1

def analyze_security_with_guessing(equations, block_names, ad_names, num_blocks, ad_counts, num_rounds):
    known_values = set()
    unknown_values = set()
    
    # Initialize known values and unknown values
    for name in block_names:
        for i in range(num_blocks[block_names.index(name)]):
            known_values.add(f"{name}_{i}")
    
    for name in ad_names:
        for i in range(ad_counts[ad_names.index(name)] * num_rounds):
            unknown_values.add(f"{name}_{i}")
    
    while True:
        single_unknown = None
        for eq in equations:
            if '=' in eq:
                rhs = eq.split('=')[1].strip()
            else:
                rhs = eq.strip()
            variables = extract_variables(rhs, block_names, ad_names)
            unknowns = variables & unknown_values
            if len(unknowns) == 1:
                single_unknown = list(unknowns)[0]
                break
        
        if single_unknown:
            unknown_values.remove(single_unknown)
            known_values.add(single_unknown)
            continue
        
        solved_value = solve_equation(equations, known_values, unknown_values, block_names, ad_names)
        if len(solved_value) != 0:
            for value in solved_value:
                unknown_values.remove(value)
                known_values.add(value)
            continue
        
        change = 0
        if len(ad_names) == 3:
            for round_num in range(num_rounds):
                ad0 = f"{ad_names[0]}_{round_num}"
                ad1 = f"{ad_names[1]}_{round_num}"
                ad2 = f"{ad_names[2]}_{round_num}"
                if (ad0 in known_values and ad1 in known_values and ad2 not in known_values):
                    unknown_values.remove(ad2)
                    known_values.add(ad2)
                    change = 1
                elif (ad0 in known_values and ad2 in known_values and ad1 not in known_values):
                    unknown_values.remove(ad1)
                    known_values.add(ad1)
                    change = 1
                elif (ad1 in known_values and ad2 in known_values and ad0 not in known_values):
                    unknown_values.remove(ad0)
                    known_values.add(ad0)
                    change = 1
        if change == 1:
            continue
        
        break
    
    unknowns_before_guessing = sorted(list(unknown_values))
    print(f"Unknown values before guessing: {unknowns_before_guessing}")

    if not unknown_values:
        return unknowns_before_guessing, []
    
    min_depth = float('inf')
    best_guesses = []

    def recursive_guess(known_values, unknown_values, depth, current_guesses):
        nonlocal min_depth, best_guesses
        if not unknown_values:
            if depth < min_depth:
                min_depth = depth
                best_guesses = [current_guesses]
            elif depth == min_depth:
                best_guesses.append(current_guesses)
            return True
        
        for guess in sorted(unknown_values):
            new_known = known_values | {guess}
            new_unknown = unknown_values - {guess}
            
            while True:
                single_unknown = None
                for eq in equations:
                    if '=' in eq:
                        rhs = eq.split('=')[1].strip()
                    else:
                        rhs = eq.strip()
                    variables = extract_variables(rhs, block_names, ad_names)
                    unknowns = variables & new_unknown
                    if len(unknowns) == 1:
                        single_unknown = list(unknowns)[0]
                        break
                
                if single_unknown:
                    new_unknown.remove(single_unknown)
                    new_known.add(single_unknown)
                    continue
                
                solved_value = solve_equation(equations, new_known, new_unknown, block_names, ad_names)
                if len(solved_value) != 0:
                    for value in solved_value:
                        new_unknown.remove(value)
                        new_known.add(value)
                    continue
                
                change = 0
                if len(ad_names) == 3:
                    for round_num in range(num_rounds):
                        ad0 = f"{ad_names[0]}_{round_num}"
                        ad1 = f"{ad_names[1]}_{round_num}"
                        ad2 = f"{ad_names[2]}_{round_num}"
                        if (ad0 in new_known and ad1 in new_known and ad2 not in new_known):
                            new_unknown.remove(ad2)
                            new_known.add(ad2)
                            change = 1
                        elif (ad0 in new_known and ad2 in new_known and ad1 not in new_known):
                            new_unknown.remove(ad1)
                            new_known.add(ad1)
                            change = 1
                        elif (ad1 in new_known and ad2 in new_known and ad0 not in new_known):
                            new_unknown.remove(ad0)
                            new_known.add(ad0)
                            change = 1
                if change == 1:
                    continue
                
                break

            recursive_guess(new_known, new_unknown, depth + 1, current_guesses + [guess])
    
    recursive_guess(known_values, unknown_values, 0, [])
    if best_guesses:
        formatted_guesses = ' or '.join([f"[{', '.join(guess)}]" for guess in best_guesses])
        return unknowns_before_guessing, formatted_guesses
    return unknowns_before_guessing, []

