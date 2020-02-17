'''Code file for baseball elimination lab created for Advanced Algorithms
Spring 2020 at Olin College. The code for this lab has been adapted from:
https://github.com/ananya77041/baseball-elimination/blob/master/src/BaseballElimination.java'''

import sys
import math
import picos as pic
import networkx as nx
import itertools
import swiglpk
import cvxopt
import re


class Division:
    '''
    The Division class represents a baseball division. This includes all the
    teams that are a part of that division, their winning and losing history,
    and their remaining games for the season.

    filename: name of a file with an input matrix that has info on teams &
    their games
    '''

    def __init__(self, filename):
        self.teams = {}
        self.G = nx.DiGraph()
        self.readDivision(filename)

    def readDivision(self, filename):
        '''Reads the information from the given file and builds up a dictionary
        of the teams that are a part of this division.
        '''
        f = open(filename, "r")
        lines = [line.split() for line in f.readlines()]
        f.close()

        lines = lines[1:]
        for ID, teaminfo in enumerate(lines):
            team = Team(int(ID), teaminfo[0], int(teaminfo[1]), int(teaminfo[2]), int(teaminfo[3]), list(map(int, teaminfo[4:])))
            self.teams[ID] = team

    def get_team_IDs(self):
        '''Gets the list of IDs that are associated with each of the teams
        in this division.
        '''
        return self.teams.keys()

    def is_eliminated(self, teamID, solver):
        '''Uses the given solver (either Linear Programming or Network Flows)
        to determine if the team with the given ID is mathematically
        eliminated from winning the division (aka winning more games than any
        other team) this season.
        '''
        flag1 = False
        team = self.teams[teamID]

        temp = dict(self.teams)
        del temp[teamID]

        for _, other_team in temp.items():
            if team.wins + team.remaining < other_team.wins:
                flag1 = True

        saturated_edges = self.create_network(teamID)
        if not flag1:
            if solver == "Network Flows":
                flag1 = self.network_flows(saturated_edges)
            elif solver == "Linear Programming":
                flag1 = self.linear_programming(teamID, saturated_edges)

        return flag1

    def network_flows(self, saturated_edges):
        '''Uses network flows to determine if the team with given team ID
        has been eliminated. You can feel free to use the built in networkx
        maximum flow function or the maximum flow function you implemented as
        part of the in class implementation activity.
        '''
        return False

    def create_network(self, teamID):
        '''Builds up the network needed for solving the baseball elimination
        problem as a network flows problem & stores it in self.G. Returns a
        dictionary of saturated edges that maps team pairs to the amount of
        additional games they have against each other.
        '''
        self.G.clear()

        # helper dictionaries to hold capacities
        matches = {}
        teammaxes = {}
        saturated_edges = {}
        # delete the team we are comparing against
        temp = dict(self.teams)
        del temp[teamID]
        # construct all the match capacities
        for team1, team2 in itertools.combinations(temp.keys(), 2):
            key = f'{team1}-{team2}'
            matches[key] = temp[team1].get_against(team2)
            saturated_edges[key] = matches[key]
        # construct all the team max capacities
        mainteam_max = self.teams[teamID].wins + self.teams[teamID].remaining
        for team in temp.keys():
            teammaxes[f'{team}'] = mainteam_max - self.teams[team].wins

        # construct the actual graph
        # source to match edges
        for match in matches:
            self.G.add_edge('source', match, capacity=matches[match])
        # match to team max edges
        for match, team in itertools.product(matches.keys(), teammaxes.keys()):
            if team in match:
                self.G.add_edge(match, team, capacity=sys.maxsize)
        # team max to sink edges
        for team in teammaxes:
            self.G.add_edge(team, 'sink', capacity=teammaxes[team])

        return saturated_edges

    def linear_programming(self, teamID, saturated_edges):
        '''Uses linear programming to determine if the team with given team ID
        has been eliminated. We recommend using a picos solver to solve the
        linear programming problem once you have it set up.
        '''

        maxflow=pic.Problem()

        # creating helper dictionaries for flows and capacities for picos
        c = {}
        f = {}
        source_edges = []
        for edge in self.G.edges():

            if self.G[edge[0]][edge[1]]['capacity'] < sys.maxsize:
                f[edge] = maxflow.add_variable(
                'f[{0}]'.format(edge),1,lower=0,upper =self.G[edge[0]][edge[1]]['capacity'])
            else:
                f[edge] = maxflow.add_variable(
                'f[{0}]'.format(edge),1,lower=0)
            if edge[0] is 'source':
                source_edges.append(edge)

        # adding variables, contraints, and objective
        F = maxflow.add_variable('F', 1)
        for i in self.G.nodes():
            if i == 'source':
                maxflow.add_constraint(pic.sum([f[p,i] for p in self.G.predecessors(i)]) +
                               F == pic.sum([f[i,p] for p in self.G.successors(i)]))
            elif i != 'sink':
                maxflow.add_constraint(pic.sum([f[p,i] for p in self.G.predecessors(i)])
                                       == pic.sum([f[i,p] for p in self.G.successors(i)]))
        maxflow.set_objective('max', F)

        # solve the problem
        maxflow.solve(verbose=0, solver='cvxopt')

        flag = False
        for flow in source_edges:
            if abs(self.G[flow[0]][flow[1]]['capacity'] - f[flow].value) > 1e-5:
                flag = True

        return flag


    def checkTeam(self, team):
        '''Checks that the team actually exists in this division.
        '''
        if team.ID not in self.get_team_IDs():
            raise ValueError("Team does not exist in given input.")

    def __str__(self):
        '''Returns pretty string representation of a division object.
        '''
        temp = ''
        for key in self.teams:
            temp = temp + f'{key}: {str(self.teams[key])} \n'
        return temp

class Team:
    '''
    The Team class represents one team within a baseball division for use in
    solving the baseball elimination problem. This class includes information
    on how many games the team has won and lost so far this season as well as
    information on what games they have left for the season.

    ID: ID to keep track of the given team
    teamname: human readable name associated with the team
    wins: number of games they have won so far
    losses: number of games they have lost so far
    remaining: number of games they have left this season
    against: dictionary that can tell us how many games they have left against
    each of the other teams
    '''

    def __init__(self, ID, teamname, wins, losses, remaining, against):
        self.ID = ID
        self.name = teamname
        self.wins = wins
        self.losses = losses
        self.remaining = remaining
        self.against = against

    def get_against(self, other_team=None):
        '''Returns number of games this team has against this other team.
        Raises an error if these teams don't play each other.
        '''
        try:
            num_games = self.against[other_team]
        except:
            raise ValueError("Team does not exist in given input.")

        return num_games

    def __str__(self):
        '''Returns pretty string representation of a team object.
        '''
        return f'{self.name} \t {self.wins} wins \t {self.losses} losses \t {self.remaining} remaining'

if __name__ == '__main__':
    filename = sys.argv[1]
    division = Division(filename)
    for (ID, team) in division.teams.items():
        print(f'{team.name}: Eliminated? {division.is_eliminated(team.ID, "Linear Programming")}')
