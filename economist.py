import re
import pulp
import Tree_building_logic as TBL
import Tree_logic as TL
import Data_normalization as dn

class IdenticalSegmentsError(Exception):
    """Raised when two segments have identical feature matrices."""
    pass

# Creates a list of all relevant features (+categories, e.g 'Laryngeal')
def get_all_features(master_root:TBL.Root):
    ftrlst = set() 
    strclst = set()
    # Recursively climbs down the tree and adds every feature name to the set. 
    def helper(node):
        if not node or node is None:
            return 
        if not isinstance(node, TBL.Root):
            ftrlst.add(node.feature)
        if node.children:
            for i in node.children:
                helper(i)
            if not isinstance(node, TBL.Root):
                strclst.add(node.feature)
        
        return ftrlst
    if not isinstance(master_root, TBL.Root):
        cont = input("adding a non-root node will result in a partial list of the features of the given subtree only. \n" \
        "in turn, such a list will crash an unaltered application when attempting to run. continue? y/n :")
        if cont == 'n':
            return 
    helper(master_root)
    # Add the root features to the set. 
    for key in master_root.data.keys():
        ftrlst.add(key)

    return (list(ftrlst), list(strclst))

# Cleans input into a set of unique IPA chars.
def input_inv(u_seg : str):
    l_seg = [seg for seg in re.split(r"[,\s]+", u_seg) if seg in dn.ipa_list]
    l_seg = list(set(l_seg))
    conmap = dn.load_conversion_map_manual("./data/conversion_dict.txt")
    l_seg = dn.normalize_and_deduplicate(l_seg, conmap)
    return l_seg, u_seg

def pair_up(l_seg):
##  creates a list of all possible pairs from the input_inv() func
    pairs = []
    for i in range(len(l_seg)):
        for p in range(i + 1, len(l_seg)):
            pairs.append([l_seg[i], l_seg[p]])
    return pairs

def get_feature_val(tree, feature_name):
    # Handle the Root-level dictionary features
    if feature_name in ["Consonantal", "Sonorant", "syllabic"]:
        return tree.root.data.get(feature_name)
    # Check for the Terminal Node's value
    node = TL.find_node(tree, feature_name)
    if node and hasattr(node, 'value'):
        if node.value == 1:
            return 1
    return 0

def feature_economist(df = dn.df, l_seg = None):
    ALLFEATURES = get_all_features(TBL.TREE1.root)
    all_feature_names = ALLFEATURES[0]
    # Define the problem as a minimization problem. 
    prob = pulp.LpProblem(name = "minimize-set", sense = pulp.LpMinimize)
    master = TBL.TREE1
    tree_inventory = [TBL.build_tree_by_symbol(sym, df) for sym in l_seg]
    pairs = pair_up(tree_inventory)
    costs = TL.get_cf(tree_inventory, master, all_feature_names)
    # Structural nodes (non-leaves) are not considered for the minimal set as they do not directly represent discrete features. 
    structural_nodes = ALLFEATURES[1]
    selectable_features = [f for f in all_feature_names if f not in structural_nodes]
    X = pulp.LpVariable.dicts("Feat", selectable_features, cat=pulp.LpBinary)
    prob += pulp.lpSum([costs[f] * X[f] for f in selectable_features]), "Total_Cost"
    
    consonant_terminals = [
        "approximant", "continuant", "nasal",
        "spreadGlottis", "constrictedGlottis", "fortis", 
        "loweredLarynxImplosive", "raisedLarynxEjective", "voiced",
        "epilaryngealSource", "retractedTongueRoot", "advancedTongueRoot",
        "click", "tap", "trill", "delayedRelease",
        "labiodental", "anterior", "distributed", "lateral", "strident"
    ]
    for feat in consonant_terminals:
        if feat in X and "Consonantal" in X:
            prob += X[feat] <= X["Consonantal"], f"RootTax_{feat}"

    vowel_terminals = [
        "round", "front", "high", "low", "back", "tense", 
        "long", "short"
    ]
    for feat in vowel_terminals:
        if feat in X and "Sonorant" in X:
            prob += X[feat] <= X["Sonorant"], f"RootTax_{feat}"

    for tree_a, tree_b in pairs:
        distinguishing_features = []
        for feature in selectable_features:
            if feature == "MASTER":
                continue
            val_a = get_feature_val(tree_a, feature)
            val_b = get_feature_val(tree_b, feature)
            if val_a != val_b:
                distinguishing_features.append(feature)
        if distinguishing_features:
            rule_name = f"Distinguish_{tree_a.root.name}_from_{tree_b.root.name}"
            prob += pulp.lpSum([X[f] for f in distinguishing_features]) >= 1, rule_name      
        else: 
            print(tree_a.root.name, tree_b.root.name)
            raise IdenticalSegmentsError
    
    prob.solve()
    status = pulp.LpStatus[prob.status]
    print(f"Solver Status: {status}")
    if status != 'Optimal':
        print("Warning: Could not find an optimal solution!")
        return None
    minimal_set = []
    for feature in selectable_features:
        if feature == "MASTER":
            continue
        if X[feature].varValue and X[feature].varValue > 0.5:
            minimal_set.append(feature)

    return (minimal_set, len(minimal_set))


def create_dicts(l_seg, all_feature_names = get_all_features(TBL.TREE1.root)[0]):
## creates list of dictionaries with negation or confirmation of features for each letter in input_inv()'s input
    dicts_feats = []
    for seg in l_seg:
        current_df = dn.df[dn.df[dn.SEGMENT_ID_COL] == seg]
        selected_cols = [dn.SEGMENT_ID_COL] + [col for col in all_feature_names if col in current_df.columns]
        current_df = current_df[selected_cols]
        dicts_feats.extend(current_df.to_dict('records'))
    return dicts_feats