import csv
import random
import json
import os
import sys


if __name__ == "__main__":
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
        if (rr["sentence_text"] in s) or (rr["d1"].lower() == rr["d2"].lower()):
            continue
        s.add(rr["sentence_text"])
        ls.append(rr)

    f.close()

    # remove examples already annotated by yosi in the pre-pilot
    already_annotated = []
    to_annotate_dir = "to_annotate/"
    for f_name in os.listdir(to_annotate_dir):
        print(f"reading {f_name}")
        with open(to_annotate_dir + f_name) as f:
            already_annotated += [json.loads(y.strip())["sentence_text"] for y in f.readlines()]

    # split by cancer
    f2 = open("cancer_list.txt")
    ls2 = f2.readlines()
    ls2 = [ll.strip().lower() for ll in ls2]
    f2.close()

    c = []
    non_c = []
    for l in ls:
        if l['sentence_text'] in already_annotated:
            continue
        if any(ll in l["title"].lower() for ll in ls2):
            c.append(l)
        else:
            non_c.append(l)

    # randomize and split
    take_c = int(sys.argv[1])  # e.g 13
    take_non_c = int(sys.argv[2])  # e.g. 12
    task_type = sys.argv[3]  # e.g. split or shared
    cycle = int(sys.argv[4])  # e.g. 4

    having_dups = True
    while having_dups:
        random.shuffle(c)
        random.shuffle(non_c)
        if (
                (len(set(cur_c["title"] for cur_c in c[:take_c])) == take_c) and
                (len(set(cur_non_c["title"] for cur_non_c in c[:take_non_c])) == take_non_c)
        ):
            having_dups = False
        else:
            print(c[:take_c], c[:take_non_c])

    pilot = c[:take_c] + non_c[:take_non_c]
    random.shuffle(pilot)
    f5 = open(f"to_annotate/pilot{cycle}_input_{task_type}.jsonl", "w")
    for aa in pilot:
        json.dump(aa, f5)
        _ = f5.write("\n")

    f5.close()
    # TODO - add distant supervision, and reshuffle
