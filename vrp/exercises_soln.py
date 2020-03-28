import math
import picos as pic
import numpy as np
import random
import xml.etree.ElementTree as ET

# Find connected component using DFS
def DFS(i,x,visited,S):
    n = len(visited)
    visited[i] = True
    S.append(i)
    for j in range(n):
        if (x[i,j].value[0] == 1.):
            if (visited[j] == False):
                if (j!=0):
                    DFS(j,x,visited,S)
                else:
                    visited[0] = True

    return S,visited[0]

# IP
def cvrp_ip(C,q,K,Q,obj=True):
    n = len(q)+1
    Cnew = np.zeros((n,n))
    for i in range(n-1):
        for j in range(i+1,n-1):
            Cnew[i,j] = C[i,j]
            Cnew[j,i] = C[j,i]
            if i == 0:
                Cnew[n-1,j] = C[i,j]
                Cnew[j,n-1] = C[j,i]
    qnew = np.append(q,[0])
    print (qnew)

    prob = pic.Problem()
    # Add variables
    x = prob.add_variable('x',(n,n),vtype="binary")
    u = prob.add_variable('u',n,vtype="continuous",upper=Q,lower=q)

    # Add flow conservation constraints
    prob.add_constraint(sum([x[0,j] for j in range(n)]) == K)
    prob.add_list_of_constraints([sum([x[i,j] for j in range(n)]) == 1 for i in range(1,n-1)])
    prob.add_list_of_constraints([sum([x[j,i] for j in range(n)]) == 1 for i in range(1,n-1)])

    # Capacity constraints
    prob.add_list_of_constraints([u[i]-u[j]+Q*x[i,j] <= Q-qnew[j] for i in range(n) for j in range(n) ])

    # Objective function
    prob.set_objective('min',pic.sum([Cnew[i,j]*x[i,j] for i in range(n) for j in range(n)]))
    if obj == False:
        prob.set_objective('min',x[0,0])

    #print prob

    # Solve
    solution = prob.solve(solver="glpk",verbose=True,gaplim=1e-2)
    print("solution is: " + str(solution))
    if (solution['status'] != 'OPTIMAL'):
        return None

    #for i in range(n):
    #    for j in range(n):
    #        if x[i,j].value[0] == 1:
    #            print "Edge "+str(i)+","+str(j)

    return prob.obj_value(), x

# Local search
def local_search(C,q,K,Q):
    n = len(q)
    _, xinit = cvrp_ip2(C,q,K,Q,False)
    max_iters = 1

    # Get connected components
    bestx = []
    visited = [False for _ in range(n)]
    starts = [i for i in range(n) if xinit[0,i].value[0] == 1]
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


# Test adding noise to loads
def add_randomness(C,q,K,Q):
    sigma = 0.2*np.std(q)
    iters = 1000
    costs = np.zeros(iters)
    for i in range(iters):
        qnew = q+np.random.normal(0,sigma,len(q))
        obj,_ = cvrp_ip2(C,qnew,K,Q)
        costs[i] = obj
    return np.mean(costs), np.std(costs)


def read_instance_A(filename):
    tree = ET.parse(filename)
    root = tree.getroot()
    nodes = root.find('network').find('nodes')
    requests = root.find('requests')

    n = len(nodes)
    C = np.zeros((n,n))
    q = np.zeros(n)
    Q = float(root.find('fleet').find('vehicle_profile').find('capacity').text)

    # Note: 1=depot, rest are labeled 2...n
    x = np.zeros(n)
    y = np.zeros(n)
    for node in nodes:
        i = int(node.get('id'))-1
        x[i] = float(node.find('cx').text)
        y[i] = float(node.find('cy').text)
    for i in range(n):
        for j in range(i+1,n):
            d = math.sqrt((x[i]-x[j])**2 + (y[i]-y[j])**2)
            C[i,j] = d
            C[j,i] = d

    for child in requests:
        i = int(child.get('node'))-1
        q[i] = float(child.find('quantity').text)

    return C,q,Q

def read_instance_C(filename):
    tree = ET.parse(filename)
    root = tree.getroot()
    nodes = root.find('network').find('nodes')
    requests = root.find('requests')

    n = len(nodes)
    C = np.zeros((n,n))
    q = np.zeros(n)
    Q = float(root.find('fleet').find('vehicle_profile').find('capacity').text)

    # Note: 1=depot, rest are labeled 2...n
    links = root.find('network').find('links')
    for link in links:
        i = int(link.get('head'))-1
        j = int(link.get('tail'))-1
        d = float(link.find('length').text)
        C[i,j] = d
        C[j,i] = d

    for child in requests:
        i = int(child.get('node'))-1
        q[i] = float(child.find('quantity').text)

    return C,q,Q

if __name__ == "__main__":
    C = np.ones((6,6))
    K = 2
    q = [0,1,1,1,1,0]
    Q = 2

    C,q,Q = read_instance_A('data2/simple.xml')
    # number of vehicles
    K = 4

    #print(add_randomness(C,q,K,Q))

    print(cvrp_ip(C,q,K,Q))
