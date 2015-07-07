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
Transition based parsing (both arc-hybrid and arc-eager).
Easily extended to support other variants.
"""
from collections import defaultdict
import sys
import copy
import random
from itertools import izip, count
from ml import sml as ml
from dynamicoracles import *
from staticoracles import *
from arceager import *
from archybrid import *

#from features.extractors import *
from common import *


### misc / pretty print / temp junk #{{{

def _ids(tok):
   if tok['id']==0: tok['form']='ROOT'
   return (tok['id'],tok['tag'])
#}}}


######

### the parser #{{{

class TransitionBasedParser: #{{{

   def __init__(self, params, transition_system, fext):
      self.params = params
      self.fext = fext
      self.transition_system = transition_system
      pass

   def decide(self, conf):
      fs = self.fext.extract(conf.stack, conf.deps, conf.sent, conf.i)
      action,scores = self.params.predict(fs)
      scores = dict(enumerate(scores))  # [-122, 0.3, 3] -> {0:-122, 1:0.3, 2:3} 
      actions = [item for item,score in sorted(scores.items(),key=lambda x:-x[1])]
      return actions

   def train(self, corpus, oracle, iterations, explore_policy):
      """
      Oracle must support the action_cost() method.
      """
      featExt = self.fext
      params = self.params
      oracle.action_map = action_map = self.action_map
      for iter_number in xrange(iterations):
         updates = 1.0
         steps = 1.0
         print >> sys.stderr,"iter", iter_number
         random.shuffle(corpus)
         for sid, sent in enumerate(corpus):
            if sid % 1000 == 0:
               print "steps:",steps
               print sid, steps, updates, updates / float(steps)
            sent = [ROOT] + sent
            state = self.transition_system.CreateInitialState(sent)
            while not state.is_in_finish_state():
               params.tick()
               steps += 1
               fs = featExt.extract(state.stack, state.deps, state.sent, state.i)
               action_scores = params.get_scores(fs)
               ranked_actions = list(sorted(action_scores.items(),key=lambda x:-x[1]))
               pred_action, best_score = ranked_actions[0]
               while oracle.action_cost(action_map[pred_action], state.stack, state.deps, state.sent, state.i) > 500:
                  ranked_actions = ranked_actions[1:]
                  pred_action, best_score = ranked_actions[0]
               gold_action = None
               for i,(act, score) in enumerate(ranked_actions):
                  cost = oracle.action_cost(action_map[act], state.stack, state.deps, state.sent, state.i)
                  if cost == 0:
                     gold_action = act
                     need_update = (i > 0)
                     break
               if need_update:
                  updates += 1
                  assert(gold_action is not None)
                  params.add(fs, gold_action, 1.0)
                  params.add(fs, pred_action, -1.0)
               else:
                  gold_action = pred_action

               if (oracle.correct_everywhere() and explore_policy.should_explore(iter_number)):
                  state.do_action(action_map[pred_action])
               else:
                  state.do_action(action_map[gold_action])
      return None

   def train_repairs(self, corpus, oracle, iterations, explore_policy):
      """
      Oracle must support the action_cost() method.
      """
      oracle = ArcEagerDynamicOracle()
      roracle = HGJDynamicOracle()
      featExt = self.fext
      params = self.params
      roracle.action_map = action_map = self.action_map
      oracle.action_map = action_map = self.action_map
      for iter_number in xrange(iterations):
         updates = 1.0
         steps = 1.0
         print >> sys.stderr,"iter", iter_number
         random.shuffle(corpus)
         for sid, sent in enumerate(corpus):
            if sid % 1000 == 0:
               print "steps:",steps
               print sid, steps, updates, updates / float(steps)
            sent = [ROOT] + sent
            state = self.transition_system.CreateInitialState(sent)
            while not state.is_in_finish_state():
               params.tick()
               steps += 1
               fs = featExt.extract(state.stack, state.deps, state.sent, state.i)
               action_scores = params.get_scores(fs)
               ranked_actions = list(sorted(action_scores.items(),key=lambda x:-x[1]))
               pred_action, best_score = ranked_actions[0]
               while roracle.action_cost(pred_action, state.stack, state.deps, state.sent, state.i) > 500:
                  ranked_actions = ranked_actions[1:]
                  pred_action, best_score = ranked_actions[0]
               gold_action = None
               gold_action2 = None
               no_repair_0_cost = set([a for (a,s) in ranked_actions if oracle.action_cost(a,state.stack,state.deps,state.sent,state.i) == 0])
               wt_repair_0_cost = set([a for (a,s) in ranked_actions if roracle.action_cost(a,state.stack,state.deps,state.sent,state.i) == 0])
               zero_cost = wt_repair_0_cost.intersection(no_repair_0_cost)
               if not zero_cost: zero_cost = wt_repair_0_cost
               for i,(act, score) in enumerate(ranked_actions):
                  if act in zero_cost:
                     gold_action = act
                     need_update = (i > 0)
                     break
               if need_update:
                  updates += 1
                  if gold_action is None: gold_action = gold_action2
                  assert(gold_action is not None)
                  params.add(fs, gold_action, 1.0)
                  params.add(fs, pred_action, -1.0)
               else:
                  gold_action = pred_action

               if (oracle.correct_everywhere() and explore_policy.should_explore(iter_number)):
                  state.do_action(action_map[pred_action])
               else:
                  state.do_action(action_map[gold_action])
      return None

   def parse(self, sent):
      nactions = len(self.action_map.keys()) / 2
      sent = [ROOT] + sent
      state = self.transition_system.CreateInitialState(sent)
      while not state.is_in_finish_state():
         next_actions = self.decide(state)
         for act in next_actions:
            try:
               # TODO: action_cost --> action_valid
               valid_actions = state.valid_actions()
               if self.action_map[act][0] not in valid_actions:
                  continue
               #if cost > 0: continue
               #print "cost:",cost
               #if (cost > 0): print "XX",self.action_map[act],cost,[self.action_map[a] for a in range(nactions) if oracle.action_cost(a, state.stack, state.deps, state.sent, state.i) == 0]
               state.do_action(self.action_map[act])
               #state = state.newAfter(self.action_map[act])
               break
            except IllegalActionException:
               print "IllegalAction", act
               pass
      return state.deps#,conf.chunks

   def get_a_gold_derivation(self, sent, oracle):
      oracle.action_map = self.action_map
      nactions = len(self.action_map.keys()) / 2
      sent = [ROOT] + sent
      state = self.stateiguration(sent)
      derivation = []
      cost = 0
      while not state.is_in_finish_state():
         valid_actions = [a for a in xrange(nactions) if
                           oracle.action_cost(
                              a, state.stack, state.deps, state.sent, state.i) == 0]

         costs = [oracle.action_cost(
                              a, state.stack, state.deps, state.sent, state.i)
                              for a in xrange(nactions)]
         print "C",max([c for c in costs if c < 500])
         if (random.random() > 1):
            valid_actions =[a for a in xrange(nactions) if
                  oracle.action_cost(
                     a, state.stack, state.deps, state.sent, state.i) < 100]
         #if len(valid_actions) > 5:
         #   print set([self.action_map[a][1] for a in valid_actions])
         #   print state.stack[-2], state.stack[-1], sent[state.stack[-1]]['parent'], sent[state.stack[-1]]['prel']
         assert(valid_actions),(state.i, state.stack, len(state.sent))
         next_action = random.choice(valid_actions)
         cost += oracle.action_cost(next_action, state.stack, state.deps, state.sent, state.i)
         derivation.append(next_action)
         state.do_action(self.action_map[next_action])
      return derivation, cost, state.deps#,state.chunks

   def get_a_random_derivation(self, sent, oracle, non_optimal_prob = 0.5):
      oracle.action_map = self.action_map
      nactions = len(self.action_map.keys()) / 2
      sent = [ROOT] + sent
      state = self.transition_system.CreateInitialState(sent)
      derivation = []
      cost = 0
      while not state.is_in_finish_state():
         action_costs = [(a,oracle.action_cost(a, state.stack, state.deps, state.sent, state.i))
               for a in xrange(nactions)]
         valid_actions = [(a,c) for a,c in action_costs if c == 0]
         assert(valid_actions),(state.i, state.stack, len(state.sent), [(a,oracle.action_cost(a, state.stack, state.deps, state.sent, state.i, True)) for a in xrange(nactions)],[t['parent'] for t in sent])
         other_actions = [(a,c) for a,c in action_costs if c > 0 and c < 500]
         if not(other_actions): other_actions = valid_actions
         if (random.random() > non_optimal_prob):
            next_action,c = random.choice(other_actions)
         else:
            next_action,c = random.choice(valid_actions)
         cost += c
         derivation.append(next_action)
         #print "next_action",next_action,c,oracle.action_cost(next_action, state.stack,state.deps,state.sent,state.i,True)
         state.do_action(self.action_map[next_action])
      return derivation, cost, state.deps#,state.chunks


def ArcEagerParser(params, fext):
   return TransitionBasedParser(params, ArcEagerState, fext)

def NonMonotonicArcEagerParser(params, fext):
   return TransitionBasedParser(params, NonMonotonicArcEagerTransitionSystem(), fext)

def ArcHybridParser(params, fext):
   return TransitionBasedParser(params, ArcHybridState, fext)

