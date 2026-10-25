import pandas as pd
import collections
import Data_normalization as dn
import unicodedata

# 1. Load your Excel
df = dn.df

DUMMY_ROW = collections.defaultdict(lambda: 1)
DUMMY_ROW['Name'] = 'MASTER'
DUMMY_ROW['Consonantal'] = 1
DUMMY_ROW['sonorant'] = 1
DUMMY_ROW['syllabic'] = 1 

def parse_val(val):
# Reduces dual values (e.g. '1,0') to 1.
    if isinstance(val, str) and ',' in val:
        return 1
    try:
        return int(val)
    except (ValueError, TypeError):
        # If it's a blank cell (NaN) or random text, default to 0
        return 0

# Recursively traverses down the tree and prunes branches where all leaf values are 0.
def prune_dead_branches(node):
    if isinstance(node, TerminalNode):
        try:
            return int(node.value)
        except (ValueError, TypeError):
            return 0
        
    branch_sum = sum(prune_dead_branches(child) for child in getattr(node, 'children', []))
    if branch_sum == 0:
        node.exist = False
    else:
        node.exist = True 
    return branch_sum

class Root:
    def __init__(self, row, root_children = None):
        df['syllabic'] = df['SegmentClass'].apply(lambda x: 1 if str(x).strip().lower() == 'vowel' else 0)
        self.name = row['Name']
        self.data = { 
            'Consonantal': parse_val(row["Consonantal"]),
            'Sonorant': parse_val(row["Sonorant"]),
            'syllabic': parse_val(row["syllabic"])
        }
        self.children = root_children
        
class TerminalNode:
    def __init__(self, row, featurename:str, parent = None, children = None):
        self.parent = parent
        self.name = row['Name']

        self.feature = featurename
        try:
            self.value = parse_val(row[featurename])
        except KeyError:
            print("\n--- DEBUG: PANDAS COLUMN MISMATCH ---")
            print(f"The code is looking for: '{featurename}'")
            print(f"The exact columns Pandas sees are: {list(row.keys())}")
            print("-------------------------------------\n")
            raise
        self.children = children
    
class NonTerminalNode:
    def __init__(self, feature_name:str, children = None, parent = None):
        self.exist = True
        self.feature = feature_name
        self.children = children if children is not None else []
        self.parent = parent 

class Tree:
    def __init__(self, row, root_children = None):
        self.row = row
        self.root = Root(row, root_children if root_children is not None else [])
    
    def add_node(self, nodetype:str, parent, featurename, children):
        seg = self.root.name
        node = None
        if nodetype == "Nonterminal":
            node = NonTerminalNode(featurename, children, parent)
        if nodetype == 'Terminal':
            node = TerminalNode(self.row, featurename, parent)
        if node and parent and hasattr(parent, 'children') and node not in parent.children:
            parent.children.append(node)
        return node

def tree_builder(row, is_master = False):
    # Initialize the tree
    tree = Tree(row = row)
    # ================= LEVEL 1 ================
    # Dependents Terminals
    tree.add_node("Terminal", tree.root, "approximant", [])
    tree.add_node("Terminal", tree.root, "continuant", [])
    tree.add_node("Terminal", tree.root, "nasal", [])

    # ================= LEVEL 2 =================
    guttural = tree.add_node("Nonterminal", tree.root, "Guttural", [])
    c_place = tree.add_node("Nonterminal", tree.root, "C-Place", [])
    length = tree.add_node("Nonterminal", tree.root, "Length", [])
    manner = tree.add_node("Nonterminal", tree.root, "Manner Modifiers", [])

    # ================= LEVEL 3 (Guttural) =================
    laryngeal = tree.add_node("Nonterminal", guttural, "Laryngeal", [])
    pharyngeal = tree.add_node("Nonterminal", guttural, "Pharyngeal", [])

    # Laryngeal Terminals
    tree.add_node("Terminal", laryngeal, "spreadGlottis", [])
    tree.add_node("Terminal", laryngeal, "constrictedGlottis", [])
    tree.add_node("Terminal", laryngeal, "fortis", [])
    tree.add_node("Terminal", laryngeal, "loweredLarynxImplosive", [])
    tree.add_node("Terminal", laryngeal, "raisedLarynxEjective", [])
    tree.add_node("Terminal", laryngeal, "voiced", [])

    # Pharyngeal Terminals
    tree.add_node("Terminal", pharyngeal, "epilaryngealSource", [])
    tree.add_node("Terminal", pharyngeal, "retractedTongueRoot", [])
    tree.add_node("Terminal", pharyngeal, "advancedTongueRoot", [])

    # ================= LEVEL 3 (C-Place) =================
    v_place = tree.add_node("Nonterminal", c_place, "V-place", [])
    labial = tree.add_node("Nonterminal", c_place, "Labial", [])
    coronal = tree.add_node("Nonterminal", c_place, "Coronal", [])
    dorsal = tree.add_node("Nonterminal", c_place, "Dorsal", [])
    
    tree.add_node("Terminal", labial, "labiodental", [])
    tree.add_node("Terminal", labial, "labial", [])
    tree.add_node("Terminal", coronal, "anterior", [])
    tree.add_node("Terminal", coronal, "distributed", [])
    tree.add_node("Terminal", coronal, "lateral", [])
    tree.add_node("Terminal", coronal, "strident", [])
    tree.add_node("Terminal", coronal, "coronal", [])
    tree.add_node("Terminal", dorsal, "high", [])
    tree.add_node("Terminal", dorsal, "low", [])
    tree.add_node("Terminal", dorsal, "back", [])
    tree.add_node("Terminal", dorsal, "dorsal", [])

     # ================= LEVEL 3 (Manner) =================
    tree.add_node("Terminal", manner, "click", [])
    tree.add_node("Terminal", manner, "tap", [])
    tree.add_node("Terminal", manner, "trill", [])
    tree.add_node("Terminal", manner, "delayedRelease", [])


     # ================= LEVEL 3 (V-Place) =================
    v_labial = tree.add_node("Nonterminal", v_place, "V-Labial", [])
    v_coronal = tree.add_node("Nonterminal", v_place, "V-Coronal", [])
    v_dorsal = tree.add_node("Nonterminal", v_place, "V-Dorsal", [])
    # V-Place Terminals
    tree.add_node("Terminal", v_labial, "round", [])
    tree.add_node("Terminal", v_coronal, "front", [])
    if is_master or tree.root.data["Consonantal"] == 0:
        tree.add_node("Terminal", v_dorsal, "high", [])
        tree.add_node("Terminal", v_dorsal, "low", [])
        tree.add_node("Terminal", v_dorsal, "back", [])
        tree.add_node("Terminal", v_dorsal, "tense", [])

    #Length terminals 
    tree.add_node("Terminal", length, "long", [])
    tree.add_node("Terminal", length, "short", [])
    
    if not is_master:
        prune_dead_branches(tree.root)

    return tree

TREE1 = tree_builder(DUMMY_ROW, True)

def build_tree_by_symbol(segment_symbol: str, df: pd.DataFrame):
    clean_symbol = unicodedata.normalize('NFC', str(segment_symbol).strip())
    
    # 2. השוואה בטוחה: מנרמלים גם את עמודת השמות בטבלה לצורך החיפוש
    # (הערה: מבחינת ביצועים, אידיאלי לעשות את הנרמול הזה ל-df רק פעם אחת בקובץ Data_normalization)
    normalized_names = df['Name'].astype(str).str.strip().apply(lambda x: unicodedata.normalize('NFC', x))
    matching_rows = df[normalized_names == clean_symbol]
    if matching_rows.empty:
        raise ValueError(f"Segment '{segment_symbol}' not found in the inventory.")
    segment_row = matching_rows.iloc[0].to_dict()
    return tree_builder(segment_row)


import graphviz

def visualize_my_tree(root_node):
    # 1. Create the blank visual canvas
    dot = graphviz.Digraph(comment='My Tree')
    # 2. Define a function that automatically draws a node and looks for its children
    def traverse(current_node):
        # Give the node a unique ID based on its memory location (prevents naming collisions)
        node_id = str(id(current_node))
        # Assuming your node object has a '.name' attribute. Change this to match your code!
        base_label = getattr(current_node, 'feature', getattr(current_node,'name', 'unnamed node'))
        if hasattr(current_node, 'data') and isinstance(current_node.data, dict):
            # 1. It is the Root Node!
            # Let's loop through the data dictionary and format it.
            components = []
            for key, val in current_node.data.items():
                components.append(f"{key}: {val}")
            # Join them with line breaks so they stack nicely under the Root name
            components_str = "\n".join(components)
            final_label = f"{base_label}\n{components_str}"
        elif hasattr(current_node, 'value'):
            # It is terminal! Format it to show both name and value.
            # The \n puts the value on a second line inside the node bubble.
            final_label = f"{base_label}\nValue: {current_node.value}"
        else:
            # It is a non-terminal node, just use the base string
            final_label = str(base_label)

        dot.node(node_id, str(final_label))
        # 3. If this node has sub-features, draw them and connect them
        # Assuming your node object has a '.children' list. Change this if needed!
        if hasattr(current_node, 'children') and current_node.children:
            for child in current_node.children:
                child_id = str(id(child))
                # Draw the line connecting parent to child
                dot.edge(node_id, child_id)
                # RECURSION: Trigger this exact process on the child to keep walking down the tree
                traverse(child)
    # 4. Kick off the automation starting at your root
    traverse(root_node)
    # 5. Render and open the image
    dot.render('my_tree_visual', format='png', view=False)
visualize_my_tree(TREE1.root)


def generate_tree_graph(root_node):
    # 1. Create the blank visual canvas
    dot = graphviz.Digraph(comment='My Tree')

    # 2. Define a function that automatically draws a node and looks for its children
    def traverse(current_node, parent_id = None):
        if getattr(current_node, 'exist', True) is False:
            return
        # Give the node a unique ID based on its memory location (prevents naming collisions)
        node_id = str(id(current_node))
        
        # חילוץ השם של התכונית
        base_label = getattr(current_node, 'feature', getattr(current_node,'name', 'unnamed node'))
        
        # עיצוב הטקסט שיופיע בבועה
        if hasattr(current_node, 'data') and isinstance(current_node.data, dict):
            components = [f"{key}: {val}" for key, val in current_node.data.items()]
            components_str = "\n".join(components)
            final_label = f"{base_label}\n{components_str}"
        elif hasattr(current_node, 'value'):
            final_label = f"{base_label}\nValue: {current_node.value}"
        else:
            final_label = str(base_label)

        # 3. ציור הבועה של הצומת הנוכחי
        dot.node(node_id, str(final_label))

        # 4. מתיחת הקו מההורה אליי (מבוצע רק אחרי שווידאנו שאני קיים!)
        if parent_id is not None:
            dot.edge(parent_id, node_id)

        # 5. מעבר על הילדים (ומעבירים להם את ה-ID שלי בתור ההורה שלהם)
        if hasattr(current_node, 'children') and current_node.children:
            for child in current_node.children:
                traverse(child, parent_id=node_id)

    # מפעילים מהשורש (לשורש אין הורה, לכן parent_id נשאר None)
    traverse(root_node)

    # 5. Render and open the image
    return dot