from collections import defaultdict
import numpy as np

UASdict = defaultdict(list)
ROOTdict = defaultdict(list)

for line in open("eval_all_langs_rules").readlines():
    line = line.strip().split()
    root_acc = line[-1]
    uas = line[11]
    key = line[0]+"\t"+line[1].split("_")[0].replace("-ud-test.conllu.delex.sample","")
    UASdict[key].append(float(uas))
    ROOTdict[key].append(float(root_acc))

for k in sorted(UASdict.keys()):
    outvals = [np.average(UASdict[k]),np.std(UASdict[k]),np.average(ROOTdict[k]),np.std(ROOTdict[k])]
    outvals = [k] + [str(round(x,2)) for x in outvals]
    print("\t".join(outvals))