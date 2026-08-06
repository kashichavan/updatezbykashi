class AIExplainerEngine:
    """
    Beginner-Friendly AI Code Explainer & Teaching Engine.
    Generates structured, multi-dimensional pedagogical explanations for every code step:
    1. What Happened (Plain English)
    2. Why It Happened (Interpreter / Compiler mechanics)
    3. Memory & Stack Allocation (Stack vs Heap changes)
    4. Common Beginner Pitfalls & How to Avoid Them
    """

    @staticmethod
    def explain_step(line_text, line_number, variables_dict, event_type, language="python"):
        line_text = (line_text or "").strip()

        what_happened = f"Executing line {line_number}: '{line_text}'."
        why_it_happened = "The interpreter reads source code sequentially top-to-bottom."
        memory_change = "Memory state remains unchanged at this step."
        common_pitfall = "Ensure variable names match exact casing (Python is case-sensitive)."

        # 1. Variable Assignment / Declaration
        if '=' in line_text and not line_text.startswith('if') and not line_text.startswith('while'):
            parts = line_text.split('=', 1)
            var_name = parts[0].replace('let', '').replace('const', '').replace('var', '').replace('int', '').strip()
            val_expr = parts[1].strip()

            what_happened = f"Created or updated variable '{var_name}' with value `{val_expr}`."
            why_it_happened = f"The expression on the right-side (`{val_expr}`) was evaluated first, and the resulting value was bound to name '{var_name}'."
            memory_change = f"A slot was allocated in the active Stack Frame for '{var_name}'. Reference pointer stored."
            common_pitfall = f"Remember: '=' is assignment, while '==' compares equality!"

        # 2. Loop Iteration (for / while)
        elif line_text.startswith('for ') or line_text.startswith('while '):
            what_happened = f"Evaluating loop condition: '{line_text}'."
            why_it_happened = "Loops repeat a block of code as long as the loop condition evaluates to True."
            memory_change = "The loop counter variable is updated in the active Stack Frame."
            common_pitfall = "Watch out for Infinite Loops! Always ensure the loop variable changes toward the termination condition."

        # 3. Function Call
        elif '(' in line_text and ')' in line_text and not line_text.startswith('def ') and not line_text.startswith('function '):
            what_happened = f"Invoking function call: '{line_text}'."
            why_it_happened = "Execution temporarily pauses in the current function and jumps into the called function's body."
            memory_change = "A new Stack Frame is pushed onto the Call Stack to store the function's local variables and arguments."
            common_pitfall = "Make sure you pass the correct number of required parameters to the function!"

        # 4. Return Statement
        elif line_text.startswith('return '):
            ret_val = line_text.replace('return', '').strip()
            what_happened = f"Returning value `{ret_val}` back to the caller."
            why_it_happened = "The function has completed its task and yields control back to where it was invoked."
            memory_change = "The function's Stack Frame is popped off the Call Stack and destroyed in memory."
            common_pitfall = "Code placed after a 'return' statement inside a function will NEVER execute (Unreachable Code)!"

        return {
            'what_happened': what_happened,
            'why_it_happened': why_it_happened,
            'memory_change': memory_change,
            'common_pitfall': common_pitfall
        }
