from baseball_elimination import Division

def assert_eliminated(division, team):
    try:
        assert division.is_eliminated(team.get_ID(), "Linear Programming") == True
    except AssertionError:
        print("Failure in linear programming is eliminated: " + team.name + " should be eliminated.")
    try:
        assert division.is_eliminated(team.get_ID(), "Network Flows") == True
    except AssertionError:
        print("Failure in network flows is eliminated: " + team.name + " should be eliminated.")

def assert_not_eliminated(division, team):
    try:
        assert division.is_eliminated(team.get_ID(), "Linear Programming") == False
    except AssertionError:
        print("Failure in linear programming is eliminated: " + team.name + " should NOT be eliminated.")
    try:
        assert division.is_eliminated(team.get_ID(), "Network Flows") == False
    except AssertionError:
        print("Failure in network flows is eliminated: " + team.name + " should NOT be eliminated.")

def test_teams2():
    division = Division("teams2.txt")
    for (ID, team) in division.teams.items():
        if team.name == "NewYork" or team.name == "Baltimore" or team.name == "Boston" or team.name == "Toronto":
            assert_not_eliminated(division, team)
        elif team.name == "Detroit":
            assert_eliminated(division, team)

def test_teams4():
    division = Division("teams4.txt")
    for (ID, team) in division.teams.items():
        if team.name == "Prava" or team.name == "Vicky":
            assert_eliminated(division, team)
        elif team.name == "Emily" or team.name == "Shashank":
            assert_not_eliminated(division, team)

if __name__ == '__main__':
    test_teams2()
    test_teams4()
    print("All tests have completed.")
