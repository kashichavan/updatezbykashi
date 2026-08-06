class HeapMemoryVisualizer:
    """
    Heap Memory & Object Reference Graph Inspector.
    Visualizes Stack-to-Heap references, pointer arrows, and Garbage Collection states.
    """

    @staticmethod
    def build_heap_graph(variables_dict):
        """
        Parses variables dictionary at a specific step and constructs:
        - Stack References (Pointer arrows connecting stack variables to heap nodes)
        - Heap Nodes (Lists, Dictionaries, Objects with indexed memory slots)
        - Reference Counts (Objects with 0 references marked for Garbage Collection)
        """
        stack_refs = []
        heap_nodes = {}
        ref_counts = {}

        for var_name, var_info in (variables_dict or {}).items():
            mem_id = var_info.get('mem_addr', '0x0')
            val = var_info.get('value')
            is_primitive = var_info.get('is_primitive', True)
            var_type = var_info.get('type', 'object')

            if is_primitive:
                # Primitive value stored directly in Stack Frame
                stack_refs.append({
                    'var_name': var_name,
                    'is_heap_ref': False,
                    'type': var_type,
                    'value': str(val),
                    'target_mem_id': mem_id
                })
            else:
                # Reference Object allocated on Heap
                stack_refs.append({
                    'var_name': var_name,
                    'is_heap_ref': True,
                    'type': var_type,
                    'target_mem_id': mem_id
                })

                ref_counts[mem_id] = ref_counts.get(mem_id, 0) + 1

                if mem_id not in heap_nodes:
                    heap_nodes[mem_id] = {
                        'id': mem_id,
                        'type': var_type,
                        'data': val,
                        'ref_count': ref_counts[mem_id]
                    }
                else:
                    heap_nodes[mem_id]['ref_count'] = ref_counts[mem_id]

        # Detect Garbage Collection Candidates (Heap items with 0 references)
        gc_candidates = [node_id for node_id, node in heap_nodes.items() if node['ref_count'] == 0]

        return {
            'stack_references': stack_refs,
            'heap_nodes': list(heap_nodes.values()),
            'gc_candidates': gc_candidates
        }
