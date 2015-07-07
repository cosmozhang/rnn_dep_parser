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

from common import SHIFT,POP,REDUCE_R,REDUCE_L
from dynamicoracles import ArcEagerDynamicOracle_fixed, ArcHybridDynamicOracle
from archybrid import ArcHybridState

def rightmost_dep(tokid, sent):
   for m in reversed(sent):
      if m['parent'] == tokid: return m['id']
   return -1

class ArcEagerStaticOracle(ArcEagerDynamicOracle_fixed):
   def correct_everywhere(self): return False
   def action_cost(self, action, state):
      stack, deps, sent, i = state.stack, state.deps, state.sent, state.i
      action, label = action
      return self.labeled_action_cost(action, label, state, stack, deps, sent, i)
   def labeled_action_cost(self, action, label, state, stack, deps, sent, i):
      valid_actions = state.valid_actions()
      if action not in valid_actions: return 1000
      if stack and sent[i:] and sent[stack[-1]]['parent'] == i or (stack and i < len(sent) and sent[i]['id'] == 0 and sent[stack[-1]]['parent'] == 0):
         gaction = REDUCE_L
         glabel  = sent[stack[-1]]['prel']
      elif stack and sent[i:] and sent[i]['parent'] == stack[-1]:
         gaction = REDUCE_R
         glabel  = sent[i]['prel']
      elif stack and deps.has_parent(sent[stack[-1]]) and rightmost_dep(stack[-1], sent) < i:
         gaction = POP
         glabel = None
      else:
         gaction = SHIFT
      if action == gaction:
         if action in [SHIFT,POP]: return 0
         if glabel == label: return 0
         return 0.5
      else: return 1

class ArcHybridStaticOracle(ArcHybridDynamicOracle):
   def correct_everywhere(self): return False
   def action_cost(self, action, state):
      stack, deps, sent, i = state.stack, state.deps, state.sent, state.i
      action, label = action
      return self.labeled_action_cost(action, label, state, stack, sent, i)
   def labeled_action_cost(self, action, label, state, stack, sent, i):
      if action not in state.valid_actions(): return 1000
      if stack and sent[stack[-1]]['parent'] == i:
         golda = REDUCE_L
         goldl = sent[stack[-1]]['prel']
      elif len(stack) > 1 and sent[stack[-1]]['parent'] == stack[-2] and rightmost_dep(stack[-1], sent) < i:
            golda = REDUCE_R
            goldl = sent[stack[-1]]['prel']
      else:
         golda = SHIFT

      if action == golda:
         if action == SHIFT: return 0
         if label == goldl: return 0
         return 1
      return 1
