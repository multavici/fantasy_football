from app import create_app, db
from app.models import Player, Team
from config import Config
import os

app = create_app(Config)
app_context = app.app_context()
app_context.push()

print(db)

team = Team.query.get(1)

print(team)

f = open('megascore_players.csv', 'r')

for line in f:
    id, name, team_id, value, sporza_name = line.split(';')
    if id != '"id"':
        p = Player(name=name[1:-1], value=value[1:-1], team_id=team_id[1:-1])
        print(p)
        db.session.add(p)

db.session.commit()