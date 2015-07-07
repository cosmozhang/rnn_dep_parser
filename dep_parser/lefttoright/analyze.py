def read_scores(fname):
   line = file(fname).next()
   line = line.strip().split()
   return [float(line[1])]
#print " , ".join(map(str,["k",0,0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9]))
for k in range(6):
   #print k,
   for p in [0,0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9]:
      uas = 0.0
      uases = []
      for seed in [1,2,3,4,5]:
         u = read_scores("models/basque-eager-k%s-p%s-seed%s.dev.scores" % (k,p,seed))[0]
         uas += u
         uases.append(u)
      uas = uas / 5
      print uas,
   print
