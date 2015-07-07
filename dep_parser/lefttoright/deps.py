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

from collections import defaultdict
import copy
import sys

class RecursiveDeps:
   def __init__(self,prev=None,h=None,m=None,l=None):
      self.prev = prev
      self.h = h
      self.m = m
      self.l = l
   def add(self, parent_id, child_id, label=None):
      self.prev = RecursiveDeps(self, parent_id, child_id, label)
   def has_parent(self, tok_id):
      if self.m == tok_id: return True
      elif self.prev == None: return False
      else: return self.prev.has_parent(tok_id)


class IDBasedDependenciesCollection: #{{{
   # TODO: {left,right}_labels as bitmask instead of set.
   #__slots__ = "_left_child","_right_child","_left2_child","_right2_child","_parents","_labels","_childs","_num_left_children","num_right_children","_right_labels","_left_labels"
   def __init__(self):
      #self.deps = set()
      self._left_child = {}
      self._right_child = {}
      self._left2_child = {}
      self._right2_child = {}
      self._parents = {}
      self._labels = {}
      #self._childs = defaultdict(list)
      self._num_left_children = defaultdict(int)
      self._num_right_children = defaultdict(int)
      self._right_labels = defaultdict(list)
      self._left_labels = defaultdict(list)
   def clone(self):
      c = IDBasedDependenciesCollection()
      #c.deps = set(self.deps)
      c._left_child = copy.copy(self._left_child)
      c._right_child = copy.copy(self._right_child)
      c._left2_child = copy.copy(self._left2_child)
      c._right2_child = copy.copy(self._right2_child)
      c._parents = copy.copy(self._parents)
      c._labels = copy.copy(self._labels)
      #c._childs = copy.copy(self._childs)
      c._num_left_children = copy.copy(self._num_left_children)
      c._num_right_children = copy.copy(self._num_right_children)
      ### NOTE: must deep-copy because of list in dict.
      c._right_labels = defaultdict(list,((k,list(v)) for k,v in self._right_labels.iteritems()))
      c._left_labels = defaultdict(list,((k,list(v)) for k,v in self._left_labels.iteritems()))
      return c

   def add(self, parent_id, child_id, label=None):
      #print "adding parent",parent_id,"for",child_id
      if self.has_parent(child_id):
         old_parent = self._parents[child_id]
         #print "removing old parent",old_parent, "for",child_id
         self.remove(old_parent, child_id)
      #self.deps.add((parent_id, child_id))
      self._labels[child_id]=label
      self._parents[child_id]=parent_id
      #self._childs[parent_id].append(child_id)

      if child_id < parent_id:
         #lc_id = self.left_child(parent_id)
         lc_id = self._left_child.get(parent_id, -1)
         if (lc_id < 0) or child_id < lc_id:
            if lc_id > -1: self._left2_child[parent_id]=lc_id
            self._left_child[parent_id]=child_id
         self._left_labels[parent_id].append(label)
         self._num_left_children[parent_id] += 1

      elif child_id > parent_id:
         rc_id = self._right_child.get(parent_id,-1)
         if (rc_id < 0) or child_id > rc_id:
            if rc_id > -1: self._right2_child[parent_id]=rc_id
            self._right_child[parent_id]=child_id
         self._right_labels[parent_id].append(label)
         self._num_right_children[parent_id] += 1

# {{{ remove
   def remove(self, parent_id, child_id): #{{{
      pid = parent_id
      cid = child_id
      del self._labels[child_id]
      children = self.children(pid)
      children.remove(cid)
      #self.deps.remove((pid,cid))
      del self._parents[cid]
      self.recalculate_children()
   #}}}

   def recalculate_children(self): #{{{
      self._left_child = {}
      self._right_child = {}
      self._left2_child = {}
      self._right2_child = {}
      self._childs = defaultdict(list)
      self._num_left_children = defaultdict(int)
      self._num_right_children = defaultdict(int)
      self._right_labels = defaultdict(list)
      self._left_labels = defaultdict(list)
      for child_id, parent_id in self._parents.items():
         label = self._labels[child_id]
         self._childs[parent_id].append(child_id)
         if child_id < parent_id:
            lc_id = self.left_child(parent_id)
            if (lc_id < 0) or child_id < lc_id:
               self._left2_child[parent_id]=lc_id
               self._left_child[parent_id]=child_id
            self._left_labels[parent_id].append(label)
            self._num_left_children[parent_id] += 1
         else:
            rc_id = self.right_child(parent_id)
            if (rc_id < 0) or child_id > rc_id:
               self._right2_child[parent_id]=rc_id
               self._right_child[parent_id]=child_id
            self._right_labels[parent_id].append(label)
            self._num_right_children[parent_id] += 1
      #}}}

   def remove_parent(self,child_id):
      self.remove(self.parent(child_id),child_id)
   #}}}

# }}}

   def annotate(self, sent):
      for tok in sent:
         try: 
            tok['pparent'] = self._parents[tok['id']]
         except KeyError: 
            sys.stderr.write("Xdefaulting to root-parent")
            tok['pparent'] = 0
            tok['pprel'] = 'ROOT'
            continue
         try:
            tok['pprel'] = self._labels[tok['id']]
         except KeyError:
            sys.stderr.write("defaulting to root-parent(%s)" % self._parents[tok['id']])
            tok['pprel'] = 'ROOT'
      return sent

   def annotate_allow_none(self, sent):
      for tok in sent:
         try:
            tok['pparent'] = self._parents[tok['id']]
         except KeyError: 
            print "key error:",tok['id']
            tok['pparent'] = 0
         tok['pprel'] = self._labels[tok['id']]
      return sent

   def has_parent(self, child_id):
      return child_id in self._parents

   def label_for(self, child_id):
      return self._labels.get(child_id, None)

   def left_child(self, tok_id):
      if tok_id < 0: return None
      return self._left_child.get(tok_id, None)

   def right_child(self, tok_id):
      if tok_id < 0: return None
      return self._right_child.get(tok_id, None)

   def left2_child(self, tok_id):
      if tok_id < 0: return None
      return self._left2_child.get(tok_id, None)

   def right2_child(self, tok_id):
      if tok_id < 0: return None
      return self._right2_child.get(tok_id, None)

   #def children(self, tok_id):
   #   if tok_id < 0: return []
   #   return self._childs[tok_id]

   #def get_depth(self, tok_id):
   #   children = self.children(tok_id)
   #   if not children: return 1
   #   depths = [self.get_depth(c) for c in self.children(tok)]
   #   return max(depths)+1

   #def sibling(self, tok_id, i=1):
   #   if tok_id < 0: return -1
   #   parent_id = self._parents.get(tok_id,-1)
   #   self._childs[parent_id].sort()
   #   siblings = self._childs[parent_id]
   #   index = siblings.index(tok_id)
   #   if 0 < (index+i) < len(siblings):
   #      return siblings[index+i]
   #   return None

   def span(self, tok_id):
      return self.right_border(tok_id) - self.left_border(tok_id)

   def parent(self, tok_id):
      return self._parents[tok_id] if tok_id in self._parents else None

   def right_border(self,tok_id):
      r = self.right_child(tok_id)
      if not r: return tok_id
      else: return self.right_border(r)

   def left_border(self,tok_id):
      l = self.left_child(tok_id)
      if not l: return tok_id
      else: return self.left_border(l)

   def num_left_children(self, tok_id): return self._num_left_children[tok_id]

   def num_right_children(self, tok_id): return self._num_right_children[tok_id]

#}}}

class DependenciesCollection: #{{{
   def __init__(self, sent):
      self.deps = IDBasedDependenciesCollection()
      self.sent = sent

   def __deepcopy__(self, memo):
      c = self.__class__(self.sent)
      #c.deps = copy.deepcopy(self.deps, memo)
      c.deps = self.deps.clone()
      return c

   def has_parent(self, child): return self.deps.has_parent(child['id'])
   def label_for(self, child): return self.deps.label_for(child['id'])

   def add(self, parent, child, label=None): return self.deps.add(parent['id'],child['id'],label)

   def remove(self, parent, child): return self.deps.remove(parent['id'],child['id'])

   def remove_left_children(self, parent): return self.deps.remove_left_children(parent['id'])

   def remove_right_children(self,parent): return self.deps.remove_right_children(parent['id'])

   def remove_parent(self,child): return self.deps.remove_parent(child['id'])

   def annotate(self, sent): return self.deps.annotate(sent)

   def annotate_allow_none(self, sent): return self.deps.annotate_allow_none(sent)

   def left_child(self, tok):
      i = self.deps.left_child(tok['id'])
      return self.sent[i] if i is not None else None

   def right_child(self, tok):
      i = self.deps.right_child(tok['id'])
      return self.sent[i] if i is not None else None

   #def children(self, tok): return [self.sent[i] for i in self.deps.children(tok['id']) if i > -1]

   def get_depth(self, tok): return self.deps.depth(tok['id'])

   def sibling(self, tok, i=1): 
      sid = self.deps.sibling(tok['id'],i)
      if sid < 0: return None
      return self.sent[sid]

   def span(self, tok): return self.deps.span(tok['id'])

   def parent(self, tok): 
      pid = self.deps.parent(tok['id'])
      if pid < 0: return None
      return self.sent[pid]

   def right_border(self,tok):
      bid = self.deps.right_border(tok['id'])
      return self.sent[bid]

   def left_border(self,tok):
      bid = self.deps.left_border(tok['id'])
      return self.sent[bid]

   def num_right_children(self, tok):
      return self.deps.num_right_children(tok['id'])

   def num_left_children(self, tok):
      return self.deps.num_left_children(tok['id'])

   def left_labels(self, tok):
      return ":".join(self.deps._left_labels[tok['id']])
      return ":".join(sorted(set(self.deps._left_labels[tok['id']])))

   def right_labels(self, tok):
      return ":".join(self.deps._right_labels[tok['id']])
      return ":".join(sorted(set(self.deps._right_labels[tok['id']])))

   def left2_child(self, tok):
      i = self.deps.left2_child(tok['id'])
      return self.sent[i] if i is not None else None

   def right2_child(self, tok):
      i = self.deps.right2_child(tok['id'])
      return self.sent[i] if i is not None else None

#}}}



