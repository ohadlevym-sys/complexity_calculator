import re
import pandas as pd
from pulp import LpProblem, LpMinimize, LpVariable, lpSum, PULP_CBC_CMD
import numpy as np

df_par = pd.read_csv("C:/Users/Ohadl/OneDrive/Desktop/App/python/API_features_set.csv")
df_lang = pd.read_csv("C:/Users/Ohadl/OneDrive/Desktop/App/phoible/cldf-datasets-phoible-f36deac/cldf/languages.csv")
df_val = pd.read_csv("C:/Users/Ohadl/OneDrive/Desktop/App/phoible/cldf-datasets-phoible-f36deac/cldf/values.csv")

cols_to_keep = [
    "voiced", "vowel", "consonant", "Affricate",
    "lateral", "Plosive", "Fricative", "Nasal", "Approximant", "Postalveolar", "Velar", "Bilabial",
    "Alveolar","Ejective", "primary stress", "Dental", "Aspirated", "Labialized", "Palatalized", "Velarized",
    "Pharyngealized", "Caron", "Retroflex", "Palatal", "Long", "Double_Long", "Extra-long", "long", "Retracted",
    "Tie_Bar","Fortis (Strong)", "Nasalized", "Raised", "Lowered", "Glottal", "Extra-short", "Uvular",
    "Pharyngeal", "Labio-dental", "close", "close-mid", "open-mid", "open", "front", "central", "back",
    "round", "Near-close", "Near-open", "Mid", "Brackets/Noise", "Geminate", "Velarized_Overlay",
]

ipa_list = df_par["NAME"].astype(str).tolist()

SEGMENT_ID_COL = 'NAME'
        
def input_inv(u_seg : str):
    ## cleans input into a list of IPA chars only, no duplicates
    l_seg = [seg for seg in re.split(r"[,\s]+", u_seg) if seg in ipa_list]
    l_seg = list(set(l_seg))
    return l_seg, u_seg

def append_input_dict(input_dict, curr_input, input_counter, name_from_ui):
    """Appends current inventory to dict with a name or counter."""
    key = name_from_ui if name_from_ui else str(input_counter)
    # We assume curr_input is the list of segments
    input_dict[key] = curr_input 
    return input_dict

def pair_up(l_seg):
##  creates a list of all possible pairs from the input_inv() func
    pairs = []
    for i in range(len(l_seg)):
        for p in range(i + 1, len(l_seg)):
            pairs.append([l_seg[i], l_seg[p]])
    return pairs

def create_dicts(l_seg):
## creates list of dictionaries with negation or confirmation 
## of features for each letter in input_inv()'s input
    dicts_feats = []
    for seg in l_seg:
        current_df = df_par[df_par[SEGMENT_ID_COL] == seg]
        selected_cols = [SEGMENT_ID_COL] + [col for col in cols_to_keep if col in current_df.columns]
        current_df = current_df[selected_cols]
        dicts_feats.extend(current_df.to_dict('records'))
    return dicts_feats

def feature_economist(l_seg = None):
## pulls dicts for all segments in input
    if l_seg == None:
        return 0
    dicts_feats = create_dicts(l_seg)
    list_of_pairs = pair_up(l_seg)
    lookup = {d[SEGMENT_ID_COL]: d for d in dicts_feats}
    features = [f for f in dicts_feats[0].keys() if f in cols_to_keep]
    if not list_of_pairs:
        return 0
    # Precompute which features can distinguish each pair
    pair_distinguishing_features = {}
    for (a, b) in list_of_pairs:
        distinguishing = [f for f in features if lookup[a][f] != lookup[b][f]]
        if not distinguishing:
            # This pair cannot be distinguished by any feature
            return 0      
        pair_distinguishing_features[(a, b)] = distinguishing
              
    # Create binary decision variables (1 = include feature, 0 = exclude)
    feature_vars = {f: LpVariable(f"x_{i}", cat='Binary') 
                   for i, f in enumerate(features)}
    # Create optimization problem
    prob = LpProblem("MinimumFeatureSet", LpMinimize)
    # Objective: minimize total number of selected features
    prob += lpSum(feature_vars.values()), "TotalFeatures"
    # Constraints: each pair must be distinguished by at least one selected feature
    for pair_id, (a, b) in enumerate(list_of_pairs):
        distinguishing = pair_distinguishing_features[(a, b)]
        prob += (lpSum(feature_vars[f] for f in distinguishing) >= 1, f"Pair_{pair_id}_{a}_{b}")
    # Solve the problem (msg=0 suppresses solver output)
    status = prob.solve(PULP_CBC_CMD(msg=0))
    # Check if optimal solution was found
    if status != 1:  # 1 = LpStatusOptimal
        return None

    # Extract selected features
    selected_features = [f for f in features if feature_vars[f].varValue == 1]
    return len(selected_features)


def feature_economist_optimized(l_seg=None):
    """
    Ultra-optimized version: NumPy Vectorization + Bitmask Constraint Pruning.
    """
    if not l_seg or len(l_seg) < 2:
        return {"count": 0, "features": []}

    # 1. Faster Data Extraction
    df_sub = df_par[df_par[SEGMENT_ID_COL].isin(l_seg)].set_index(SEGMENT_ID_COL)
    df_sub = df_sub[[c for c in cols_to_keep if c in df_sub.columns]]
    
    matrix = df_sub.to_numpy()
    features = df_sub.columns.tolist()
    segment_names = df_sub.index.tolist()
    num_segs = len(segment_names)

    # 2. NumPy Pairwise Comparison
    # Create diff_matrix: (N_segs, N_segs, N_features)
    diff_matrix = matrix[:, None, :] != matrix[None, :, :]
    rows, cols = np.triu_indices(num_segs, k=1)
    
    # 3. Bit-Packed Pruning (The "Speed Secret")
    # Convert each pair's differences into a single large integer (bitmask)
    pair_bitsets = []
    for r, c in zip(rows, cols):
        # np.where returns the indices where features differ
        diff_indices = np.where(diff_matrix[r, c])[0]
        
        if len(diff_indices) == 0:
            return {"error": f"Indistinguishable: ({segment_names[r]}, {segment_names[c]})"}
        
        # Create bitmask: e.g., features 0 and 2 different -> 101 (binary) -> 5 (int)
        mask = 0
        for idx in diff_indices:
            mask |= (1 << idx)
        pair_bitsets.append(mask)

    # Remove duplicates and sort by number of set bits (simplest constraints first)
    unique_masks = sorted(list(set(pair_bitsets)), key=lambda x: bin(x).count('1'))
    
    # Subset Pruning: If A is a subset of B, B is redundant.
    minimal_masks = []
    for b in unique_masks:
        # Check if any mask already in 'minimal' is a subset of the current mask 'b'
        if not any((b & m) == m for m in minimal_masks):
            minimal_masks.append(b)

    # 4. Final Small-Scale Optimization
    prob = LpProblem("MinFeatures", LpMinimize)
    feature_vars = {f: LpVariable(f"feat_{i}", cat='Binary') for i, f in enumerate(features)}
    
    prob += lpSum(feature_vars.values())

    # Add only the pruned, essential constraints
    for mask in minimal_masks:
        # Reconstruct which features the mask represents
        dist_feats = [features[i] for i in range(len(features)) if (mask & (1 << i))]
        prob += lpSum([feature_vars[f] for f in dist_feats]) >= 1
        
    # Solve silently
    status = prob.solve(PULP_CBC_CMD(msg=0))
    
    if status == 1:
        selected = [f for f in features if feature_vars[f].varValue == 1]
        return len(selected)
    
    return {"error": "Solver failed to find a solution."}


print(feature_economist(['a', 'b', 'c', 'd', 'f', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'w', 'r', 's']))