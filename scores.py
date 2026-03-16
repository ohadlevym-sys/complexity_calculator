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
    bottom = max_features-min_features
    econ_score = 1 - (top/bottom)**0.5
    comp_score = 1 - econ_score
    return econ_score, comp_score

