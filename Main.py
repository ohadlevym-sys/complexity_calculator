import economist as econ
import scores as scores
     
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
        features = econ.feature_economist(segments) 
        for model in models:
            score = scores.model_choose(segments, features, res, model)
            results_for_this_inv[model] = score
            
        score_dict[name] = results_for_this_inv
        
    return score_dict, models