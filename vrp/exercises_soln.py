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
    print(C)
    print(Cnew)
    print(q)
    print (qnew)

    prob = pic.Problem()
    # Add variables
    x = prob.add_variable('x',(n,n),vtype="binary")
    print(x)
    u = prob.add_variable('u',n,vtype="continuous",upper=Q,lower=q)

    # Add flow conservation constraints
    prob.add_constraint(sum([x[0,j] for j in range(n)]) <= K)
    prob.add_constraint(sum([x[i,0] for i in range(n)]) == 0)
    prob.add_constraint(sum([x[i,i] for i in range(n)]) == 0)
    prob.add_constraint(sum([x[0,j] for j in range(n)]) == sum([x[i,n-1] for i in range(n)]))
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
    solution = prob.solve(solver="cplex",verbose=True,gaplim=1e-2)
    print("solution is: " + str(solution))
    if ("optimal" not in solution['status']):
        return None

    for i in range(n):
       for j in range(n):
           if x[i,j].value == 1.0:
               print ("Edge "+str(i)+","+str(j))

    return prob.obj_value(), x

# Local search
def local_search(C,q,K,Q):
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

    print(cvrp_ip(C,q,K,Q))
    #print(local_search(C,q,K,Q))
