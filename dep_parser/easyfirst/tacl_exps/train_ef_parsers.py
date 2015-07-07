import random
import sys
import os
import os.path
sys.path.append(os.path.join(os.path.dirname(__file__),".."))
import pickle
import isprojective
from pio import io
from explore_policies import *
from easyfirst import train,Model,Parser
import moduleloader
from ml.ml import MulticlassModel

def parse_corpus(corpus_fname, weights_fname, features_fname):
   fext = moduleloader.load_module(features_fname).FeaturesExtractor()
   m=MulticlassModel(weights_fname)
   parser=Parser(m,fext,None)
   parsed = []
   for sent in io.conll_to_sents(file(corpus_fname)):
      deps = parser.parse(sent)
      sent = deps.annotate(sent)
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
   sents = [s for s in io.conll_to_sents(file(corpus_fname)) if isprojective.is_projective(s)]
   print "training ",corpus_fname,k,p,seed,len(sents)

   explore = ExplorePolicy(k,p)
   TRAIN_OUT_FILE = "%s-ef-k%s-p%s-seed%s" % (model_out_prefix, k, p, seed)
   if static:
      TRAIN_OUT_FILE = "%s-ef-static-seed%s" % (model_out_prefix, seed)
      explore=None

   model = Model("features/znp.py", "%s.weights" % TRAIN_OUT_FILE)
   model.save("%s.model" % TRAIN_OUT_FILE)
   random.seed(seed)
   train(sents, model, dev=None, ITERS=20,save_every=None,explore_policy=explore,shuffle_sents=True)
   print "training of",corpus_fname,k,p,seed,"done"
   print "parsing"

   parsed = parse_corpus(dev_fname, TRAIN_OUT_FILE + ".weights.FINAL", "features/znp.py")
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
   os.unlink(TRAIN_OUT_FILE + ".weights.FINAL")
   os.unlink(TRAIN_OUT_FILE + ".model")

if __name__ == '__main__':
   from multiprocessing import Pool
   # assume conll data is structured in files lang.{test,train}
   CONLL_BASE = "/home/yogo/G/data/conll_data/2007/"
   pool = Pool()
   for lang in "arabic basque catalan chinese czech english greek hungarian italian turkish".split():
      corpus = CONLL_BASE + lang + ".train"
      dev = CONLL_BASE + lang + ".test"
      model_prefix = "models/%s" % lang
      print "corpus:",corpus
      for seed in [1,2,3,4,5]:
         for k in [1]:
            for p in [0.9,1]:
               pool.apply_async(training_job, (corpus,k,p,seed,False,dev,model_prefix))
   pool.close()
   pool.join()

