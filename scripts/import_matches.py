from app import create_app, db
from app.models import Match, Team
from config import Config
import os

app = create_app(Config)
app_context = app.app_context()
app_context.push()

f = open('megascore_matches.csv', 'r')

for line in f:
    id, home_team_id, away_team_id, matchday = line.split(';')
    if id != '"id"':
        m = Match(home_team_id=home_team_id[1:-1], away_team_id=away_team_id[1:-1], matchday=matchday[1:-1])
        db.session.add(m)

db.session.commit()