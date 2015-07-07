#!/usr/bin/env python

## Copyright 2013 Yoav Goldberg
##
##    This is free software: you can redistribute it and/or modify
##    it under the terms of the GNU General Public License as published by
##    the Free Software Foundation, either version 3 of the License, or
##    (at your option) any later version.
##
##    This code is distributed in the hope that it will be useful,
##    but WITHOUT ANY WARRANTY; without even the implied warranty of
##    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
##    GNU General Public License for more details.
##
##    You should have received a copy of the GNU General Public License
##    along with this code.  If not, see <http://www.gnu.org/licenses/>.

import random
import sys
from pio import io
import isprojective
from explore_policies import ExplorePolicy

from optparse import OptionParser

from easyfirst import train,Model

usage="""usage: %prog -o model -f features [options] train_file [dev_file] """ 

parser = OptionParser(usage)
parser.add_option("-o","--model",dest="model_file")
parser.add_option("-f","--features",dest="features_file",default="None")
parser.add_option("--iters",dest="iters",action="store",type="int",default=20)
parser.add_option("--every",dest="save_every",action="store",type="int",default=1)
parser.add_option("--costoracle",dest="follow_incorrect",action="store_true",default=False)
parser.add_option("--labeled",dest="labeled",action="store_true",default=False)
parser.add_option("--seed",dest="random_seed",action="store",type="int",default=1)

opts, args = parser.parse_args()

if len(args)<1 or not (opts.model_file or opts.features_file):
   parser.print_usage()
   sys.exit(1)

TRAIN_FILE = args[0]
DEV_FILE   = args[1] if len(args)>1 else None
FEATURES   = opts.features_file
MODEL      = opts.model_file


model = Model(FEATURES, "%s.weights" % MODEL)
model.save("%s.model" % MODEL)


dev = [s for s in io.conll_to_sents(file(DEV_FILE))] if DEV_FILE else []

train_sents = list(io.conll_to_sents(file(TRAIN_FILE)))
print len(train_sents)
train_sents = [s for s in train_sents if isprojective.is_projective(s)]
print len(train_sents)

random.seed(opts.random_seed)
if opts.follow_incorrect:
   explore=ExplorePolicy(2,0.9) # almost always
else: explore=None
if (opts.labeled):
   from easyfirst import train_labeled
   train_labeled(train_sents, model, dev, opts.iters,save_every=opts.save_every,explore_policy=explore,shuffle_sents=True)
else:
   train(train_sents, model, dev, opts.iters,save_every=opts.save_every,explore_policy=explore,shuffle_sents=True)

