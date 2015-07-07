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
from common import *
from collections import defaultdict
from itertools import count

class ArcEagerState(ParserState): #{{{
   """
   Nivre's ArcEager parsing algorithm
   with slightly different action names:

      Nivre's        ThisCode
      ========================
      SHIFT          SHIFT
      ARC_L          REDUCE_L
      ARC_R          REDUCE_R
      REDUCE         POP

   """
   @classmethod
   def CreateInitialState(self, sent):
      return ArcEagerState(sent)

   @classmethod
   def get_action_map(self, labels):
      nactions = 2 + (2*len(labels))
      action_map = defaultdict(count().next)
      action_map[(POP, None)]
      action_map[(SHIFT, None)]
      for label in labels:
         action_map[(REDUCE_R, label)]
         action_map[(REDUCE_L, label)]
      action_map = dict(action_map)
      for (k,v) in action_map.items():
         action_map[v] = k
      return nactions, action_map

   def is_in_finish_state(self, strict=False):
      if strict:
         return len(self.stack) == 1 and not self.sent[self.i:]
      else:
         return not self.sent[self.i:]

   def actions_map(self):
      return {SHIFT:self.do_shift, REDUCE_R: self.do_reduceR, REDUCE_L:self.do_reduceL, POP:self.do_pop}

   def do_shift(self, label=None):
      #print "SHIFT"
      if not (self.sent[self.i:]): raise IllegalActionException()
      self.actions.append((SHIFT, None))
      self._features=[]
      self.stack.append(self.i)
      self.i+=1

   def do_reduceR(self, label=None):
      #print "R"
      if len(self.stack) < 1: raise IllegalActionException()
      if len(self.sent) <= self.i: raise IllegalActionException()
      self.actions.append((REDUCE_R, label))
      self._features=[]
      stack=self.stack
      deps=self.deps
      sent=self.sent

      # attach the tokens, keeping having both on the stack
      parent = self.sent[stack[-1]]
      child = sent[self.i] 
      if deps.has_parent(child): raise IllegalActionException()
      #print "addingR",child['id'], parent['id']
      deps.add(parent, child, label)
      #print "parent is:",deps.parent(child)['id']
      self.stack.append(self.i)
      self.i+=1

   def do_reduceL(self, label=None):
      #print "L"
      if len(self.stack) < 1: raise IllegalActionException()
      if len(self.sent) <= self.i: raise IllegalActionException()
      if self.stack[-1] == 0: raise IllegalActionException()
      self.actions.append((REDUCE_L, label))
      self._features=[]
      stack=self.stack
      deps=self.deps
      sent=self.sent

      # add top-of-stack as child of sent, pop stack
      child = self.sent[stack[-1]]
      parent = sent[self.i] 
      if deps.has_parent(child): raise IllegalActionException() 
      stack.pop()
      #print "addingL",child['id'], parent['id']
      deps.add(parent, child, label)  
      #print "parent is:",deps.parent(child)['id']

   def do_pop(self, label=None):
      stack=self.stack

      if len(stack) == 0: raise IllegalActionException()
      if self.sent[self.i:]:
         ## also illegal to pop when the item to be popped does not have a parent. (can this happen? yes, right after a shift..)
         if not self.deps.has_parent(self.sent[stack[-1]]): 
            if self.sent[stack[-1]]['parent']!=-1: 
               pass
               #raise IllegalActionException() 
         
      self.actions.append((POP, label))
      self._features=[]

      stack.pop()
   
   def valid_actions(self):
      res=[SHIFT,REDUCE_R,REDUCE_L,POP]

      if not (self.sent[self.i:]): res.remove(SHIFT)

      if len(self.stack) == 0: res.remove(POP)
      elif (self.sent[self.i:]):
         if not self.deps.has_parent(self.sent[self.stack[-1]]): res.remove(POP)

      if self.stack and self.stack[-1] == 0: res.remove(REDUCE_L)
      if len(self.stack) < 1: 
         res.remove(REDUCE_L)
         res.remove(REDUCE_R)
      elif len(self.sent) <= self.i: 
         res.remove(REDUCE_L)
         res.remove(REDUCE_R)
      else:
         if self.deps.has_parent(self.sent[self.stack[-1]]): res.remove(REDUCE_L)
         if self.deps.has_parent(self.sent[self.i]): res.remove(REDUCE_R)

      return res

#}}}

class RootAtEndArcEagerState(ParserState): #{{{
   """
   Nivre's ArcEager parsing algorithm
   with slightly different action names:

      Nivre's        ThisCode
      ========================
      SHIFT          SHIFT
      ARC_L          REDUCE_L
      ARC_R          REDUCE_R
      REDUCE         POP

   Here we use a representation in which ROOT is the last element on the buffer, instead of the first on the stack.
   For compatibility reasons, and to allow convenient indexing of tokens from sentence, our sentence representation
   is [ROOT, w1, ...,wn, ROOT]. The first root never enters the stack, as i starts at 1 and not at 0.

   It is assumed that the sentences passed to the CreateInitialState method already contain the ROOT token at the beginnng.
   """
   @classmethod
   def CreateInitialState(self, sent):
      assert(sent[0] == ROOT)
      sent = sent[:] + [sent[0]]
      s = RootAtEndArcEagerState(sent)
      s.i += 1
      return s

   @classmethod
   def get_action_map(self, labels):
      nactions = 2 + (2*len(labels))
      action_map = defaultdict(count().next)
      action_map[(POP, None)]
      action_map[(SHIFT, None)]
      for label in labels:
         action_map[(REDUCE_R, label)]
         action_map[(REDUCE_L, label)]
      action_map = dict(action_map)
      for (k,v) in action_map.items():
         action_map[v] = k
      return nactions, action_map

   def is_in_finish_state(self, strict=False):
      if strict:
         return len(self.stack) == 0 and len(self.sent[self.i:])==1
      else:
         return len(self.stack) == 0 and len(self.sent[self.i:])==1

   def actions_map(self):
      return {SHIFT:self.do_shift, REDUCE_R: self.do_reduceR, REDUCE_L:self.do_reduceL, POP:self.do_pop}

   def do_shift(self, label=None):
      #print "SHIFT"
      if not (self.sent[self.i:]): raise IllegalActionException()
      self.actions.append((SHIFT, None))
      self._features=[]
      self.stack.append(self.i)
      self.i+=1

   def do_reduceR(self, label=None):
      #print "R"
      if len(self.stack) < 1: raise IllegalActionException()
      if len(self.sent) <= self.i: raise IllegalActionException()
      self.actions.append((REDUCE_R, label))
      self._features=[]
      stack=self.stack
      deps=self.deps
      sent=self.sent

      # attach the tokens, keeping having both on the stack
      parent = self.sent[stack[-1]]
      child = sent[self.i] 
      if deps.has_parent(child): raise IllegalActionException()
      #print "addingR",child['id'], parent['id']
      deps.add(parent, child, label)
      #print "parent is:",deps.parent(child)['id']
      self.stack.append(self.i)
      self.i+=1

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
      child = self.sent[stack[-1]]
      parent = sent[self.i] 
      if deps.has_parent(child): raise IllegalActionException() 
      stack.pop()
      #print "addingL",child['id'], parent['id']
      deps.add(parent, child, label)  
      #print "parent is:",deps.parent(child)['id']

   def do_pop(self, label=None):
      stack=self.stack

      if len(stack) == 0: raise IllegalActionException()
      if self.sent[self.i:]:
         ## also illegal to pop when the item to be popped does not have a parent. (can this happen? yes, right after a shift..)
         if not self.deps.has_parent(self.sent[stack[-1]]): 
            if self.sent[stack[-1]]['parent']!=-1: 
               pass
               #raise IllegalActionException() 
         
      self.actions.append((POP, label))
      self._features=[]

      stack.pop()
   
   def valid_actions(self):
      res=[SHIFT,REDUCE_R,REDUCE_L,POP]

      if len(self.sent[self.i:])==1:
         assert(self.sent[self.i] == ROOT)
         res.remove(SHIFT)
         res.remove(REDUCE_R)

      if len(self.stack) == 0: res.remove(POP)
      elif (self.sent[self.i:]):
         if not self.deps.has_parent(self.sent[self.stack[-1]]): res.remove(POP)

      if len(self.stack) < 1: 
         res.remove(REDUCE_L)
         res.remove(REDUCE_R)
      else:
         if self.deps.has_parent(self.sent[self.stack[-1]]): res.remove(REDUCE_L)
         if self.deps.has_parent(self.sent[self.i]): res.remove(REDUCE_R)
      return res

#}}}

