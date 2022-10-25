import json

f = open("./synergy.txt")
ts = [l.strip() for l in f.readlines()]

f = open("./converted2model/final_test_set.jsonl")
js = [json.loads(l) for l in f.readlines()]
f.close()


def calc_score(span, spans, exact_match=False):
    score = 0
    for gold_span in spans:
        spans_intersecting = len(set(span).intersection(set(gold_span)))
        spans_union = len(set(span + gold_span))
        if ((spans_intersecting >= 2) and (not exact_match)) or ((spans_intersecting / spans_union) == 1):
            score = max(score, spans_intersecting / spans_union)
    return score


def print_f(exact, pos):
    cum_p = 0
    cum_r = 0
    gold = 0
    predicated = 0
    for i, j in enumerate(js):
        pred_span = []
        gold += len(j['rels'])
        if any([t for t in ts if t.lower() in j['sentence'].lower()]):
            predicated += 1
            pred_span = list(range(len(j['spans'])))
        cum_p += calc_score(pred_span, [rel['spans'] for rel in j['rels'] if not pos or rel['class'] == "POS"], exact)
        for rel in j['rels']:
            if not pos or rel['class'] == "POS":
                cum_r += calc_score(rel['spans'], [pred_span], exact)
    p = (cum_p / predicated) if predicated else 0
    r = (cum_r / gold) if gold else 0
    print("Exact match:" if exact else "Partial match:", ((2 * p * r) / (p + r)) if (p + r > 0) else 0, p, r)


print_f(False, False)
print_f(True, False)
print_f(False, True)
print_f(True, True)
