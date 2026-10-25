import economist as econ
import scores as scores
import math

def model_choose(inv, features, res, model):
    res = int(res)
    if model == 'f':
            return frug_score(inv, features)[res-1]
    elif model == 'e':
            return expl_score(inv, features)[res-1]
    elif model == 'r':
            return relat_score(inv, features)[res-1]


def expl_score(inv, features):
    econ_score = len(inv)/features**2
    comp_score = 1 - econ_score
    return econ_score, comp_score

def frug_score(inv, features):
    min_features = math.log2(len(inv))
    econ_score = min_features/features
    comp_score = 1 - econ_score
    return econ_score, comp_score
        
def relat_score(inv, features):
    min_features = math.ceil(math.log2(len(inv)))
    max_features = len(inv) - 1
    top = features-min_features
    ##מה קורה אם כמות התכונות המקסימלית היא כמות התכונות המינימלית? מתחלק ב0?
    bottom = max_features-
    if bottom == 0: 
         return 0, 1
    econ_score = 1 - (top/bottom)**0.5
    comp_score = 1 - econ_score
    return econ_score, comp_score
     
def get_res():
     while True:
            res = input("choose if you want to see the economy (1) score, or the complexity (2) score: ")
            if res != '1' and res != '2':
                print("please choose one of the options provided")
                continue
            return res

def get_multi_score(inputdict, selected_models, calc_type):
    score_dict = {}
    models = [m for m in selected_models]
    res = calc_type
    if 'r' in models:
        if any(len(val) < 5 for val in inputdict.values()):
            models.remove('r')
    for name, segments in inputdict.items():
        results_for_this_inv = {}
        features = econ.feature_economist(l_seg = segments) 
        for model in models:
            score = scores.model_choose(segments, features[1], res, model)
            results_for_this_inv[model] = score
            
        score_dict[name] = results_for_this_inv
        
    return score_dict, models
