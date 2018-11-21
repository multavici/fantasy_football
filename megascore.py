from app import create_app, db
from app.models import User, Post, Team, Player, Match, FantasyPlayer, FantasyTeam, SquadAppearance, Event, Goal, Card, Substitution, PenaltyMissed, Matchday

app = create_app()

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Post': Post, 'Team': Team, 'Player': Player, 'Match': Match,
            'FantasyTeam': FantasyTeam, 'FantasyPlayer': FantasyPlayer, 'SquadAppearance': SquadAppearance,
            'Event': Event, 'Goal': Goal, 'Card': Card, 'Substitution': Substitution, 'PenaltyMissed': PenaltyMissed,
            'Matchday': Matchday}