#!/usr/bin/env python
## Copyright 2013 Yoav Goldberg
##
##    This is free software: you can redistribute it and/or modify
##    it under the terms of the GNU General Public License as published by
##    the Free Software Foundation, either version 3 of the License, or
##    (at your option) any later version.
##
##    This software is distributed in the hope that it will be useful,
##    but WITHOUT ANY WARRANTY; without even the implied warranty of
##    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
##    GNU General Public License for more details.
##
##    You should have received a copy of the GNU General Public License
##    along with this software.  If not, see <http://www.gnu.org/licenses/>.
"""
driver for ArcEager parser.

Author: Yoav Goldberg (yoav.goldberg@gmail.com)
"""
from features import extractors 
from params import parser
import gflags
import sys
import time
import random
from ml import sml as ml

from pio import io
from minimaltransitionparser import *
FLAGS = gflags.FLAGS

########


gflags.DEFINE_string("feature_extractor","eager.zn","Feature extractor name.",
                     short_name='f')
gflags.DEFINE_boolean("train",False,"If on, train a new model.")
gflags.DEFINE_string("system","eager","Transition system to use.")
gflags.DEFINE_string("explore","none","Exploration policy for cost-oracle.")

gflags.DEFINE_string("model_file","model.out","model file name.",short_name='m')
gflags.DEFINE_boolean("eval",False,"If on, print evaluation.",short_name='e')


gflags.DEFINE_boolean("ignore_punc",True,"Ignore punctuation in evaluation.")
gflags.DEFINE_boolean("only_proj",True,"If true, prune non-projective sentences in training.")
gflags.DEFINE_boolean("add_dep_label",True,"If true, replace the '_' label with 'dep'.")
gflags.DEFINE_integer("random_seed",0,"Random seed.")

gflags.DEFINE_integer("save_every",0,"Dump a model every k iterations.")

args = FLAGS(sys.argv)
print args

DATA_FILE=args[1]


featExt = extractors.get(FLAGS.feature_extractor)

sents = list(io.conll_to_sents(file(DATA_FILE)))

if FLAGS.train and (True or FLAGS.only_proj):
   import isprojective
   sents = [s for s in sents if isprojective.is_projective(s)]

if FLAGS.add_dep_label:
   for sent in sents:
      for tok in sent:
         if tok['prel'] == '_': tok['prel'] = "dep"

EXPLORE = 1

LABELED = True

MODE = "train" if FLAGS.train else "test"
#MODE="test_system"

system = FLAGS.system

ITERATIONS = 5

random.seed(FLAGS.random_seed)

import pickle
def save_action_map(action_map, fh):
   pickle.dump(action_map, fh)

def load_action_map(fh):
   return pickle.load(fh)

from explore_policies import exploration_policies

if MODE=="train":
   explore_policy = exploration_policies[FLAGS.explore_policy]
   TRAIN_OUT_FILE = FLAGS.model_file
   if LABELED:
      labels = set()
      for sent in sents:
         for tok in sent:
            labels.add(tok['prel'])
   else:
      labels = set([None]) 
   fout = file(TRAIN_OUT_FILE,"w")
   if system == 'eager':
      nactions, action_map = ArcEagerState.get_action_map(labels)
      oracle = ArcEagerDynamicOracle_fixed()
      params = ml.SparseMultitronParameters(nactions)
      p = ArcEagerParser(params, featExt)
   elif system == 'static-eager':
      nactions, action_map = ArcEagerConfiguration.get_action_map(labels)
      from oracles import ArcEagerStaticOracle
      oracle = ArcEagerStaticOracle()
      params = ml.SparseMultitronParameters(nactions)
      p = ArcEagerParser(params, featExt)
   elif system == 'hybrid':
      nactions, action_map = ArcHybridConfiguration.get_action_map(labels)
      oracle = ArcHybridDynamicOracle()
      params = ml.SparseMultitronParameters(nactions)
      p = ArcHybridParser(params, featExt)
   else:
      raise Exception("Invalid transition system.")
   #params = ml.MultitronParameters(nactions)
   p.action_map = action_map
   import random
   #random.shuffle(sents)
   p.train(sents, oracle, ITERATIONS, explore_policy)
   # Save model.
   params.finalize()
   params.dump(out=fout, sparse=True)
   save_action_map(action_map, file(TRAIN_OUT_FILE+".amap","w"))
   sys.exit()

def verify_cost(sent,deps,cost):
   deps.annotate(sent)
   print "\ncost",cost,"\n",[tok['parent'] for tok in sent],"\n",[tok['pparent'] for tok in sent]
   for tok in sent[0:]:
      if tok['parent'] != tok['pparent']: cost -= 1
   assert(cost == 0),cost

if MODE=="test_system":
   if LABELED:
      labels = set()
      for sent in sents:
         for tok in sent:
            labels.add(tok['prel'])
   else:
      labels = set([None]) 
   if system == 'eager':
      nactions, action_map = ArcEagerConfiguration.get_action_map(labels)
      oracle = ArcEagerDynamicOracle()
      oracle = ArcEagerDynamicOracle_fixed()
      #oracle = ArcEagerStaticOracle()
      params = ml.SparseMultitronParameters(nactions)
      p = ArcEagerParser(params, featExt)
   if system == 'nm-eager':
      nactions, action_map = NonMonotonicArcEagerState.get_action_map(labels)
      oracle = HGJDynamicOracle()
      params = ml.SparseMultitronParameters(nactions)
      p = NonMonotonicArcEagerParser(params, featExt)
   elif system == 'hybrid':
      nactions, action_map = ArcHybridConfiguration.get_action_map(labels)
      oracle = ArcHybridDynamicOracle()
      params = ml.SparseMultitronParameters(nactions)
      p = ArcHybridParser(params, featExt)
   else:
      raise Exception("Invalid transition system.")
   #params = ml.MultitronParameters(nactions)
   p.action_map = action_map
   import random
   random.seed("seed")
   #random.shuffle(sents)
   for sent in sents:
      derivs = set()
      for x in xrange(15):
         #d,c,deps = p.get_a_gold_derivation(sent, oracle)
         d,c,deps = p.get_a_random_derivation(sent, oracle, 1)
         verify_cost(sent,deps,c)
         derivs.add(tuple(d))
         print float(c)/len(sent)
      #print len(derivs)
      #if len(derivs) > 5:
      #   derivs = list(derivs)
      #   print derivs[0]
      #   print derivs[1]
      #   print
   sys.exit()

# test
elif MODE=="test":
   params = ml.SparseMulticlassModel(FLAGS.model_file, sparse=True)
   if system == 'eager':
      p = ArcEagerParser(params, featExt)
   if system == 'nm-eager':
      p = NonMonotonicArcEagerParser(params, featExt)
   elif system == 'hybrid':
      p = ArcHybridParser(params, featExt)
   p.action_map = load_action_map(file(FLAGS.model_file+".amap"))


good = 0.0
bad  = 0.0
complete=0.0

#main test loop
reals = set()
preds = set()

lgood = lbad = 0.0

MLTrainerWrongActionException = "str"
now = time.time()
for i,sent in enumerate(sents):
   sgood=0.0
   sbad=0.0
   mistake=False
   print >> sys.stdout, "%s %s %s\n" % ( "@@@",i,good/(good+bad+1))
   #io.out_conll(sent)
   try:
      d=p.parse(sent)
   except MLTrainerWrongActionException:
      # this happens only in "early update" parsers, and then we just go on to
      # the next sentence..
      print "WTF"
      continue
   sent = d.annotate(sent)
   io.out_conll(sent,parent='parent')
   io.out_conll(sent,parent='pparent')
   for tok in sent:
      #print tok['parent'],tok['pparent']
      if FLAGS.ignore_punc and tok['form'][0] in "`',.-;:!?{}": continue
      reals.add((i,tok['parent'],tok['id']))
      preds.add((i,tok['pparent'],tok['id']))
      if FLAGS.ignore_punc and tok['prel'] == 'punct': continue
      if tok['pparent']==-1:continue
      if tok['parent']==tok['pparent'] or tok['pparent']==-1:
         if tok['prel'] == tok['pprel']: lgood += 1
         else: print "badl:",tok['prel'],tok['pprel']
         good+=1
         sgood+=1
      else:
         bad+=1
         sbad+=1
         mistake=True
         #print "mistake:", tok['parent'],tok['pparent'],tok['id']
   if not mistake: complete+=1
   #sys.exit()
   #if opts.SCORES_OUT: scores_out.write("%s\n" % (sgood/(sgood+sbad)))
  
print time.time() - now,"secs"
#if opts.SCORES_OUT: scores_out.close()

if FLAGS.eval:
   print "accuracy:", good/(good+bad)
   print "complete:", complete/len(sents)
   preds = set([(i,p,c) for i,p,c in preds if p != -1])
   print "recall:", len(preds.intersection(reals))/float(len(reals))
   print "precision:", len(preds.intersection(reals))/float(len(preds))
   print "assigned:",len(preds)/float(len(reals))
   print "labeled:",lgood / (good + bad)
   
