# translated to python from https://github.com/ananya77041/baseball-elimination/blob/master/src/BaseballElimination.java
import sys
import math
import picos as pic
import networkx as nx
import itertools
import swiglpk
import cvxopt
import re

class Division:
    def __init__(self, filename):
        self.teams = {}
        self.G = nx.DiGraph()
        self.readDivision(filename)    

    def readDivision(self, filename):
        f = open(filename, "r")
        lines = [line.split() for line in f.readlines()]
        f.close()

        lines = lines[1:]
        for ID, teaminfo in enumerate(lines):
            team = Team(int(ID), teaminfo[0], int(teaminfo[1]), int(teaminfo[2]), int(teaminfo[3]), list(map(int, teaminfo[4:])))
            self.teams[ID] = team     

    def get_team_IDs(self):
        return self.teams.keys()

    def is_eliminated(self, teamID):
        flag1 = False

        temp = dict(self.teams)
        del temp[teamID]

        for _, other_team in temp.items():
            if team.get_wins() + team.get_remaining() < other_team.get_wins():
                flag1 = True

        # flag2 = self.network_flows(teamID)
        flag2 = self.linear_programming(teamID)
        return flag1 or flag2

    def network_flows(self, teamID):
        saturated_edges = self.create_network(teamID)
        flow_value, flow_dict = nx.maximum_flow(self.G, 'source', 'sink')

        flag = False
        for match in flow_dict['source']:
            if flow_dict['source'][match] != saturated_edges[match]:
                flag = True

        return flag

    def create_network(self, teamID):
        self.G.clear()

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

    def linear_programming(self, teamID):
        saturated_edges = self.create_network(teamID)

        maxflow=pic.Problem()

        # creating helper dictionaries for flows and capacities for picos
        c = {}
        f = {}
        source_edges = []
        for edge in self.G.edges():
            f[edge] = maxflow.add_variable('f[{0}]'.format(edge),1)
            if edge[0] is 'source':
                source_edges.append(edge)

        # adding variables, contraints, and objective
        F = maxflow.add_variable('F', 1)
        maxflow.add_constraint(pic.flow_Constraint(
            self.G, f, source='source', sink='sink', capacity='capacity', flow_value=F, graphName='G'))
        maxflow.set_objective('max', F)

        # solve the problem
        maxflow.solve(verbose=0, solver='glpk')

        # list of edges that carry flow
        flow_edges=[e for e in self.G.edges() if f[e].value > 1e-4]

        flag = False

        for flow in source_edges:
            if saturated_edges[flow[1]] != f[flow].value:
                flag = True

        return flag
        

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
        try:
            num_games = self.against[other_team]
        except:
            raise ValueError("Team does not exist in given input.")

        return num_games

    def __str__(self):
        return f'{self.name} \t {self.wins} wins \t {self.losses} losses \t {self.remaining} remaining'

if __name__ == '__main__':
    filename = sys.argv[1]
    division = Division(filename)
    for (ID, team) in division.teams.items():
        print(team.name + ": Eliminated? " + str(division.is_eliminated(team.get_ID())))



