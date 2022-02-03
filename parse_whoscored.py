import json

from app import create_app, db
from config import Config
from app.models import Match, Player, SquadAppearance, Event, Goal, Card, Substitution, PenaltyMissed
from fuzzywuzzy import fuzz

app = create_app(Config)
app_context = app.app_context()
app_context.push()

with open("data/matches/match_1.json", "r") as f:
    text = f.read()
match_dict = json.loads(text)

# Get win information
# print(json.dumps(d, indent=2))
# print(d.keys())
print(match_dict['score'])
match = Match.query.get(1)
match.home_score = match_dict['home']['scores']['fulltime']
match.away_score = match_dict['away']['scores']['fulltime']
match.finished = True
# print("home team:", match_dict['home']['scores']['fulltime'])
# print("home team:", match_dict['away']['scores']['fulltime'])
print(match)
print(match.home_team_id)

def parse_squad_appearance(match: Match, raw_player: dict, players_in_db: list, home: bool=True):
    try:
        player = Player.query.filter(Player.name.like(raw_player['name'])).one()
    except:
        players_in_db.sort(key=lambda p: fuzz.ratio(raw_player['name'], p.name))
        player = players_in_db[-1]
    print(f"{raw_player['name']} is in the database as: {player.name}")

    if raw_player['stats'].get('ratings'):
        last_minute = max(raw_player['stats']['ratings'].keys())
        rating = int(raw_player['stats']['ratings'][last_minute] * 10)
    else:
        rating = None
    print("rating: ", rating)

    sa = SquadAppearance(
        player_id = player.id, 
        match_id = match.id, 
        team_id = match.home_team_id if home else match.away_team_id,
        starting = True if raw_player.get('isFirstEleven') else False,
        man_of_the_match = raw_player['isManOfTheMatch'],
        rating = rating
    )
    db.session.add(sa)
    db.session.flush()
    print(sa)
    print(sa.rating)
    # playersdict[raw_player]["id"] = player.id

players_in_db = Player.query.filter(Player.team_id == match.home_team_id).all()
for raw_player in match_dict['home']['players']:
    parse_squad_appearance(match=match, raw_player=raw_player, players_in_db=players_in_db, home=True)

players_in_db = Player.query.filter(Player.team_id == match.away_team_id).all()
for raw_player in match_dict['away']['players']:
    parse_squad_appearance(match=match, raw_player=raw_player, players_in_db=players_in_db, home=False)

def parse_event():
    pass

exit()

# Get home team data
players_in_db = Player.query.filter(Player.team_id == match.home_team_id).all()
for raw_player in match_dict['home']['players']:
    print(raw_player['name'])
    # try to look for the player in the database
    try:
        player = Player.query.filter(Player.name.like(raw_player['name'])).one()
        print(f"{raw_player['name']} is in the database with id: {player.id}")
    except:
        players_in_db.sort(key=lambda p: fuzz.ratio(raw_player['name'], p.name))
        player = players_in_db[-1]
        print(f"{raw_player['name']} is in the database with id: {player.id}")

    if raw_player['stats'].get('ratings'):
        last_minute = max(raw_player['stats']['ratings'].keys())
        rating = int(raw_player['stats']['ratings'][last_minute] * 10)
        print("rating: ", rating)
    else:
        rating = None
    sa = SquadAppearance(
        player_id = player.id, 
        match_id = match.id, 
        team_id = match.home_team_id,
        starting = True if raw_player.get('isFirstEleven') else False,
        man_of_the_match = raw_player['isManOfTheMatch'],
        rating = rating
    )
    db.session.add(sa)
    db.session.flush()
    print(sa)
    print(sa.rating)
    # playersdict[raw_player]["id"] = player.id

# Get away team data
players_in_db = Player.query.filter(Player.team_id == match.away_team_id).all()
for raw_player in match_dict['away']['players']:
    print(raw_player['name'])
    # try to look for the player in the database
    try:
        player = Player.query.filter(Player.name.like(raw_player['name'])).one()
        print(f"{raw_player['name']} is in the database with id: {player.id}")
    except:
        players_in_db.sort(key=lambda p: fuzz.ratio(raw_player['name'], p.name))
        player = players_in_db[-1]
        print(f"{raw_player['name']} is in the database with id: {player.id}")

    if raw_player['stats'].get('ratings'):
        last_minute = max(raw_player['stats']['ratings'].keys())
        rating = int(raw_player['stats']['ratings'][last_minute] * 10)
        print("rating: ", rating)
    else:
        rating = None
    sa = SquadAppearance(
        player_id = player.id, 
        match_id = match.id, 
        team_id = match.away_team_id,
        starting = True if raw_player.get('isFirstEleven') else False,
        man_of_the_match = raw_player['isManOfTheMatch'],
        rating = rating
    )
    db.session.add(sa)
    db.session.flush()
    print(sa)
    print(sa.rating)
    # playersdict[raw_player]["id"] = player.id

    # print(f"{raw_player['name']} not found in db")
    # not_found.append(raw_player['name'])
    # print('*******************')

    # print(player['name'])
    # starting = True if player.get('isFirstEleven') else False
    # print('starting:', starting)
    # man_of_the_match = player['isManOfTheMatch']
    # print('man of the match:', man_of_the_match)
    # if player['stats'].get('ratings'):
    #     last_minute = max(player['stats']['ratings'].keys())
    #     rating = player['stats']['ratings'][last_minute]
    #     print("rating: ", rating)

exit()

print('*******************')

event_types = set()
for event in match_dict['events']:
    event_types.add(event['type']['displayName'])
print(event_types)

print('*******************')

for event in match_dict['events']:
    if event['type']['displayName'] == 'PenaltyFaced':
        print(event)