import operator
import collections

def convert_gameloops_to_seconds(gameloops):
    return gameloops / 16.0 * (26.0 / 36.0)

def convert_seconds_to_gameloops(seconds):
    return seconds * 16.0 / (26.0 / 36.0)

def simplify_probabilities(results, threshold = 0.1):
    def map(v):
        if(v < threshold):
            return 0.0
        return v

    filtered = dict()
    for k, v in results.iteritems():
        if(map(v) > 0.0):
            filtered[k] = map(v)
    return filtered

def sort_by_probability(results):
    results_sorted = sorted(results.items(), key=operator.itemgetter(1), reverse=True)
    d = collections.OrderedDict()
    for k, v in results_sorted:
        d[k] = v
    return d

def get_most_probable_build(results):
    sorted = sort_by_probability(results)
    keys = sorted.keys()
    values = sorted.values()

    return (
        keys[0]   if keys   else None,
        values[0] if values else None
    )