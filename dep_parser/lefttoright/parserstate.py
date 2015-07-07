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

from deps import DependenciesCollection
import copy

class ParserState: #{{{
   def __init__(self,sent):
      self.stack=[]
      self.sent=sent
      self.deps=DependenciesCollection(sent)
      self.i=0
      self.actions = []
      self._action_scores=[]
      self.cost=0

   def __repr__(self):
      return "parserstate:<s:%s i:%s a:%s>" % (self.stack,self.i,self.actions)

   def __deepcopy__(self, memo):
      c = self.__class__(self.sent) ##@@ TODO: how to create the proper Configuration in the derived class?
      c.deps = copy.deepcopy(self.deps, memo)
      c.i = self.i
      c.stack = self.stack[:]
      c.actions = self.actions[:]
      c.cost = self.cost
      return c

   def actions_map(self):
      """
      returns:
         a dictionary of ACTION -> function_name. to be provided in the derived class
         see ArcStandardConfiguration for an example
      """
      return {}

   #def score(self, action):pass #@TODO

   def is_in_finish_state(self):
      return len(self.stack)==1 and not self.sent[self.i:]

   def do_action(self, action):
      try:
         action, label = action
      except ValueError:
         label = '_'
      #self.actions.append(action)
      return self.actions_map()[action](label)

   def newAfter(self, action):
      """
      return a new configuration based on current one after aplication of ACTION
      """
      conf = copy.deepcopy(self)
      conf.do_action(action)
      return conf

#}}}

