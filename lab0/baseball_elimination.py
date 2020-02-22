'''Code file for baseball elimination lab created for Advanced Algorithms
Spring 2020 at Olin College. The code for this lab has been adapted from:
https://github.com/ananya77041/baseball-elimination/blob/master/src/BaseballElimination.java'''

import sys
import math
import picos as pic
import networkx as nx
import itertools
import cvxopt
import matplotlib
import matplotlib.pyplot as plt


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
                flag1 = self.linear_programming(saturated_edges)

        return flag1

    def create_network(self, teamID):
        '''Builds up the network needed for solving the baseball elimination
        problem as a network flows problem & stores it in self.G. Returns a
        dictionary of saturated edges that maps team pairs to the amount of
        additional games they have against each other.
        '''
        
        self.G.clear()

        # helper dictionaries to hold capacities
        saturated_edges = {}
        mainteam_max = self.teams[teamID].wins + self.teams[teamID].remaining

        team_ids = list(self.get_team_IDs())
        # Remove main teamID from this list (they don't have a match against themselves)
        team_ids.remove(teamID) 

        # these three lists could be all_edges, they're separated for understanding
        sink_edges = []
        mid_edges = []
        source_edges = []

        teams_already_battled = []
        for i, id in enumerate(team_ids):

            max_win = mainteam_max - self.teams[id].wins
            sink_edges.append((self.teams[id].name, "sink", {'capacity': max_win, 'flow' : 0}))

            teams_already_battled.append(i)

            for j, other_team_id in enumerate(team_ids):
                if j not in teams_already_battled:
                    remaining_games = self.teams[id].get_against(other_team_id)
                    mid_edges.append((self.teams[id].name + "-" + self.teams[other_team_id].name, self.teams[id].name, {"capacity": remaining_games, 'flow':0}))
                    mid_edges.append((self.teams[id].name + "-" + self.teams[other_team_id].name, self.teams[other_team_id].name, {"capacity": remaining_games, 'flow':0}))
                    source_edges.append(("source", self.teams[id].name + "-" + self.teams[other_team_id].name, {"capacity": remaining_games, 'flow':0}))
                    saturated_edges[self.teams[id].name + "-" + self.teams[other_team_id].name] = remaining_games

        self.G.add_edges_from(sink_edges)
        self.G.add_edges_from(mid_edges)
        self.G.add_edges_from(source_edges)

        return saturated_edges
       

    def network_flows(self, saturated_edges):
        '''Uses network flows to determine if the team with given team ID
        has been eliminated. You can feel free to use the built in networkx
        maximum flow function or the maximum flow function you implemented as
        part of the in class implementation activity.
        '''
        flow_value, flow_dict = nx.maximum_flow(self.G, 'source', 'sink')
        #print(saturated_edges)
        flag = False
        for match in flow_dict['source']:
            if flow_dict['source'][match] != saturated_edges[match]:
                flag = True

        return flag

    def linear_programming(self, saturated_edges):
        '''Uses linear programming to determine if the team with given team ID
        has been eliminated. We recommend using a picos solver to solve the
        linear programming problem once you have it set up.
        Do not use the flow_constraint method that Picos provides (it does all of the work for you)
        We want you to set up the constraint equations using picos (hint: add_constraint is the method you want)

        saturated_edges: 
        returns True if team is eliminated, false otherwise
        '''

        maxflow=pic.Problem()

        # creating helper dictionaries for flows and capacities for picos
        f = {}
        source_edges = []
        for edge in self.G.edges():
            #print(edge)
            # if max capacity is not infinity, then set lower bound to 0 and upper to capacity
            if self.G[edge[0]][edge[1]]['capacity'] < sys.maxsize:
                # add to flow dict, a picos variable
                f[edge] = maxflow.add_variable(
                'f[{0}]'.format(edge),1,lower=0,upper =self.G[edge[0]][edge[1]]['capacity'])
            # if max capacity is infinity, then only set lower bound to 0
            else:
                f[edge] = maxflow.add_variable(
                'f[{0}]'.format(edge),1,lower=0)

            # list of edges coming out of source
            if edge[0] is 'source':
                source_edges.append(edge)

        # adding variables, contraints, and objective
        F = maxflow.add_variable('F', 1)
        for i in self.G.nodes():
            if i == 'source':
                # add constraint, such that flow coming into the source and flow that source
                # generates is equal to flow coming out of source
                maxflow.add_constraint(pic.sum([f[p,i] for p in self.G.predecessors(i)]) +
                            F == pic.sum([f[i,p] for p in self.G.successors(i)]))
            elif i != 'sink':
                # add constraint, such that flow coming into the node is equal to flow coming out of node
                maxflow.add_constraint(pic.sum([f[p,i] for p in self.G.predecessors(i)])
                                       == pic.sum([f[i,p] for p in self.G.successors(i)]))
        # maximize flow that source generates
        maxflow.set_objective('max', F)

        # solve the problem
        maxflow.solve(verbose=0, solver='cvxopt')

        flag = False
        for flow in source_edges:
            # check to see if capacity is saturated, if not (aka diff is bigger than 0) it is eliminated
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
        # break
