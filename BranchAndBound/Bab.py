import picos as pic
from picos import RealVariable
from copy import deepcopy
from heapq import *
import heapq as hq
import numpy as np
import itertools
import math
counter = itertools.count() 

class BBTreeNode():
    def __init__(self, vars = [], constraints = [], objective='', prob=None):
        self.vars = vars
        self.constraints = constraints
        self.objective = objective
        self.children = []
        self.prob = prob

    def __deepcopy__(self, memo):
        '''
        Deepcopies the picos problem
        This overrides the system's deepcopy method bc it doesn't work on classes by itself
        '''
        newprob = pic.Problem.clone(self.prob)
        return BBTreeNode(self.vars, newprob.constraints, self.objective, newprob)
    
    def buildProblem(self):
        '''
        Bulids the initial Picos problem
        '''
        prob=pic.Problem()
   
        prob.add_list_of_constraints(self.constraints)    
        
        prob.set_objective('max', self.objective)
        self.prob = prob
        return self.prob

    def is_integral(self):
        '''
        Checks if all variables (excluding the one we're maxing) are integers
        '''
        for v in self.vars[:-1]:
            if v.value == None or abs(round(v.value) - float(v.value)) > 1e-4 :
                return False
        return True

    def branch_floor(self, branch_var):
        '''
        Makes a child where xi <= floor(xi)
        '''
        n1 = deepcopy(self)
        n1.prob.add_constraint( branch_var <= math.floor(branch_var.value) ) # add in the new binary constraint

        return n1

    def branch_ceil(self, branch_var):
        '''
        Makes a child where xi >= ceiling(xi)
        '''
        n2 = deepcopy(self)
        n2.prob.add_constraint( branch_var >= math.ceil(branch_var.value) ) # add in the new binary constraint
        return n2


    def bbsolve(self):
        '''
        Use the branch and bound method to solve an integer program
        This function should return:
            return bestres, bestnode_vars

        where bestres = value of the maximized objective function
              bestnode_vars = the list of variables that create bestres
        '''

        # these lines build up the initial problem and adds it to a heap
        root = self
        res = root.buildProblem().solve(solver='cvxopt')
        heap = [(res, next(counter), root)]
        bestres = -1e20 # a small arbitrary initial best objective value
        bestnode_vars = root.vars # initialize bestnode to the root

        # while there are still nodes to evaluate
        while len(heap) > 0:
            # pop the node off the heap
            _, _, fnode = hq.heappop(heap)
         
            # solve the relaxed version of the problem
            try:
                res = fnode.prob.solve(solver='cvxopt')
            except:
                #if problem is infeasible this will catch it and kill the branch
                print("Infeasible")
                pass
            
            if float(fnode.vars[-1]) < float(bestres - 1e-3): # even the relaxed problem sucks. forget about this branch then
                print("Relaxed Problem Stinks. Killing this branch.")
                pass
            elif fnode.is_integral(): #if a valid solution then this is the new best
                    print("New Best Integral solution.")
                    # have to cast everything to float so it stops being a PICOS variable bc of copying issues
                    bestres = float(fnode.vars[-1])
                    bestnode_vars = [float(v.value) for v in fnode.vars]
            else: #otherwise, we're unsure if this branch holds promise. Maybe it can't actually achieve this upper bound. So branch into it
                for v in fnode.vars:
                    # grab the first var that isn't an integer
                    if v.value != None and abs(round(v.value) - float(v.value)) > 1e-4:
                        # create the branches
                        new_left_node = fnode.branch_floor(v)
                        new_right_node = fnode.branch_ceil(v)

                        # add the branches to the heap
                        hq.heappush(heap, (float(fnode.vars[-1]), next(counter), new_left_node ) )  # using counter to avoid possible comparisons between nodes. It tie breaks
                        hq.heappush(heap, (float(fnode.vars[-1]), next(counter), new_right_node ) )
                        break
        return bestres, bestnode_vars
 