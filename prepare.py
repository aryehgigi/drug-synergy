import csv
import random
import json


# get all examples
# The file all_with_abstracts was create using: wget on the url of download csv (unlimited results),
#   of the boolean query Drug1:{drugs} Drug2:{drugs} with the abstract filter {synergy}
f = open("../all_with_abstracts.csv")
r = csv.DictReader(f)
ls = []
s = set()
for i, rr in enumerate(r):
    if i % 40000 == 0:
        print(i)
    if (rr["sentence_text"] in s) or (rr["Drug1"] == rr["Drug2"]):
        continue
    s.add(rr["sentence_text"])
    ls.append(rr)


f.close()

# remove examples already annotated by yosi in the pre-pilot
f = open("to_annotate/yosi_input.jsonl")
yos = [json.loads(y.strip())["sentence_text"] for y in f.readlines()]
f.close()
f = open("to_annotate/pilot_input.jsonl")
pilot = [json.loads(y.strip())["sentence_text"] for y in f.readlines()]
f.close()

# split by cancer
f2 = open("cancer_list.txt")
ls2 = f2.readlines()
ls2 = [ll.strip().lower() for ll in ls2]
f2.close()

c = []
non_c = []
for l in ls:
    if l['sentence_text'] in yos or l['sentence_text'] in pilot:
        continue
    if any(ll in l["title"].lower() for ll in ls2):
        c.append(l)
    else:
        non_c.append(l)


# randomize and split
random.shuffle(c)
random.shuffle(non_c)
for (part, startc, endc, startnc, endnc) in [("shared", 0, 13, 0, 12), ("split", 13, 63, 12, 62)]:
    pilot = c[startc: endc] + non_c[startnc: endnc]
    random.shuffle(pilot)
    f5 = open(f"to_annotate/pilot_input_{part}.jsonl", "w")
    for aa in pilot:
        json.dump(aa, f5)
        _ = f5.write("\n")

    f5.close()


# TODO - shuffle the data, and choose example
# TODO - add distant supervision, and reshuffle

