class StepController:
    """
    Debugger Step Navigation & Breakpoint Controller.
    Implements VS Code / Chrome DevTools execution control logic:
    - Step Over
    - Step Into
    - Step Out
    - Continue to Breakpoint
    """

    @staticmethod
    def get_step_over_target(steps, current_idx):
        """Calculates the target step index for Step Over in current call stack depth."""
        if not steps or current_idx >= len(steps) - 1:
            return current_idx

        curr_depth = len(steps[current_idx].get('stack_frames', []))
        next_idx = current_idx + 1

        while next_idx < len(steps):
            step_depth = len(steps[next_idx].get('stack_frames', []))
            if step_depth <= curr_depth:
                return next_idx
            next_idx += 1

        return len(steps) - 1

    @staticmethod
    def get_step_out_target(steps, current_idx):
        """Calculates the target step index for Step Out (returning to parent stack frame)."""
        if not steps or current_idx >= len(steps) - 1:
            return current_idx

        curr_depth = len(steps[current_idx].get('stack_frames', []))
        next_idx = current_idx + 1

        while next_idx < len(steps):
            step_depth = len(steps[next_idx].get('stack_frames', []))
            if step_depth < curr_depth:
                return next_idx
            next_idx += 1

        return len(steps) - 1

    @staticmethod
    def get_continue_target(steps, current_idx, breakpoints):
        """Calculates target step index for Continue (fast-forwarding to next breakpoint)."""
        if not steps or current_idx >= len(steps) - 1:
            return current_idx

        bp_set = set(breakpoints or [])
        next_idx = current_idx + 1

        while next_idx < len(steps):
            step_line = steps[next_idx].get('line_number')
            if step_line in bp_set or steps[next_idx].get('is_breakpoint'):
                return next_idx
            next_idx += 1

        return len(steps) - 1
