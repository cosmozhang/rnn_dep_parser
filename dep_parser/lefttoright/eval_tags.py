import sys
for l1,l2 in zip(
      file(sys.argv[1]),
      file(sys.argv[2])):
   l1 = l1.strip().split()
   l2 = l2.strip().split()
   if not l1:
      assert(not l2)
      continue
   t1 = l1[3]
   t2 = l2[3]
   print t1 == t2


