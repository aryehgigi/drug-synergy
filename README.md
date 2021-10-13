# drug-synergy

- agreement1 - first 25 examples of to_annotate/pilot_input * 7 annotators = 175 annotations
- bulk1 - last 175 examples of to_annotate/pilot_input split by 7 annotators - 20 examples not annotated by Yakir = 155 annotations
- agreement2 - 25 examples of to_annotate/pilot2_input_shared * 8 annotators (shaked joined) = 200 annotations
- bulk2 - 300 examples of to_annotate/pilot2_input_split split by 7 annotators = 300 annotations
- bulk3 - next 358 examples of to_annotate/pilot2_input_split split by 7 annotators = 358 annotations
  - yakir's 15 are part of shaked's 100.
  - shaked and yakir in total did 98
  - hagit only di 60
  - we miss 42 examples from the original to_annotate/pilot2_input_split
- agreement3_yakir_yosi(bulk2) - last 25 examples of to_annotate/pilot2_input_split (belonged to yosi on the split task) * 2 annotators (yosi and yakir) = 50 annotations
- agreement4_yakir_yosi(bulk2) - 25 examples (151-175) of to_annotate/pilot2_input_split (belonged to yosi on the split task) * 2 annotators (yosi and yakir) = 50 annotations
- agreement3_fixed - 25 examples doubley annotated in agreement3_yakir_yosi(bulk2) fixed by yosi's arbitration on the disagreements
- test_set_1 - 75 examples double-annotated by yakir (25 of yuval, 25 of maytal and 25 of hagit) taken from bulk2 and 3 (first 25 of each 100 of the first 300 in the pilot2_input_split)
- test_set_2 - 75 examples double-annotated by shaked (25 of dana_n, 25 of dana_a and 25 of yosi) taken from bulk2 and 3 (first 25 of each 100 of the last 300 in the pilot2_input_split)
- test_set_1_gold and test_set_2_gold - are (each) the 75 first-time-annotated taken from bulk2 and 3.
- test_set_1_combined and test_set_2_combined - are (each) 150 of the combined test_set_x + test_set_x_gold
- 