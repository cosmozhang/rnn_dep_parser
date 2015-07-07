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

import sys
import random
from ml import sml
from common import ROOT

def online_greedy_train(
      corpus, transition_system, oracle, feature_extractor, labels, param_maker=sml.SparseMultitronParameters,
      iterations=15, explore_policy=None, random_seed=1, shuffle_corpus=True):
   """
   corpus: list of sentences
   transition_system: has .CreateInitialState(sent)
   oracle: has .action_cost((action,label), state) and .correct_everywhere().  TODO
   feature_extractor: has .extract(state) and is compatible with the states. TODO
   params: SparseMultitronParameters
   param_maker: param_maker(nactions) should return a new parameter vector
   iterations: number
   explore_policy: None or has .should_explore(iter_number).
   random_seed: number
   shuffle_corpus: boolean
   """
   random.seed(random_seed)
   nactions, action_map = transition_system.get_action_map(labels)
   params = param_maker(nactions)
   for iter_number in xrange(iterations):
      print >> sys.stderr,"iter", iter_number
      if shuffle_corpus: random.shuffle(corpus)
      for sid, sent in enumerate(corpus):
         if sid % 1000 == 0:
            print "sents:",sid
         sent = [ROOT] + sent  #TODO: sent copy and ROOT addition into transition_system
         state = transition_system.CreateInitialState(sent)
         while not state.is_in_finish_state():
            params.tick()
            fs = feature_extractor.extract(state.stack, state.deps, state.sent, state.i) #TODO: single param
            action_scores = params.get_scores(fs)
            ranked_actions = list(sorted(action_scores.items(),key=lambda x:-x[1]))
            pred_action, best_score = ranked_actions[0]
            # TODO: move from action_cost to "is allowed"
            while oracle.action_cost(action_map[pred_action], state) > 500:
               ranked_actions = ranked_actions[1:]
               pred_action, best_score = ranked_actions[0]
            gold_action = None
            for i,(act, score) in enumerate(ranked_actions):
               cost = oracle.action_cost(action_map[act], state)
               if cost == 0:
                  gold_action = act
                  need_update = (i > 0)
                  break
            if need_update:
               assert(gold_action is not None)
               params.add(fs, gold_action, 1.0)
               params.add(fs, pred_action, -1.0)
            else:
               gold_action = pred_action

            if (oracle.correct_everywhere() and explore_policy and explore_policy.should_explore(iter_number)):
               state.do_action(action_map[pred_action])
            else:
               state.do_action(action_map[gold_action])
   return action_map, params

if __name__ == '__main__':
   import sys
   import pickle
   import isprojective
   from pio import io
   from explore_policies import *
   from arceager import ArcEagerState
   from dynamicoracles import ArcEagerDynamicOracle_fixed
   import features.extractors

   sents = [s for s in list(io.conll_to_sents(file(sys.argv[1]))) if isprojective.is_projective(s)]
   labels = set()
   for sent in sents:
      for tok in sent:
         labels.add(tok['prel'])

   action_map, params = online_greedy_train(
         sents,
         transition_system=ArcEagerState,
         oracle=ArcEagerDynamicOracle_fixed(),
         feature_extractor=features.extractors.get("eager.zn"),
         labels=labels,
         iterations=2,
         explore_policy=ExplorePolicy(2, 0.9),
         random_seed=1,
         shuffle_corpus=True)

   params.finalize()
   TRAIN_OUT_FILE = "model"
   params.dump(file(TRAIN_OUT_FILE,"w"), sparse=True)
   pickle.dump(action_map, file(TRAIN_OUT_FILE+".amap","w"))
