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

from parserstate import ParserState
from collections import defaultdict
from itertools import count
from common import *

class ArcHybridState(ParserState): #{{{
   """
   ArcHybrid parsing algorithm
      SHIFT     s] [b b2     ==> s b] [b2
      REDUCE_L  s2 s1] [b    ==> s2] [b         (b,s1)
      REDUCE_R  s2 s1] [b    ==> s2] [b          (s2,s1)
   """

   @classmethod
   def CreateInitialState(self, sent):
      return ArcHybridState(sent)

   @classmethod
   def get_action_map(self, labels):
      nactions = 1 + (2*len(labels))
      action_map = defaultdict(count().next)
      action_map[(SHIFT, None)]
      for label in labels:
         action_map[(REDUCE_R, label)]
         action_map[(REDUCE_L, label)]
      action_map = dict(action_map)
      for (k,v) in action_map.items():
         action_map[v] = k
      return nactions, action_map

   def is_in_finish_state(self):
      #return len(self.stack) == 1 and not self.sent[self.i:]
      return (not self.sent[self.i:]) and self.stack == [0]

   def actions_map(self):
      return {SHIFT:self.do_shift, REDUCE_R: self.do_reduceR, REDUCE_L:self.do_reduceL}

   def do_shift(self, label=None):
      #print "SHIFT"
      if not (self.sent[self.i:]): raise IllegalActionException()
      self.actions.append((SHIFT, None))
      self._features=[]
      self.stack.append(self.i)
      self.i+=1

   def do_reduceR(self, label=None):
      #print "R"
      if len(self.stack) < 2: raise IllegalActionException()
      self.actions.append((REDUCE_R, label))
      self._features=[]
      stack=self.stack
      deps=self.deps
      sent=self.sent

      # attach the tokens, keeping having both on the stack
      parent = sent[stack[-2]]
      child  = sent[stack[-1]]
      if deps.has_parent(child): raise IllegalActionException()
      deps.add(parent, child, label)
      stack.pop()

   def do_reduceL(self, label=None):
      #print "L"
      if len(self.stack) < 1: raise IllegalActionException()
      if len(self.sent) <= self.i: raise IllegalActionException()
      self.actions.append((REDUCE_L, label))
      self._features=[]
      stack=self.stack
      deps=self.deps
      sent=self.sent

      # add top-of-stack as child of sent, pop stack
      child = sent[stack[-1]]
      parent = sent[self.i] 
      if deps.has_parent(child): raise IllegalActionException() 
      stack.pop()
      deps.add(parent, child, label)  

   def valid_actions(self):
      res=[SHIFT,REDUCE_R,REDUCE_L]
      if not (self.sent[self.i:]):
         res.remove(SHIFT)
      if len(self.stack) < 2: 
         res.remove(REDUCE_R)
      if len(self.stack) < 1:
         res.remove(REDUCE_L)
      if self.stack and self.stack[-1] == 0:
         res.remove(REDUCE_L)
      elif len(self.sent) <= self.i: 
         res.remove(REDUCE_L)
      return res
#}}}


