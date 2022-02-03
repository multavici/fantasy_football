import requests


payload={}
headers = {
  'x-rapidapi-key': '8711de0c5bfd05a04c6a6fe29ff66afc',
  'x-rapidapi-host': 'v3.football.api-sports.io'
}

# url = "https://v3.football.api-sports.io/leagues"
# response = requests.request("GET", url, headers=headers, data=payload)
# with open('/Users/falkvandermeirsch/projects/fantasy_football/megascore/data/leagues.json', 'w+') as f:
#     f.write(response.text)

url = "https://v3.football.api-sports.io/fixtures/rounds?season=2020&league=4"
response = requests.request("GET", url, headers=headers, data=payload)
with open('/Users/falkvandermeirsch/projects/fantasy_football/megascore/data/rounds.json', 'w+') as f:
    f.write(response.text)

# url = "https://v3.football.api-sports.io/fixtures?league=4&season=2020"
# response = requests.request("GET", url, headers=headers, data=payload)
# with open('/Users/falkvandermeirsch/projects/fantasy_football/megascore/data/fixtures.json', 'w+') as f:
#     f.write(response.text)
