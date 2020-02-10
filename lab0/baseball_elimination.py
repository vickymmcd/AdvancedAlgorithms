# translated to python from https://github.com/ananya77041/baseball-elimination/blob/master/src/BaseballElimination.java
import sys
import math
import picos as pic
import networkx as nx
import itertools
import cvxopt
import random

class Division:
    def __init__(self, filename):
        self.numTeams = 0
        self.teams = {}
        # self.teamNumbers = {}
        # self.against = [[]]
        self.subset = []
        self.checked = False
        self.G = nx.DiGraph()

        self.readDivision(filename)       

    def readDivision(self, filename):
        f = open(filename, "r")
        lines = [line.split() for line in f.readlines()]
        f.close()

        self.numTeams = lines[0]

        lines = lines[1:]
        for ID, teaminfo in enumerate(lines):
            team = Team(int(ID), teaminfo[0], int(teaminfo[1]), int(teaminfo[2]), int(teaminfo[3]), list(map(int, teaminfo[4:])))
            self.teams[ID] = team     

    def numberOfTeams(self):
        return self.numTeams

    def get_team_IDs(self):
        return self.teams.keys()

    def is_eliminated(self, team):
        self.checkTeam(team)

        flag = False

        temp = dict(self.teams)
        del temp[team.get_ID()]

        for _, other_team in temp.items():
            if team.get_wins() + team.get_remaining() < other_team.get_wins():
                self.subset.append(other_team)
                self.checked = True
                flag = True # remove, just to test out this function

        # flag = flow_check(team)
        # checked = True
        return flag

    def flow_check(self, teamID):
        saturated_edges = self.create_network(teamID)
        flow_value, flow_dict = nx.maximum_flow(self.G, 'source', 'sink')
        print(flow_value)
        # TODO: reformat answer
        # for match in flow_dict['source']:
        #     print(flow_dict['source'][match] == saturated_edges[match])

    def create_network(self, teamID):
        # self.checkTeam(team)

        # helper dictionaries to hold capacities
        # delete the team we are comparing against
        temp = dict(self.teams)
        del temp[teamID]
        # construct all the match capacities
        matches = {}
        for team1, team2 in itertools.combinations(temp.keys(), 2):
            matches[f'{team1}-{team2}'] = temp[team1].get_against(team2)
        # construct all the team max capacities
        teammaxes = {}
        mainteam_max = self.teams[teamID].get_wins() + self.teams[teamID].get_remaining()
        for team in temp.keys():
            teammaxes[f'{team}'] = mainteam_max - self.teams[team].get_remaining()

        # construct the actual graph
        # source to match edges
        edges = []
        saturated_edges = {}
        for match in matches:
            edges.append(('source', match, {'capacity': matches[match]}))
            saturated_edges[match] = matches[match]
        # match to team max edges
        for match, team in itertools.product(matches.keys(), teammaxes.keys()):
            edges.append((match, team, {'capacity': sys.maxsize}))
        # team max to sink edges
        for team in teammaxes:
            edges.append((team, 'sink', {'capacity': teammaxes[team]}))
        # add edges to graph
        for edge in edges:
            self.G.add_edge(edge[0], edge[1], capacity=edge[2]['capacity'])

        return saturated_edges

    def create_lp(self, teamID):
        self.create_network(teamID)

        maxflow=pic.Problem()

        # creating helper dictionaries for flows and capacities for picos
        c = {}
        f = {}
        for edge in self.G.edges(data=True):
            c[(edge[0], edge[1])] = edge[2]['capacity']
            f[(edge[0], edge[1])] = maxflow.add_variable('f[{0}]'.format((edge[0], edge[1])),1)

        # adding PICOs expression
        cc = pic.new_param('c', c)

        # adding variables, contraints, and objective
        F = maxflow.add_variable('F', 1)
        maxflow.add_constraint(pic.flow_Constraint(
            self.G, f, source='source', sink='sink', capacity='capacity', flow_value=F, graphName='G'))
        maxflow.set_objective('max', F)

        # solve the problem
        maxflow.solve(verbose=0, solver='cvxopt')

        # list of edges that carry flow
        flow_edges=[e for e in self.G.edges() if f[e].value > 1e-4]

        # print(F)
        # print(flow_edges)

        for edge in self.G.edges(data=True):
            print(f'edge: {edge}, \t\t\t value: {f[(edge[0], edge[1])].value}')
        

    def certificateOfElimination(self, team):
        self.checkTeam(team)

        return self.subset if is_eliminated(team) else None

    def checkTeam(self, team):
        if team.get_ID() not in self.get_team_IDs():
            raise ValueError("Team does not exist in given input.")

    def __str__(self):
        temp = ''
        for key in self.teams:
            temp = temp + f'{key}: {str(self.teams[key])} \n'
        return temp

class Team:
    def __init__(self, ID, teamname, wins, losses, remaining, against):
        self.ID = ID
        self.name = teamname
        self.wins = wins
        self.losses = losses
        self.remaining = remaining
        self.against = against

    def get_ID(self):
        return self.ID

    def get_wins(self):
        return self.wins

    def get_losses(self):
        return self.losses

    def get_remaining(self):
        return self.remaining

    def get_against(self, other_team=None):

        if other_team is not None:
            try:
                num_games = self.against[other_team]
            except:
                raise ValueError("Team does not exist in given input.")

            return num_games
        else:
            return self.against

    def __str__(self):
        return f'{self.name} \t {self.wins} wins \t {self.losses} losses \t {self.remaining} remaining'

def example():
    # Use a fixed RNG seed so the result is reproducable.
    random.seed(1)

    # Number of nodes.
    N=4

    # Generate a graph using LCF notation.
    G=nx.LCF_graph(N,[1,3,14],5)
    G=nx.DiGraph(G) #edges are bidirected

    # Generate edge capacities.
    c={}
    for e in sorted(G.edges(data=True)):
        capacity = random.randint(1, 20)
        e[2]['capacity'] = capacity
        c[(e[0], e[1])]  = capacity
        # print(e)      (0, 3, {'capacity': 3})
        # print(c)      {(0, 1): 5, (0, 2): 19, (0, 3): 3}

    # Convert the capacities to a PICOS expression.
    cc=pic.new_param('c',c)

    # Set source and sink nodes for flow computation.
    s=0
    t=3

    maxflow2=pic.Problem()

    # Add the flow variables.
    f={}
    for e in G.edges():
        f[e]=maxflow2.add_variable('f[{0}]'.format(e),1)

    # Add another variable for the total flow.
    F=maxflow2.add_variable('F',1)

    # Enforce all flow constraints at once.
    maxflow2.add_constraint(pic.flow_Constraint(
        G, f, source=0, sink=3, capacity='capacity', flow_value=F, graphName='G'))

    # Set the objective.
    maxflow2.set_objective('max',F)

    # Solve the problem.
    maxflow2.solve(verbose=0,solver='cvxopt')

    # Determine which edges carry flow.
    flow_edges=[e for e in G.edges() if f[e].value > 1e-4]

    # print(F)            # 26.999999866136633
    # print(flow_edges)   # [(0, 1), (0, 3), (0, 2), (1, 2), (1, 3), (2, 1), (2, 3), (3, 2), (3, 1)]
    # print(G.edges())      # [(0, 1), (0, 3), (0, 2), (1, 0), (1, 2), (1, 3), (2, 1), (2, 3), (2, 0), (3, 2), (3, 0), (3, 1)]
    # print(G.edges(data=True))     # [(0, 1, {'capacity': 5}), (0, 3, {'capacity': 3}),

if __name__ == '__main__':
    filename = sys.argv[1]
    # print(filename)
    division = Division(filename)
    # for (ID, team) in division.teams.items():
    #     print(team.name + ": Eliminated? " + str(division.is_eliminated(team)))
    # print(str(division))
    # division.flow_check(3)
    # division.create_network(1)
    # division.create_network(2)
    # division.create_network(3)


    # example()
    division.create_lp(3)



