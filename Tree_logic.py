import Tree_building_logic as TBL

# Returns 1/2^depth "weight" value for any node in the tree.
def apply_weight(node, tier=0):
    if isinstance(node, TBL.Root):
        # If given node is the root, return the weight as given below:
        return 1/(2**tier)
    if not node: 
        return 0
    if isinstance(node, TBL.NonTerminalNode) and not node.exist:
        # Return weight 0 for pruned-subtree roots.
        return 0
    # Recursively "climb" from given node to root, increasing 'tier' on each call.
    return apply_weight(node.parent, tier+1)
    
# Finds and returns a given node by the feature name.
def find_node(tree, name):
    stack = [tree.root]
    while stack:
        current = stack.pop() 
        node_name = getattr(current, 'feature', getattr(current, 'name', None))
        if node_name == name:
            return current
        # If the node has valid children, add them all to the stack
        if hasattr(current, 'children') and current.children:
            stack.extend(current.children)
    # Return None if the node doesn't exist in the tree
    return None

# Applies a score between 0 and 1 to given feature, based on how well the features divides the inventory. 
def apply_score(inventory: list[TBL.Tree]):
    feature_counter = {}
    invalid_trees = 0
    if not inventory:
        # Empty inventory returns None
        return None
    for tree in inventory:
        # Iterates through all trees, finds given feature and increments the counter for every segment with the feature. 
        if not tree or not hasattr(tree, 'root'):
            invalid_trees += 1
            continue

        if tree.root.data.get("Consonantal") == 1:
            feature_counter["Consonantal"] = feature_counter.get("Consonantal", 0) + 1
        if tree.root.data.get("Sonorant") == 1:
            feature_counter["Sonorant"] = feature_counter.get("Sonorant", 0) + 1

        stack = [tree.root]
        while stack:
            current = stack.pop()
            name = getattr(current, 'feature', getattr(current, 'name', None))
            if isinstance(current, TBL.NonTerminalNode) and current.exist:
                feature_counter[name] = feature_counter.get(name, 0) + 1
            elif isinstance(current, TBL.TerminalNode) and int(current.value) == 1:
                feature_counter[name] = feature_counter.get(name, 0) + 1

            if hasattr(current, 'children') and current.children:
                    stack.extend(current.children)
        # Calculate and return the relation between segments with and without feature.
    valid = len(inventory)-invalid_trees
    balances = {}

    if valid == 0:
        return None
    
    for feature_name, count in feature_counter.items():
        score = count/valid
        balance = 1 - 2*abs(0.5 - score)
        balances[feature_name] = balance
    
    return balances

def get_cf(inventory, master_tree_root, all_feature_names):
    e1 = 0.01
    e2 = 0.0001
    costs = {}
    balances = apply_score(inventory)
    for feature in all_feature_names:
        if feature in ["Consonantal", "Sonorant"]:
            weight = 1.
        else:
            node = find_node(master_tree_root, feature)
            weight = apply_weight(node)
        balance = balances.get(feature, 0)
        C_f = 1 - (e1*weight) - (e2*balance)
        costs[feature] = C_f

    return costs

