## Copyright 2013 Yoav Goldberg
#
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

from common import *

class ArcEagerDynamicOracle_fixed: # {{{
   def correct_everywhere(self): return True

   def action_cost(self, action, state): #{{{
      stack, deps, sent, i = state.stack, state.deps, state.sent, state.i
      action, label = action
      if label == '_': label = None
      valids = state.valid_actions()
      if action not in valids: return 1000
      #action, label = self.action_map[action]
      lost = 0
      if action == SHIFT:
         # i can no longer have children or parents on stack.
         for s in stack:
            # fix 1
            if sent[s]['parent'] == i and not deps.has_parent(sent[s]):
               lost += 1
            if sent[i]['parent'] == s:
               if s != 0: # if real parent is ROOT and is on stack,
                          # we will get it by post-proc the end.
                  lost += 1
      elif action == POP:
         # stack[-1] can no longer have deps on buffer
         top = stack[-1]
         for tok in sent[i:]:
            if tok['parent'] == top:
               lost += 1
      elif action == REDUCE_L:
         # stack[-1] can no longer have deps on buffer
         # stack[-1] can no longer have parents on buffer[1:]
         top = stack[-1]
         # lose the root parent when assigning a wrong parent, if we use root-at-start + post-proc.
         # this should NOT fire for the root-at-end case.
         if sent[top]['parent'] == 0 and stack and stack[0] == 0:
            lost += 1
         for (idx, tok) in enumerate(sent[i:]):
            if sent[top]['parent'] == tok['id']:
               if (idx > 0):
                  lost += 1
               elif label and sent[top]['prel'] != label:# and sent[top]['prel'] != 'dep': # idx == 0
                  lost += 1
                  pass
            if tok['parent'] == top:
               lost += 1
      elif action == REDUCE_R:
         # i can no longer have parents in stack[:-1]
         # i can no longer have deps in stack
         # i can no longer have parents in buffer
         ipar = sent[i]['parent']
         for s in stack:
            # fix 2
            if sent[s]['parent'] == i and not deps.has_parent(sent[s]):
               lost += 1
            if (ipar == s):
               if s != stack[-1]:
                  lost += 1
               elif label and sent[i]['prel'] != label:# and sent[i]['prel'] != 'dep':
                  pass
                  lost += 1
         # If root-at-end representation, lose the correct parent of i if it is root.
         if ipar > i or (ipar == 0 and stack and stack[0] != 0):
            lost += 1
      else:
         assert(False), ("Invalid action", action)
      #print "action",action,"loss",lost
      return lost 
   #}}}

   def lost_arcs(self, action, state): #{{{
      stack, deps, sent, i = state.stack, state.deps, state.sent, state.i
      action, label = action
      if label == '_': label = None
      valids = state.valid_actions()
      if action not in valids: return None # Illegal
      lost = []
      if action == SHIFT:
         # i can no longer have children or parents on stack.
         for s in stack:
            # fix 1
            if sent[s]['parent'] == i and not deps.has_parent(sent[s]):
               lost.append((i,sent[s]['prel'],s))
            if sent[i]['parent'] == s:
               if s != 0: # if real parent is ROOT and is on stack,
                          # we will get it by post-proc the end.
                          # this should not fire with root-at-end,
                          # where no post-proc should be done.
                  lost.append((s,sent[i]['prel'],i))
      elif action == POP:
         # stack[-1] can no longer have deps on buffer
         top = stack[-1]
         for tok in sent[i:]:
            if tok['parent'] == top:
               lost.append((top,tok['prel'],tok['id']))
      elif action == REDUCE_L:
         # stack[-1] can no longer have deps on buffer
         # stack[-1] can no longer have parents on buffer[1:]
         top = stack[-1]
         assert(top != 0),valids
         # lose the root parent when assigning a wrong parent, if we use root-at-start + post-proc.
         # this should NOT fire for the root-at-end case.
         if sent[top]['parent'] == 0 and stack and stack[0] == 0:
            lost.append((0,sent[top]['prel'],sent[top]['id']))
         for (idx, tok) in enumerate(sent[i:]):
            if sent[top]['parent'] == tok['id']:
               if (idx > 0):
                  lost.append((tok['id'],sent[top]['prel'],top))
               elif label and sent[top]['prel'] != label:# and sent[top]['prel'] != 'dep': # idx == 0
                  #print "y",sent[top]['parent'],sent[top]['prel'],top
                  lost.append((sent[top]['parent'],sent[top]['prel'],top))
            if tok['parent'] == top:
               lost.append((top,tok['prel'],tok['id']))
      elif action == REDUCE_R:
         # i can no longer have parents in stack[:-1]
         # i can no longer have deps in stack
         # i can no longer have parents in buffer
         for s in stack:
            # fix 2
            if sent[s]['parent'] == i and not deps.has_parent(sent[s]):
               lost.append((i,sent[s]['prel'],s))
            if (sent[i]['parent'] == s):
               if s != stack[-1]:
                  lost.append((s,sent[i]['prel'],i))
               elif label and sent[i]['prel'] != label:# and sent[i]['prel'] != 'dep':
                  #print "x",sent[i]['parent'],sent[i]['prel'],i
                  lost.append((sent[i]['parent'],sent[i]['prel'],i))
         # If root-at-end representation, lose the correct parent of i if it is root.
         ipar = sent[i]['parent']
         if ipar > i or (ipar == 0 and stack and stack[0] != 0):
            lost.append((sent[i]['parent'],sent[i]['prel'],i))
      else:
         assert(False), ("Invalid action", action)
      #print "action",action,"loss",lost
      return lost 
   #}}}
#}}}

            
ArcEagerDynamicOracle = ArcEagerDynamicOracle_fixed
            
class ArcHybridDynamicOracle: #{{{
   #
   # top of buffer can have children from stack.
   # top of stack can have parents from buffer and one before it on the stack.
   # once one is shifted, its parent must be either on buffer, or top of stack.
   #                      its child must be on the buffer
   def correct_everywhere(self): return True
   def action_cost(self, action, state):
      stack, deps, sent, i = state.stack, state.deps, state.sent, state.i
      action, label = action
      #action, label = self.action_map[action]
      lost = 0
      if action == SHIFT:
         if i >= len(sent): return 1000
         # i can no longer have children on the stack
         # i can no longer have a prent on stack[:-1]
         for s in stack[:-1]:
            if sent[s]['parent'] == i:
               lost += 1
            if sent[i]['parent'] == s:
               lost += 1
         if stack and sent[stack[-1]]['parent'] == i:
            lost += 1
      elif action == REDUCE_L:
         if len(sent) <= i: return 1000
         if not stack: return 1000
         if stack[-1] == 0: return 1000
         #if deps.has_parent(sent[stack[-1]]): return 1000 SHOULD NOT HAPPEN
         # stack[-1] can no longer have deps on buffer
         # stack[-1] can no longer have parents on buffer[1:]
         # stack[-1] can no longer have parents on stack[-2]
         top = stack[-1]
         for (idx, tok) in enumerate(sent[i:]):
            if sent[top]['parent'] == tok['id']:
               if (idx > 0):
                  lost += 1
               #elif label and (sent[top]['prel'] != label) and sent[top]['prel'] != 'dep': # idx == 0
               elif label and (sent[top]['prel'] != label):
                  lost += 1
            if tok['parent'] == top:
               lost += 1
         if len(stack) > 1:
            if sent[top]['parent'] == stack[-2]:
               lost += 1
         #if lost == 0: assert(sent[top]['parent'] == i)
      elif action == REDUCE_R:
         #if i >= len(sent): return 1000
         if len(stack) < 2: return 1000
         # top can no longer have parents in buffer
         # top can no longer have children in buffer
         top = sent[stack[-1]]
         if top['parent'] >= i: lost += 1
         for mod in sent[i:]:
            if mod['parent'] == top['id']: lost += 1
         if top['parent'] == stack[-2]:
            #if label and top['prel'] != label and (top['prel'] != 'dep'):
            if label and top['prel'] != label:
               lost += 1
            else:
               pass
               #print "correct parent, but:",label, top['prel']
         #if lost == 0: assert(top['parent'] == stack[-2])
      else:
         assert(False), ("Invalid action", action)
      return lost
# }}}

