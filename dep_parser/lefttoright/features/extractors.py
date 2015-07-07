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
Feature extractors for arc-eager and arc-hybrid transition based parsers.
"""
from common import *
import os

### Features #{{{
__EXTRACTORS__ = {}

class EagerZhangNivre2011Extractor: #{{{
   """
   arc-eager features from Yue Zhang and Joakim Nivre, acl 2011.
   http://www.sutd.edu.sg/cmsresource/faculty/yuezhang/acl11j.pdf
   table 2
   """
   def __init__(self):
      pass

   def extract(self, stack, deps, sent, i):
      features=[]
      f = features.append
      import math

      # Core Elements
      s0 = sent[stack[-1]] if stack else PAD
      if s0 is not PAD:
         h = deps.parent(s0)
         s0h = h if h else PAD
         if s0h is not PAD:
            h2 = deps.parent(s0h)
            s0h2 = h2 if h2 else PAD
         else:
            s0h2 = PAD
         l = deps.left_child(s0)
         s0l = l if l else PAD
         r = deps.right_child(s0)
         s0r = r if r else PAD
         l = deps.left2_child(s0)
         s0l2 = l if l else PAD
         r = deps.right2_child(s0)
         s0r2 = r if r else PAD
      else:
         s0h = PAD
         s0h2 = PAD
         s0l = PAD
         s0r = PAD
         s0l2 = PAD
         s0r2 = PAD
      n0 = sent[i] if i < len(sent) else PAD
      if n0 is not PAD:
         l = deps.left_child(n0)
         n0l = l if l else PAD
         #r = deps.right_child(n0)
         #n0r = r if r else PAD
         l = deps.left2_child(n0)
         n0l2 = l if l else PAD
         #r = deps.right2_child(n0)
         #n0r2 = r if r else PAD
      else:
         n0l = PAD
         n0l2 = PAD
         #n0r = PAD
         #n0r2 = PAD

      if n0 != PAD and s0 != PAD:
         d = str(n0['id'] - s0['id'])
         if len(d) == 2: d = "10+" #TODO: cutoff needed?
      else: d = "NA"

      s0vr = deps.num_right_children(s0)
      s0vl = deps.num_left_children(s0)
      n0vl = deps.num_left_children(n0)

      n1 = sent[i+1] if i+1 < len(sent) else PAD
      n2 = sent[i+2] if i+2 < len(sent) else PAD

      s0w = s0['form']
      n0w = n0['form']
      n1w = n1['form']
      n2w = n2['form']
      s0hw = s0h['form']
      s0lw = s0l['form']
      s0rw = s0r['form']
      n0lw = n0l['form']
      s0h2w = s0h2['form']
      s0l2w = s0l2['form']
      s0r2w = s0r2['form']
      n0l2w = n0l2['form']

      s0p = s0['tag']
      n0p = n0['tag']
      n1p = n1['tag']
      n2p = n2['tag']
      s0hp = s0h['tag']
      s0lp = s0l['tag']
      s0rp = s0r['tag']
      n0lp = n0l['tag']
      s0h2p = s0h2['tag']
      s0l2p = s0l2['tag']
      s0r2p = s0r2['tag']
      n0l2p = n0l2['tag']

      #assert(s0l == PAD or s0l2 == PAD or s0l['id'] < s0l2['id'])
      #assert(n0lc == PAD or n0lc2 == PAD or n0lc['id'] < n0lc2['id'])
      #assert(s0rc2 == PAD or s0rc == PAD or s0rc['id'] > s0rc2['id'])
      #assert(s0rc == PAD or s0rc['id'] > s0['id'])

      s0L = deps.label_for(s0)
      s0lL = deps.label_for(s0l)
      s0rL = deps.label_for(s0r)
      n0lL = deps.label_for(n0l)
      s0hL = deps.label_for(s0h)
      s0l2L = deps.label_for(s0l2)
      s0r2L = deps.label_for(s0r2)
      n0l2L = deps.label_for(n0l2)

      s0wp = "%s:%s" % (s0w, s0p)
      n0wp = "%s:%s" % (n0w, n0p)
      n1wp = "%s:%s" % (n1w, n0p)
      n2wp = "%s:%s" % (n2w, n0p)

      s0sr = deps.right_labels(s0)
      s0sl = deps.left_labels(s0)
      n0sl = deps.left_labels(n0)

      # Single Words
      f("s0wp_%s" % (s0wp))
      f("s0w_%s"  % (s0w))
      f("s0p_%s"  % (s0p))
      f("n0wp_%s" % (n0wp))
      f("n0w_%s"  % (n0w))
      f("n0p_%s"  % (n0p))
      f("n1wp_%s" % (n1wp))
      f("n1w_%s"  % (n1w))
      f("n1p_%s"  % (n1p))
      f("n2wp_%s" % (n2wp))
      f("n2w_%s"  % (n2w))
      f("n2p_%s"  % (n2p))

      # Pairs
      f("s0wp,n0wp_%s_%s" % (s0wp, n0wp))
      f("s0wp,n0w_%s_%s" % (s0wp, n0w))
      f("s0w,n0wp_%s_%s" % (s0w, n0wp))
      f("s0wp,n0p_%s_%s" % (s0wp, n0p))
      f("s0p,n0wp_%s_%s" % (s0p, n0wp))
      f("s0w,n0w_%s_%s" % (s0w, n0w)) #?
      f("s0p,n0p_%s_%s" % (s0p, n0p))
      f("n0p,n1p_%s_%s" % (n0p, n1p))

      # Tuples
      f("n0p,n1p,n2p_%s_%s_%s" % (n0p, n1p, n2p))
      f("s0p,n0p,n1p_%s_%s_%s" % (s0p, n0p, n1p))
      f("s0hp,s0p,n0p_%s_%s_%s" % (s0hp, s0p, n0p))
      f("s0p,s0lp,n0p_%s_%s_%s" % (s0p, s0lp, n0p))
      f("s0p,s0rp,n0p_%s_%s_%s" % (s0p, s0rp, n0p))
      f("s0p,n0p,n0lp_%s_%s_%s" % (s0p, n0p, n0lp))

      # Distance
      f("s0wd_%s:%s" % (s0w, d))
      f("s0pd_%s:%s" % (s0p, d))
      f("n0wd_%s:%s" % (n0w, d))
      f("n0pd_%s:%s" % (n0p, d))
      f("s0w,n0w,d_%s:%s:%s" % (s0w, n0w, d))
      f("s0p,n0p,d_%s:%s:%s" % (s0p, n0p, d))

      # Valence
      f("s0wvr_%s:%s" % (s0w, s0vr))
      f("s0pvr_%s:%s" % (s0p, s0vr))
      f("s0wvl_%s:%s" % (s0w, s0vl))
      f("s0pvl_%s:%s" % (s0p, s0vl))
      f("n0wvl_%s:%s" % (n0w, n0vl))
      f("n0pvl_%s:%s" % (n0p, n0vl))

      # Unigrams
      f("s0hw_%s" % (s0hw))
      f("s0hp_%s" % (s0hp))
      f("s0L_%s" % (s0L))

      f("s0lw_%s" % (s0lw))
      f("s0lp_%s" % (s0lp))
      f("s0lL_%s" % (s0lL))

      f("s0rw_%s" % (s0rw))
      f("s0rp_%s" % (s0rp))
      f("s0rL_%s" % (s0rL))

      f("n0lw_%s" % (n0lw))
      f("n0lp_%s" % (n0lp))
      f("n0lL_%s" % (n0lL))

      # Third-order
      #do we really need the non-grandparent ones?
      f("s0h2w_%s" % (s0h2w))
      f("s0h2p_%s" % (s0h2p))
      f("s0hL_%s"  % (s0hL))
      f("s0l2w_%s" % (s0l2w))
      f("s0l2p_%s" % (s0l2p))
      f("s0l2L_%s" % (s0l2L))
      f("s0r2w_%s" % (s0r2w))
      f("s0r2p_%s" % (s0r2p))
      f("s0r2L_%s" % (s0r2L))
      f("n0l2w_%s" % (n0l2w))
      f("n0l2p_%s" % (n0l2p))
      f("n0l2L_%s" % (n0l2L))
      f("s0p,s0lp,s0l2p_%s_%s_%s" % (s0p, s0lp, s0l2p))
      f("s0p,s0rp,s0r2p_%s_%s_%s" % (s0p, s0rp, s0r2p))
      f("s0p,s0hp,s0h2p_%s_%s_%s" % (s0p, s0hp, s0h2p))
      f("n0p,n0lp,n0l2p_%s_%s_%s" % (n0p, n0lp, n0l2p))

      # Labels
      f("s0wsr_%s_%s" % (s0w, s0sr))
      f("s0psr_%s_%s" % (s0p, s0sr))
      f("s0wsl_%s_%s" % (s0w, s0sl))
      f("s0psl_%s_%s" % (s0p, s0sl))
      f("n0wsl_%s_%s" % (n0w, n0sl))
      f("n0psl_%s_%s" % (n0p, n0sl))

      #print features
      return features
   #}}}

class HybridFeatures: #{{{
   def __init__(self):
      
      pass

   def extract(self, stack, deps, sent, i):
      features=[]
      import math
      #features.append("toend_%s" % round(math.log(len(sent)+3-i)))
      append = features.append

      # participants
      w0=sent[i] if len(sent) > i else PAD
      w1=sent[i+1] if len(sent) > i+1 else PAD
      s0=sent[stack[-1]] if len(stack) > 0 else PAD
      s1=sent[stack[-2]] if len(stack) > 1 else PAD
      s2=sent[stack[-3]] if len(stack) > 2 else PAD

      Tlcs1=deps.left_child(s1)
      if Tlcs1: Tlcs1=Tlcs1['tag']

      Tlcs0=deps.left_child(s0)
      if Tlcs0: Tlcs0=Tlcs0['tag']

      Tlcw0=deps.left_child(w0)
      if Tlcw0: Tlcw0=Tlcw0['tag']

      Trcs0=deps.right_child(s0)
      if Trcs0: Trcs0=Trcs0['tag']

      Trcs1=deps.right_child(s1)
      if Trcs1: Trcs1=Trcs1['tag']

      Tw0=w0['tag']
      w0=w0['form']

      Tw1=w1['tag']
      w1=w1['form']

      Ts0=s0['tag']
      s0=s0['form']

      Ts1=s1['tag']
      s1=s1['form']

      Ts2=s2['tag']
      s2=s2['form']

      # (1)
      append("s0_%s" % s0)
      append("Ts0_%s" % Ts0)
      append("Ts0s0_%s_%s" % (Ts0, s0))

      append("s1_%s" % s1)
      append("Ts1_%s" % Ts1)
      append("Ts1s1_%s_%s" % (Ts1, s1))

      append("w0_%s" % w0)
      append("Tw0_%s" % Tw0)
      append("Tw0w0_%s_%s" % (Tw0, w0))
      # +hybrid
      append("w1_%s" % w1)
      append("Tw1_%s" % Tw1)
      append("Tw1w1_%s_%s" % (Tw1, w1))

      # (2)
      append("s0s1_%s_%s" % (s0,s1))
      append("Ts0Ts1_%s_%s" % (Ts0,Ts1))
      append("Ts0Tw0_%s_%s" % (Ts0,Tw0))
      append("s0Ts0Ts1_%s_%s_%s" % (s0,Ts0,Ts1))
      append("Ts0s1Ts1_%s_%s_%s" % (Ts0,s1,Ts1))
      append("s0s1Ts1_%s_%s_%s" % (s0,s1,Ts1))
      append("s0Ts0s1_%s_%s_%s" % (s0,Ts0,s1))
      append("s0Ts0Ts1_%s_%s_%s" % (s0,Ts0,Ts1))
      # +hybrid   
      append("s0w0_%s_%s" % (s0,w0))
      append("Ts0Tw0_%s_%s" % (Ts0,Tw0))
      append("Ts0Tw1_%s_%s" % (Ts0,Tw1))
      append("s0Ts0Tw0_%s_%s_%s" % (s0,Ts0,Tw0))
      append("Ts0w0Tw0_%s_%s_%s" % (Ts0,w0,Tw0))
      append("s0w0Tw0_%s_%s_%s" % (s0,w0,Tw0))
      append("s0Ts0w0_%s_%s_%s" % (s0,Ts0,w0))
      append("w0Tw0Tw1_%s_%s_%s" % (w0,Tw0,Tw1)) #

      # (3)
      append("Ts0Tw0Tw1_%s_%s_%s" % (Ts0,Tw0,Tw1))
      append("Ts1Ts0Tw0_%s_%s_%s" % (Ts1,Ts0,Tw0))
      append("s0Tw0Tw1_%s_%s_%s" % (s0,Tw0,Tw1))
      append("Ts1s0Tw0_%s_%s_%s" % (Ts1,s0,Tw0))

      # (4) rc -1  lc 1
      append("Ts1Trcs1Tw0_%s_%s_%s" % (Ts1, Trcs1, Tw0))
      append("Ts1Trcs1Tw0_%s_%s_%s" % (Ts1, Trcs1, Ts0))
      append("Ts1Tlcs1Ts0_%s_%s_%s" % (Ts1, Tlcs1, Ts0))
      append("Ts1Ts0Tlcs0_%s_%s_%s" % (Ts1, Ts0, Tlcs0))
      append("Ts1Trcs0Ts0_%s_%s_%s" % (Ts1, Trcs0, Ts0))
      append("Ts0Tlcs1s0_%s_%s_%s" % (Ts0, Tlcs1, s0))
      append("Ts1s0Trcs0_%s_%s_%s" % (Ts1, s0, Trcs0))
      append("Ts0Tlcs1s0_%s_%s_%s" % (Ts0, Trcs1, s0))
      append("Ts1s0Trcs0_%s_%s_%s" % (Ts1, s0, Tlcs0))

      # +hybrid
      append("Ts0Trcs0Tw0_%s_%s_%s" % (Ts0,Trcs0,Tw0))
      append("Ts0Trcs0Tw0_%s_%s_%s" % (Ts0,Trcs0,Tw1))
      append("Ts0Tlcs0Tw0_%s_%s_%s" % (Ts0,Tlcs0,Tw0))
      append("Ts0Tw0Tlcw0_%s_%s_%s" % (Ts0,Tw0,Tlcw0))
      append("Ts0Tlcs0w0_%s_%s_%s" % (Ts0,Tlcs0,w0))
      append("Ts0Tlcs0w0_%s_%s_%s" % (Ts0,Trcs0,w0))
      append("Ts0w0Tlcw0_%s_%s_%s" % (Ts0,w0,Tlcw0))

      append("Ts0Tw0Trcs0Tlcw0_%s_%s_%s_%s" % (Ts0,Tw0,Tlcw0,Trcs0))
      append("Ts0Ts1Trcs1Tlcs0_%s_%s_%s_%s" % (Ts0,Ts1,Tlcs0,Trcs1))

      # (5)
      append("Ts2Ts1Ts0_%s_%s_%s" % (Ts2,Ts1,Ts0))
      append("Ts1Ts0Tw0_%s_%s_%s" % (Ts1,Ts0,Tw0))
      append("Ts0Tw0Tw1_%s_%s_%s" % (Ts0,Tw0,Tw1))

      return features
   #}}}

#}}}

__EXTRACTORS__['eager.zn'] = EagerZhangNivre2011Extractor()
__EXTRACTORS__['hybrid.1']   = HybridFeatures()

def get(name):
   try:
      return __EXTRACTORS__[name]
   except KeyError:
      import sys
      sys.stderr.write("invalid feature extactor %s. possible values: %s\n" % (name,__EXTRACTORS__.keys()))
      sys.exit()

