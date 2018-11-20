from app import create_app, db
from config import Config
import requests
from bs4 import BeautifulSoup
from app.models import Match, Player, SquadAppearance, Event, Goal, Card, Substitution, PenaltyMissed
import json

app = create_app(Config)
app_context = app.app_context()
app_context.push()


def get_textfile(match_id):
    # if textfile already exists, skip
    try:
        open('files/' + str(match_id) + ".txt", "r")
        return 1
    except FileNotFoundError:
        match = Match.query.get(match_id)
        if match.matchday < 10:
            matchday_string = "0" + str(match.matchday)
        else:
            matchday_string = str(match.matchday)
        print("matchday: " + matchday_string)
        url = ("https://sporza.be/nl/matches/voetbal/jupiler-pro-league/2018-2019/regulier/" + matchday_string + "/"
               + match.slugify())
        print(url)
        page = requests.get(url)
        soup = BeautifulSoup(page.text, 'html.parser')
        json_text_utf = soup.find('script', attrs={'data-hypernova-key': 'Timeline'}).get_text()[4:-3]
        f = open('files/' + str(match.id) + ".txt", "w+")
        f.write(json_text_utf)
        print(str(match.id) + ".txt has been made")


def input_db(match_id):
    print('match ' + str(match_id))
    # get the match info
    match = Match.query.get(match_id)

    # get the json_text
    f = open('files/' + str(match_id) + ".txt", "r")
    json_text = f.read()
    match_dict = json.loads(json_text)

    # get all involved players
    home_lineup = match_dict["data"]["homeSquad"]["lineup"]
    home_substitutes = match_dict["data"]["homeSquad"]["substitutes"]

    away_lineup = match_dict["data"]["awaySquad"]["lineup"]
    away_substitutes = match_dict["data"]["awaySquad"]["substitutes"]

    playersdict = {}
    for row in home_lineup:
        playersdict[row["player"]["name"]] = {"shortName": row["player"]["shortName"], "starting": True,
                                              "team_id": match.home_team_id}
    for row in home_substitutes:
        playersdict[row["player"]["name"]] = {"shortName": row["player"]["shortName"], "starting": False,
                                              "team_id": match.home_team_id}
    for row in away_lineup:
        playersdict[row["player"]["name"]] = {"shortName": row["player"]["shortName"], "starting": True,
                                              "team_id": match.away_team_id}
    for row in away_substitutes:
        playersdict[row["player"]["name"]] = {"shortName": row["player"]["shortName"], "starting": False,
                                              "team_id": match.away_team_id}

    # check if players are in database
    for raw_player in playersdict:
        # try to look for the player in the database
        try:
            player = Player.query.filter(Player.name.like(raw_player)).one()
            print(raw_player + ' is in the database with id: ' + str(player.id))
        except:
            try:
                player = Player.query.filter(Player.sporza_name.like(raw_player)).one()
                print(raw_player + ' is in the database with id: ' + str(player.id))
            except:
                try:
                    player = Player.query.filter(Player.name.like('%' + playersdict[raw_player]["shortName"] + '%')).one()
                    q = input(
                        'sporza player ' + raw_player + ' was not found in the db. We did find ' + player.name + '. '
                        + 'Do you want to add the sporza name to the db'
                        + ' so in the future this player is recognized? (y/n)')
                    if q == 'y':
                        player.sporza_name = raw_player
                    if q == 'n':
                        print(raw_player + ' has not been found in the database')
                        raise SystemExit(0)
                except:
                    q = input(raw_player + ' has not been found in the database. Do you want to add this player? (y/n)')
                    if q == 'y':
                        q2 = input("What's the value of the player (as an integer value, x10)?")
                        p = Player(name=raw_player, value=int(q2), team_id=playersdict[raw_player]["team_id"])
                        db.session.add(p)
                        db.session.flush()
                    else:
                        print(raw_player + ' has not been found in the database')
                        raise SystemExit(0)

    # add SquadAppearance
    for raw_player in playersdict:
        try:
            player = Player.query.filter(Player.name.like(raw_player)).one()
        except:
            player = Player.query.filter(Player.sporza_name.like(raw_player)).one()
        sa = SquadAppearance(player_id=player.id, match_id=match.id, team_id=match.home_team.id,
                             starting=playersdict[raw_player]["starting"])
        db.session.add(sa)
        db.session.flush()
        print(sa)
        playersdict[raw_player]["id"] = player.id

    # get events
    raw_events = match_dict["data"]["events"]

    for raw_event in raw_events:
        # check if event is one of the events that interests us
        # TODO: make a better system for time capturing
        if raw_event["type"] in ["SUBSTITUTION", "GOAL", "YELLOW_CARD", "RED_CARD", "YELLOW_TO_RED_CARD", "OWN_GOAL",
                                 "PENALTY_GOAL"]:
            # if the event happens during half time the time is saved with a ':' in the sporza database
            minute = 0
            if ':' in raw_event["time"]:
                minute = 46
            else:
                # remove the minute sign and split the extra time minutes (e.g. 90+7')
                # and then sum to get to the total minute (97)
                minutes = raw_event["time"][:-1].split("+")
                for number in minutes:
                    minute += int(number)
            if raw_event["owner"] == "HOME":
                home = True
            else:
                home = False

        if raw_event["type"] == "SUBSTITUTION":
            sub = Substitution(match_id=match.id, minute=minute, home=home, type='substitution',
                               player_in_id=playersdict[raw_event['in']['name']]['id'],
                               player_out_id=playersdict[raw_event['out']['name']]['id'])
            db.session.add(sub)
            db.session.flush()
            print(sub.describe())

        # TODO: add assist-giver
        if raw_event["type"] == "GOAL":
            goal = Goal(match_id=match.id, minute=minute, home=home, type='goal',
                        scorer_id=playersdict[raw_event['player']['name']]['id'],
                        home_score=raw_event['homeScore'], away_score=raw_event['awayScore'], goal_type='field_goal')
            db.session.add(goal)
            db.session.flush()
            print(goal.describe())

        if raw_event['type'] == "YELLOW_CARD":
            card = Card(match_id=match.id, minute=minute, home=home, type='card',
                        player_id=playersdict[raw_event["player"]["name"]]["id"], card_type='yellow')
            db.session.add(card)
            db.session.flush()
            print(card.describe())

        if raw_event['type'] == "RED_CARD":
            card = Card(match_id=match.id, minute=minute, home=home, type='card',
                        player_id=playersdict[raw_event["player"]["name"]]["id"], card_type='red')
            db.session.add(card)
            db.session.flush()
            print(card.describe())

        if raw_event['type'] == "OWN_GOAL":
            goal = Goal(match_id=match.id, minute=minute, home=home, type='goal',
                        scorer_id=playersdict[raw_event['player']['name']]['id'],
                        home_score=raw_event['homeScore'], away_score=raw_event['awayScore'], goal_type='own_goal')
            db.session.add(goal)
            db.session.flush()
            print(goal.describe())

        # TODO: add keeper
        if raw_event['type'] == "PENALTY_GOAL":
            goal = Goal(match_id=match.id, minute=minute, home=home, type='goal',
                        scorer_id=playersdict[raw_event['player']['name']]['id'], home_score=raw_event['homeScore'],
                        away_score=raw_event['awayScore'], goal_type='penalty_scored')
            db.session.add(goal)
            db.session.flush()
            print(goal.describe())

    # get the final score of the match:
    final_goal = Goal.query.filter_by(match_id=match.id).order_by(Goal.minute.desc()).first()
    if final_goal:
        match.home_score = final_goal.home_score
        match.away_score = final_goal.away_score
    else:
        match.home_score = 0
        match.away_score = 0

    db.session.commit()
    match.finished = True
    db.session.commit()


for i in range(121, 122):
    get_textfile(i)
    input_db(i)
