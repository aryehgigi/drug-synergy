import csv
import random
import json
import os
import sys


def get_examples(path_to_file: str):
    f = open(path_to_file)
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
    return ls


def clear_ds(ds):
    with open("synergy.txt") as f:
        synergy_lines = f.readlines()
    synergy_words = [ll.strip().lower() for ll in synergy_lines]

    final_ds = []
    for example in ds:
        # skip sentences that have a synergy word in the abstract
        if any(synergy_word in example["abstract"] for synergy_word in synergy_words):
            continue
        final_ds.append(example)

    return final_ds


def get_already_annotated():
    already_annotated = []
    to_annotate_dir = "to_annotate/"
    for f_name in os.listdir(to_annotate_dir):
        print(f"reading {f_name}")
        with open(to_annotate_dir + f_name) as f:
            for y in f.readlines():
                loaded_y = json.loads(y.strip())
                if "sentence_text" in loaded_y:
                    already_annotated.append(loaded_y["sentence_text"])
                else:
                    print(f"{f_name} is missing a sentence_text {loaded_y}")
    return already_annotated


def get_cancer_list():
    with open("cancer_list.txt") as f2:
        ls2 = f2.readlines()
    return [ll.strip().lower() for ll in ls2]


def get_data_to_annotate(candidate_data, already_annotated, cancer_list, take_c, take_non_c):
    # filter and split
    c = []
    non_c = []
    for l in candidate_data:
        if l['sentence_text'] in already_annotated:
            continue
        if any(cancer_word in l["title"].lower() for cancer_word in cancer_list):
            c.append(l)
        else:
            non_c.append(l)

    # randomize  and remove dups
    having_dups = True
    while having_dups:
        random.shuffle(c)
        random.shuffle(non_c)
        # validate we take sentences only from different articles (by their title)
        if (
                (len(set(cur_c["title"] for cur_c in c[:take_c])) == take_c) and
                (len(set(cur_non_c["title"] for cur_non_c in c[:take_non_c])) == take_non_c)
        ):
            having_dups = False
        else:
            print(c[:take_c], c[:take_non_c])

    return c[:take_c] + non_c[:take_non_c]


if __name__ == "__main__":
    # read user arguments
    take_c = int(sys.argv[1])  # e.g 13
    take_non_c = int(sys.argv[2])  # e.g. 12
    take_c_ds = int(sys.argv[3])  # e.g 13
    take_non_c_ds = int(sys.argv[4])  # e.g. 12
    task_type = sys.argv[5]  # e.g. split or shared
    cycle = int(sys.argv[6])  # e.g. 4

    # remove examples already annotated
    already_annotated = get_already_annotated()

    # split by cancer
    cancer_list = get_cancer_list()

    # get all examples
    # The file all_with_abstracts was created using: wget on the url of download csv (unlimited results),
    #   of the boolean query d1:{drugs} d2:{drugs} with the abstract filter {synergy}
    # Notes:
    #   - remember to take the newest version as the drug list might be updated
    #   - the download csv has an option now to choose fields, so notice to choose:
    #       abstract, paragraph_text, article_link, sentence_text, title, capture_indices
    chosen_data_regular = []
    if take_c or take_non_c:
        ls = get_examples("../all_with_abstracts.csv")
        chosen_data_regular = get_data_to_annotate(ls, already_annotated, cancer_list, take_c, take_non_c)

    # get distant supervision examples
    # The file distant_supervision.csv was created using: wget on the url of download csv (unlimited results),
    #   of the boolean query d1:{combos.1} d2:{combos.2}
    chosen_data_ds = []
    if take_c_ds or take_non_c_ds:
        ds = clear_ds(get_examples("../distant_supervision.csv"))
        chosen_data_ds = get_data_to_annotate(ds, already_annotated, cancer_list, take_c_ds, take_non_c_ds)

    # filter, randomize and split
    chosen_data = chosen_data_regular + chosen_data_ds
    random.shuffle(chosen_data)

    # output
    with open(f"to_annotate/pilot{cycle}_input_{task_type}.jsonl", "w") as f:
        for aa in chosen_data:
            json.dump(aa, f)
            _ = f.write("\n")
