'''Code file for vehicle routing problem created for Advanced Algorithms
Spring 2020 at Olin College. These functions solve the vehicle routing problem
using an integer programming and then a local search approach. This code has
been adapted from functions written by Alice Paul.'''

import picos as pic
import numpy as np
from read_files import read_file_type_A, read_file_type_C

# Find connected component using DFS
def DFS(i,x,visited,S):
    n = len(visited)
    visited[i] = True
    S.append(i)
    for j in range(n):
        if (x[i,j].value == 1.):
            if (visited[j] == False):
                if (j!=0):
                    DFS(j,x,visited,S)
                else:
                    visited[0] = True

    return S,visited[0]

def cvrp_ip(C,q,K,Q,obj=True):
    '''
    Solves the capacitated vehicle routing problem using an integer programming
    approach.

    C: matrix of edge costs, that represent distances between each node
    q: list of demands associated with each client node
    K: number of vehicles
    Q: capacity of each vehicle
    obj:
    returns:
        objective_value: value of the minimum travel cost
        x: matrix representing number of routes that use each arc
    '''
    # need to add in destination node (same as source)
    n = len(q)+1
    Cnew = np.zeros((n,n))
    for i in range(n-1):
        for j in range(i+1,n-1):
            Cnew[i,j] = C[i,j]
            Cnew[j,i] = C[j,i]
            # set destination node to have same distances as source
            if i == 0:
                Cnew[n-1,j] = C[i,j]
                Cnew[j,n-1] = C[j,i]
    # destination node, like origin, has 0 demand
    qnew = np.append(q,[0])

    # set up the picos problem
    prob = pic.Problem()

    # Add variables

    # x represents # of routes that use each arc
    x = prob.add_variable('x',(n,n),vtype="binary")
    # u represents cumulative quantity of goods delivered between origin and a given node
    u = prob.add_variable('u',n,vtype="continuous",upper=Q,lower=q)

    # Add flow conservation constraints
    prob.add_constraint(sum([x[0,j] for j in range(n)]) <= K) # no more than K routes for K vehicles
    prob.add_constraint(sum([x[i,0] for i in range(n)]) == 0) # routes can't end at the origin
    prob.add_constraint(sum([x[i,i] for i in range(n)]) == 0) # routes can't include edges connecting node to itself
    # number of routes that leave origin = number that enter the destination
    prob.add_constraint(sum([x[0,j] for j in range(n)]) == sum([x[i,n-1] for i in range(n)]))
    # every node must be visited - an edge goes from another node to it
    prob.add_list_of_constraints([sum([x[i,j] for j in range(n)]) == 1 for i in range(1,n-1)])
    # route must also leave that node - edge goes from it to another node
    prob.add_list_of_constraints([sum([x[j,i] for j in range(n)]) == 1 for i in range(1,n-1)])

    # Capacity constraints
    prob.add_list_of_constraints([u[i]-u[j]+Q*x[i,j] <= Q-qnew[j] for i in range(n) for j in range(n) ])

    # Objective function - minimize travel cost
    prob.set_objective('min',pic.sum([Cnew[i,j]*x[i,j] for i in range(n) for j in range(n)]))

    # ?? what is this about??
    if obj == False:
        prob.set_objective('min',x[0,0])

    # Solve
    solution = prob.solve(solver="cplex",verbose=True,gaplim=1e-2)

    if ("optimal" not in solution['status']):
        return None

    # print edges that are included in the solution
    for i in range(n):
       for j in range(n):
           if x[i,j].value == 1.0:
               print ("Edge "+str(i)+","+str(j))

    objective_value = prob.obj_value()
    return objective_value, x

# Local search
def local_search(C,q,K,Q):
    '''
    Solves the capacitated vehicle routing problem using a local search
    approach.

    C: matrix of edge costs, that represent distances between each node
    q: list of demands associated with each client node
    K: number of vehicles
    Q: capacity of each vehicle
    returns:
        bestval: value of the minimum travel cost
        bestx: matrix representing number of routes that use each arc
    '''
    n = len(q)
    _, xinit = cvrp_ip(C,q,K,Q,False)
    max_iters = 1

    # Get connected components
    bestx = []
    visited = [False for _ in range(n)]
    starts = [i for i in range(n) if xinit[0,i].value == 1]
    for i in starts:
        comp,_ = DFS(i,xinit,[False for _ in range(n)],[])
        bestx.append(0)
        bestx.extend(comp)
    bestx.append(0)

    m = len(bestx)
    bestval = 0
    for l in range(m-1):
        bestval += C[bestx[l],bestx[l+1]]

    iters = 0
    updated = True
    while (iters <= max_iters) and (updated==True):
        updated = False
        iters += 1

        for l in range(m):
            if bestx[l] == 0:
                continue
            currind = l
            currval = bestval
            # Find best location for i
            for j in range(1,m-1):
                if (j != l+1) and (j != l):
                    tempval = bestval
                    tempval -= (C[bestx[l-1],bestx[l]]+C[bestx[l],bestx[l+1]]+C[bestx[j-1],bestx[j]])
                    tempval += (C[bestx[j-1],bestx[l]]+C[bestx[l],bestx[j]]+C[bestx[l-1],bestx[l+1]])

                    if tempval < currval:
                        currval = tempval
                        currind = j
            if currval < bestval:
                updated = True
                i = bestx.pop(l)
                if currind > l:
                    bestx.insert(currind-1,i)
                else:
                    bestx.insert(currind,i)
                bestval = currval

    return bestval, bestx


if __name__ == "__main__":

    C,q,K,Q = read_file_type_A('data2/A-n016-k05.xml')
    #C,q,Q = read_instance_data3('data3/LD11_1.xml')

    #print(cvrp_ip(C,q,K,Q))
    print(local_search(C,q,K,Q))
