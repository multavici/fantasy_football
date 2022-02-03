from app import create_app, db
from config import Config
import requests
from app.models import Player, Team

# from selenium import webdriver
# from selenium.webdriver.chrome.options import Options

app = create_app(Config)
app_context = app.app_context()
app_context.push()

def get_teams():
    page = requests.get("https://gaming.uefa.com/en/uefaeuro2020fantasyfootball/services/api/Feed/players?matchdayId=1&lang=en&tour_id=1")
    playerlist = page.json()['data']['value']['playerList']
    teams = set()
    for player in playerlist:
        teams.add(player['tName'])
    for team in teams:
        db.session.add(Team(teamname=team))
    db.session.commit()

def get_players():
    page = requests.get("https://gaming.uefa.com/en/uefaeuro2020fantasyfootball/services/api/Feed/players?matchdayId=1&lang=en&tour_id=1")
    playerlist = page.json()['data']['value']['playerList']
    for player in playerlist:
        team = Team.query.filter(Team.teamname.like(player['tName'])).one()
        p = Player(
            name=player['pFName'],
            value=player['value'],
            team_id = team.id
        )
        db.session.add(p)
    db.session.commit()

if __name__ == "__main__":
    get_teams()
    # get_players()