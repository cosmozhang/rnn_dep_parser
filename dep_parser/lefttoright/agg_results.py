import sys
import glob
from collections import defaultdict
uas = defaultdict(list)
for fname in glob.glob("models/*.dev.scores"):
   name = fname.split("models/",1)[1]
   lang, rest = name.split("-",1)
   which, seed = rest.split("seed")
   uas[(lang,which)].append(float(file(fname).next().split()[1]))
for (lang,which), scores in uas.iteritems():
   print lang, which, sum(scores)/len(scores)
