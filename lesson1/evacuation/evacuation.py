# python3

class Edge:

    def __init__(self, u, v, capacity):
        self.u = u
        self.v = v
        self.capacity = capacity
        self.flow = 0

    def __str__(self):
        return "Edge from: " + str(self.u) + " to " + str(self.v) + " with capacity " + str(self.capacity)

# This class implements a bit unusual scheme for storing edges of the graph,
# in order to retrieve the backward edge for a given edge quickly.
class FlowGraph:

    def __init__(self, n):
        # List of all - forward and backward - edges
        self.edges = []
        # These adjacency lists store only indices of edges in the edges list
        self.graph = [[] for _ in range(n)]

    def add_edge(self, from_, to, capacity):
        # Note that we first append a forward edge and then a backward edge,
        # so all forward edges are stored at even indices (starting from 0),
        # whereas backward edges are stored at odd indices.
        forward_edge = Edge(from_, to, capacity)
        backward_edge = Edge(to, from_, 0)
        self.graph[from_].append(len(self.edges))
        self.edges.append(forward_edge)
        self.graph[to].append(len(self.edges))
        self.edges.append(backward_edge)

    def size(self):
        return len(self.graph)

    def get_ids(self, from_):
        return self.graph[from_]

    def get_edge(self, id):
        return self.edges[id]

    def add_flow(self, id, flow):
        # To get a backward edge for a true forward edge (i.e id is even), we should get id + 1
        # due to the described above scheme. On the other hand, when we have to get a "backward"
        # edge for a backward edge (i.e. get a forward edge for backward - id is odd), id - 1
        # should be taken.
        #
        # It turns out that id ^ 1 works for both cases. Think this through!
        self.edges[id].flow += flow
        self.edges[id ^ 1].flow -= flow

    def find_path(self, start, end, parent):
        # find a shortest path from start to end (if one exists) using BFS

        # mark all vertices as not visited
        visited = [False]*(len(self.graph))

        # set up a queue
        queue = [0]
        visited[0] = True

         # Standard BFS Loop
        while queue:

            #Dequeue a vertex from queue and print it
            u = queue.pop(0)

            # Get all adjacent vertices of the dequeued vertex u
            # If a adjacent has not been visited, then mark it
            # visited and enqueue it
            for idx in self.graph[u]:
                v = self.edges[idx].u if self.edges[idx].u != u else self.edges[idx].v
                if visited[v] == False and self.edges[idx].capacity > 0:
                    queue.append(v)
                    visited[v] = True
                    parent[v] = u

        # check if you reached the sink
        return visited[len(self.graph)-1]

def read_data():
    vertex_count, edge_count = map(int, input().split())
    graph = FlowGraph(vertex_count)
    for _ in range(edge_count):
        u, v, capacity = map(int, input().split())
        graph.add_edge(u - 1, v - 1, capacity)
    return graph


def max_flow(graph, from_, to):
    flow = 0
    # your code goes here
    parent = [-1]*len(graph.graph)

    while graph.find_path(from_, to, parent):
        s = to

        path_flow = float("Inf")
        while s != from_:
            for edge in graph.graph[parent[s]]:
                if graph.edges[edge].u == parent[s] and graph.edges[edge].v == s:
                    curr_edge = graph.edges[edge]
            s = parent[s]
            path_flow = min(path_flow, curr_edge.capacity)

        flow += path_flow

        # update residual capacities of the edges and reverse edges
        # along the path
        v = to
        while(v !=  from_):
            for edge in graph.edges:
                if edge.u == parent[v] and edge.v == v:
                    edge.capacity -= path_flow
                if edge.u == v and edge.v == parent[v]:
                    edge.capacity += path_flow
            v = parent[v]

    return flow


if __name__ == '__main__':
    graph = read_data()
    parent = [-1]*len(graph.graph)
    print(max_flow(graph, 0, graph.size() - 1))
