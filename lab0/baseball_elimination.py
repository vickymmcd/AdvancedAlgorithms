# translated to python from https://github.com/ananya77041/baseball-elimination/blob/master/src/BaseballElimination.java

class Division:
    def __init__(self, filename):
        pass

    def is_eliminated(team):
        pass

    def flow_check(team):
        pass

class Team:
    def __init__(self, teamname):
        name = teamname


if __name__ == '__main__':
    filename = sys.argv[1]
    division = Division(filename)
    for team in division.teams:
        print(team.name + ": Eliminated? " + division.is_eliminated(team))
