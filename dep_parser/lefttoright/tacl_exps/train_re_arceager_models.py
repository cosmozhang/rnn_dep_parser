"""
ArcEager models with root-at-end
"""
import sys
import os
import os.path
sys.path.append(os.path.join(os.path.dirname(__file__),".."))
import pickle
import isprojective
from pio import io
from explore_policies import *
from arceager import RootAtEndArcEagerState
from dynamicoracles import ArcEagerDynamicOracle_fixed
from staticoracles import ArcEagerStaticOracle
import features.extractors
from minimaltransitionparser import TransitionBasedParser
from ml import sml as ml

def parse_corpus(corpus_fname, model_fname, feature_extractor, transition_system):
   params = ml.SparseMulticlassModel(file(model_fname), sparse=True)
   parser = TransitionBasedParser(params, RootAtEndArcEagerState, feature_extractor)
   parser.action_map = pickle.load(file(model_fname + ".amap"))
   parsed = []
   for sent in io.conll_to_sents(file(corpus_fname)):
      deps = parser.parse(sent)
      deps.annotate(sent)
      parsed.append(sent)
   return parsed

def eval(corpus,ignore_punct=False):
   ugood = ubad = 0.0
   lgood = lbad = 0.0
   for sent in corpus:
      for tok in sent:
         if ignore_punct and tok['form'][0] in ",.-;:'\"!?`{}()[]": continue
         if tok['pparent'] == tok['parent']:
            ugood += 1
            if tok['prel'] == tok['pprel']: lgood += 1
            else: lbad += 1
         else:
            ubad += 1
            lbad += 1
   return ugood/(ugood+ubad), lgood/(lgood+lbad), 0

# train while varying:
# (a) corpus
# (b) exploration policy (both k and p)
# (c) random seed (1,2,3,4,5)
def training_job(corpus_fname, k, p, seed, static, dev_fname, model_out_prefix):
   from training import online_greedy_train
   sents = [s for s in io.conll_to_sents(file(corpus_fname)) if isprojective.is_projective(s)]
   print "training ",corpus_fname,k,p,seed,len(sents)
   labels = set()
   for sent in sents:
      for tok in sent:
         if tok['prel'] == '_': tok['prel'] = 'dep'
         labels.add(tok['prel'])

   oracle = ArcEagerStaticOracle() if static else ArcEagerDynamicOracle_fixed()
   explore = None if static else ExplorePolicy(k, p)
   print "start"
   feature_extractor=features.extractors.get("eager.zn")

   action_map, params = online_greedy_train(
         sents,
         transition_system=RootAtEndArcEagerState,
         oracle=oracle,
         feature_extractor=feature_extractor,
         labels=labels,
         iterations=15,
         explore_policy=explore,
         random_seed=seed,
         shuffle_corpus=True)
   print "end"
   params.finalize()
   TRAIN_OUT_FILE = "%s-reeager-k%s-p%s-seed%s" % (model_out_prefix, k, p, seed)
   if static:
      TRAIN_OUT_FILE = "%s-reeager-static-seed%s" % (model_out_prefix, seed)
   params.dump(file(TRAIN_OUT_FILE,"w"), sparse=True)
   pickle.dump(action_map, file(TRAIN_OUT_FILE+".amap","w"))
   print "training of",corpus_fname,k,p,seed,"done"

   print "parsing"
   parsed = parse_corpus(dev_fname, TRAIN_OUT_FILE, feature_extractor, RootAtEndArcEagerState)
   print "writing"
   outf = file(TRAIN_OUT_FILE + ".dev.parsed","w")
   for sent in parsed:
      io.out_conll(sent, outf, parent='pparent',prel='pprel')
   uas,las,complete = eval(parsed)
   puas,plas,complete = eval(parsed,ignore_punct=True)
   outf.close()
   outf = file(TRAIN_OUT_FILE + ".dev.scores","w")
   print >> outf, "UAS:",uas,"LAS:",las,"NP_UAS:",puas,"NP_LAS:",plas
   outf.close()

   print "deleting"
   os.unlink(TRAIN_OUT_FILE)
   os.unlink(TRAIN_OUT_FILE + ".amap")

if __name__ == '__main__':
   from multiprocessing import Pool
   # assume conll data is structured in files lang.{test,train}
   CONLL_BASE = "/home/yogo/G/data/conll_data/2007/"
   pool = Pool()
   for lang in "arabic basque catalan chinese czech english greek hungarian italian turkish".split():
      corpus = CONLL_BASE + lang + ".train"
      dev = CONLL_BASE + lang + ".test"
      model_prefix = "models/%s" % lang
      for seed in [1,2,3,4,5]:
         for k in [1]:
            for p in [0.9,1]:
               pool.apply_async(training_job, (corpus,k,p,False,seed,dev,model_prefix))
   pool.close()
   pool.join()
