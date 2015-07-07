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

from parserstate import ParserState, DependenciesCollection
from common import *
from collections import defaultdict
from itertools import count

class ArcStandardState: #{{{
   def __init__(self, sent, init=True):
      if init:
         self.heads = [None] * len(sent)
         self.right = [None] * len(sent)
         self.left = [None] * len(sent)
      else:
         self.heads = None
         self.right = None
         self.left = None
      self.stack = []
      self.i = 0
      self.sent = sent
      self.acts = []

   @classmethod
   def CreateInitialState(self, sent):
      return ArcStandardState.init(sent)

   @classmethod
   def get_action_map(self, labels):
      return LightArcStandardState.get_action_map(labels)

   def core_elements(self):
      s0 = self.stack[-1] if self.stack else None
      s1 = self.stack[-2] if len(self.stack) > 1 else None
      s0l = self.left[s0] if s0 is not None else None
      s0r = self.right[s0] if s0 is not None else None
      s1l = self.left[s1] if s1 is not None else None
      s1r = self.right[s1] if s1 is not None else None
      s2 = self.stack[-3] if len(self.stack) > 2 else None
      return (self.i,s0,s0l,s0r,s1,s1l,s1r,s2)

   def valid_actions(self):
      stack = self.stack
      s0 = self.stack[-1] if stack else None
      s1 = self.stack[-2] if len(stack) > 1 else None
      actions = []
      if s0 != None: # has stack
         if s1 != None:
            if s1 != 0: actions.append(REDUCE_L)
            actions.append(REDUCE_R)
      if self.i < len(self.sent):
         actions.append(SHIFT)
      return actions

   def is_in_finish_state(self, strict=False):
      return self.stack[-1] == 0 and self.i >= len(self.sent)

   @classmethod
   def initial(self, sent):
      init = ArcStandardState(sent)
      init.stack = [0]
      init.i = 1
      return init

   def do_shift(self, label = None):
      self.acts.append((SHIFT,label))
      self.stack.append(self.i)
      self.i += 1

   def do_reduceL(self, label = None):
      self.acts.append((REDUCE_L,label))
      s0 = self.stack.pop()
      s1 = self.stack.pop()
      self.stack.append(s0)
      self.left[s0] = s1
      self.heads[s1] = s0

   def do_reduceR(self, label = None):
      self.acts.append((REDUCE_R,label))
      s0 = self.stack.pop()
      s1 = self.stack[-1]
      self.right[s1] = s0
      self.heads[s0] = s1

   def stack(self):
      return self.stack

   def actions(self):
      return self.acts()

   def arcs(self):
      return [(h,m,'dep') for m,h in enumerate(self.heads)]

   def clone(self):
      new = ArcStandardState(self.sent,init=False)
      new.i = self.i
      new.heads = self.heads[:]#list(self.heads)
      new.left = self.left[:]#list(self.left)
      new.right = self.right[:]#list(self.right)
      new.stack = self.stack[:]#list(self.stack)
      new.acts = self.acts[:]#list(self.acts)
      return new

   def newAfter(self, action):
      act, label = action
      s = self.clone()
      if act == SHIFT: s.do_shift()
      if act == REDUCE_R: s.do_reduceR(label)
      if act == REDUCE_L: s.do_reduceL(label)
      return s

   def deps(self):
      return DepsAnnotator(self)

   def sig1(self): 
      stack = self.stack
      s0 = stack[-1] if stack else None
      s1 = stack[-2] if len(stack) > 1 else None
      s2 = stack[-3] if len(stack) > 2 else None
      s0l = self.left[s0] if s0 is not None else None
      s1l = self.left[s1] if s1 is not None else None
      s1r = self.right[s1] if s1 is not None else None
      return s0,s1,s2,s1l,s1r,s0l
   def sig2(self): return (self.i,)

   def pp(self):
      ps1 = "(%s)" % self.sent[self.stail.s0]['parent'] if self.s0 != 0 else 'x'
      ps0 = "(%s)" % self.sent[self.s0]['parent']
      return " ".join(map(str,(self.stail.s0,ps1,self.s0,ps0,"|",self.i,len(self.sent))))
   #}}}

class LightArcStandardState(object): #{{{
   # all items = idx
   __slots__ = "cost","prev","i","stail","s0","s0l","s0r","action","sent","empty"
   empty = None
   def __init__(self,
         cost,prev,i,stail,s0,s0l,s0r,action,sent):
         self.cost = cost
         self.prev = prev
         self.i = i
         self.stail = stail
         self.s0 = s0
         self.s0l = s0l
         self.s0r = s0r
         self.action = action
         self.sent = sent

   @classmethod
   def CreateInitialState(self, sent):
      return LightArcStandardState.initial(sent)

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

   def core_elements(self):
      return (self.i,self.s0,self.s0l,self.s0r,self.stail.s0,self.stail.s0l,self.stail.s0r,self.stail.stail.s0)

   def valid_actions(self):
      s0 = self.s0
      actions = []
      if s0 != None: # has stack
         if self.stail.s0 != None:
            if self.stail.s0 != 0: actions.append(REDUCE_L)
            actions.append(REDUCE_R)
      if self.i < len(self.sent):
         actions.append(SHIFT)
      return actions

   def is_in_finish_state(self, strict=False):
      return self.s0 == 0 and self.i >= len(self.sent)

   @classmethod
   def initial(self, sent):
      if not self.empty:
         empty_stack = self(0, None, -1, None, None, None, None, None, None)
         empty_stack.stail = empty_stack
         self.empty = empty_stack

      init = self(0, None, 1, self.empty, 0, None, None, None, sent)
      return init

   def do_shift(self, label = None):
      return LightArcStandardState(self.cost, self, self.i+1, self, self.i, None, None, SHIFT, self.sent)

   def do_reduceL(self, label = None):
      return LightArcStandardState(self.cost, self, self.i, self.stail.stail, self.s0, self.stail.s0, self.s0r, REDUCE_L, self.sent)

   def do_reduceR(self, label = None):
      s0 = self.s0
      s1 = self.stail.s0
      s1l = self.stail.s0l
      return LightArcStandardState(self.cost, self, self.i, self.stail.stail, s1, s1l, s0, REDUCE_R, self.sent)

   def stack(self):
      if self.stail == self:
         return [(self.s0,self.s0l,self.s0r)]
      else:
         return self.stail.stack() + [(self.s0,self.s0l,self.s0r)]

   def actions(self):
      if self.prev == None: return []
      return self.prev.actions() + [(self.action,'dep' if self.action != 0 else None)]

   def arcs(self):
      arcs = []
      a = arcs.append
      p = self.prev
      while p != None:
         if p.action == REDUCE_R: a((p.s0,p.s0r,'dep'))
         elif p.action == REDUCE_L: a((p.s0,p.s0l,'dep'))
         p = p.prev
      return arcs
      if self.prev == None: return []
      if self.action == REDUCE_R: return self.prev.arcs() + [(self.s0, self.s0r,'dep')]
      if self.action == REDUCE_L: return self.prev.arcs() + [(self.s0, self.s0l,'dep')]
      return self.prev.arcs()

   def newAfter(self, action):
      act, label = action
      if act == SHIFT: return self.do_shift()
      if act == REDUCE_R: return self.do_reduceR(label)
      if act == REDUCE_L: return self.do_reduceL(label)
      raise Exception("Unknown action %s" % act)

   def deps(self):
      return DepsAnnotator(self)

   def sig1(self): return self.s0,self.stail.s0,self.stail.stail.s0,self.stail.s0l,self.stail.s0r,self.s0l
   def sig2(self): return (self.i,)

   def pp(self):
      ps1 = "(%s)" % self.sent[self.stail.s0]['parent'] if self.s0 != 0 else 'x'
      ps0 = "(%s)" % self.sent[self.s0]['parent']
      return " ".join(map(str,(self.stail.s0,ps1,self.s0,ps0,"|",self.i,len(self.sent))))
   #}}}

from arceager import DepsAnnotator
