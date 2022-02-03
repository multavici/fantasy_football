import json

from app import create_app, db
from config import Config
from app.models import Matchday, Match, Team

app = create_app(Config)
app_context = app.app_context()
app_context.push()


# with open('/Users/falkvandermeirsch/projects/fantasy_football/megascore/data/leagues.json') as f:
#     text = f.read()
# print(json.loads(text)['response'][0])

with open('/Users/falkvandermeirsch/projects/fantasy_football/megascore/data/fixtures.json') as f:
    text = f.read()
matches = json.loads(text)['response']
for match in matches:
    if match['league']['round'].startswith('Group'):
        round = match['league']['round'][-1]
        matchday = Matchday.query.get(round)
        home_team = Team.query.filter(Team.teamname.like(match['teams']['home']['name'])).one()
        away_team = Team.query.filter(Team.teamname.like(match['teams']['away']['name'])).one()
        match_obj = Match(
            matchday_id=matchday.id,
            home_team_id=home_team.id,
            away_team_id=away_team.id,
        )
        db.session.add(match_obj)
db.session.commit()


# dict_keys(['get', 'parameters', 'errors', 'results', 'paging', 'response'])

# with open('/Users/falkvandermeirsch/projects/fantasy_football/megascore/data/rounds.json') as f:
#     text = f.read()
# rounds = json.loads(text)['response']
# print(rounds)