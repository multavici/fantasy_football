from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from app import app, db, login
from flask_login import UserMixin
from hashlib import md5
from time import time
import jwt

followers = db.Table('followers', 
    db.Column('follower_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('followed_id', db.Integer, db.ForeignKey('user.id'))
)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    posts = db.relationship('Post', backref='author', lazy='dynamic')
    about_me = db.Column(db.String(140))
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return '<User: {}>'.format(self.username)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(digest, size)
    
    followed = db.relationship(
        'User', secondary=followers,
        primaryjoin=(followers.c.follower_id == id),
        secondaryjoin=(followers.c.followed_id == id),
        backref=db.backref('followers', lazy='dynamic'), lazy='dynamic'
    )

    def follow(self, user):
        if not self.is_following(user):
            self.followed.append(user)
    
    def unfollow(self, user):
        if self.is_following(user):
            self.followed.remove(user)
    
    def is_following(self, user):
        return self.followed.filter(followers.c.followed_id == user.id).count() > 0
    
    def followed_posts(self):
        followed = Post.query.join(
            followers, (followers.c.followed_id == Post.user_id)).filter(
                followers.c.follower_id == self.id)
        own = Post.query.filter_by(user_id=self.id)
        return followed.union(own).order_by(Post.timestamp.desc())
    
    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {'reset_password': self.id, 'exp': time() + expires_in},
            app.config['SECRET_KEY'], algorithm='HS256'
        ).decode('utf-8')
    
    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, app.config['SECRET_KEY'], algoritms=['HS256'])['reset_password']
        except:
            return
        return User.query.get(id)
            

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.String(140))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return '<Post: {}>'.format(self.body)


@login.user_loader
def load_user(id):
    return User.query.get(int(id))


class Team(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    teamname = db.Column(db.String(64), index=True, unique=True, nullable=False)
    # players = db.relationship('Player', backref='team', lazy=True)

    def result(self, match):
        if match.home_team == self:
            if match.home_score > match.away_score:
                return 'win'
            if match.home_score < match.away_score:
                return 'loss'
            else:
                return 'draw'
        if match.away_team == self:
            if match.home_score > match.away_score:
                return 'loss'
            if match.home_score < match.away_score:
                return 'win'
            else:
                return 'draw'
    
    def __repr__(self):
        return self.teamname


class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), index=True, nullable=False)
    value = db.Column(db.Integer)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'))
    # to scrape the match data we need to have the name of the player in the sporza databasead
    sporza_name = db.Column(db.String(128))

    team = db.relationship('Team', backref='players')

    def __repr__(self):
        return '<Player: {}>'.format(self.name)

    def as_dict(self):
        return {'name': self.name, 'team': self.team.teamname, 'value': self.value}

    def squad_appearance(self, match):
        try:
            return SquadAppearance.query.filter_by(player_id=self.id, match_id=match.id).one()
        except:
            return False


class Match(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    matchday_id = db.Column(db.Integer, db.ForeignKey('matchday.id'))
    home_team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    away_team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    home_score = db.Column(db.Integer)
    away_score = db.Column(db.Integer)
    finished = db.Column(db.Boolean, default=False)

    home_team = db.relationship('Team', foreign_keys=[home_team_id], backref='home_matches')
    away_team = db.relationship('Team', foreign_keys=[away_team_id], backref='away_matches')
    matchday = db.relationship('Matchday', backref='matches')

    def __repr__(self):
        return '<Match: {} - {}: {}-{}>'.format(self.home_team.teamname, self.away_team.teamname, self.home_score,
                                                self.away_score)

    def slugify(self):
        return '{}-{}'.format(self.home_team.teamname.lower().replace(" ", "-"),
                              self.away_team.teamname.lower().replace(" ", "-"))


class Matchday(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    finished = db.Column(db.Boolean, default=False)


class FantasyTeam(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    formation = db.Column(db.String(3))

    user = db.relationship('User', backref='fantasy_teams')

    def __repr__(self):
        return '<Fantasy Team: {}>'.format(self.name)

    def get_players_of_pos(self, position):
        return FantasyPlayer.query.filter_by(team_id=self.id, position=position, sub=False).all()

    def matchday_score(self, matchday):
        score = 0
        for fp in self.fantasy_players:
            score += fp.matchday_score(matchday) if fp.matchday_score(matchday) != "-" else 0
        return score

    def total_score(self):
        matchdays = Matchday.query.filter_by(finished=True).all()
        total_score = 0
        for matchday in matchdays:
            total_score += self.matchday_score(matchday)
        return total_score


class FantasyPlayer(db.Model):
    player_id = db.Column(db.Integer, db.ForeignKey('player.id'), primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('fantasy_team.id'), primary_key=True)
    number = db.Column(db.Integer, db.CheckConstraint('number<15'), nullable=False)
    position = db.Column(db.String(2), nullable=False)
    sub = db.Column(db.Boolean)

    player = db.relationship('Player', backref='fantasy_teams')
    fantasy_team = db.relationship('FantasyTeam', backref='fantasy_players')

    def __repr__(self):
        return '<Fantasy Player: {} for {} as {}>'.format(self.player.name, self.fantasy_team.name, self.position)

    def raw_score(self, matchday):
        match = self.match_on(matchday)
        if self.player.squad_appearance(match) and self.player.squad_appearance(match).minutes_played() > 0:
            score = 0
            score += self.player.squad_appearance(match).count_field_goals() * 5
            score += self.player.squad_appearance(match).count_penalties_scored() * 3
            score += self.player.squad_appearance(match).count_own_goals() * (-3)
            score += self.player.squad_appearance(match).count_yellow_cards() * (-1)
            score += self.player.squad_appearance(match).count_second_yellow_cards() * (-2)
            score += self.player.squad_appearance(match).count_red_cards() * (-3)
            if self.player.squad_appearance(match).minutes_played() > 0:
                score += 2
                if self.player.team.result(match) == 'win':
                    score += 3
                if self.player.team.result(match) == 'draw':
                    score += 1
                if self.player.squad_appearance(match).minutes_played() > 60:
                    score += 1
        else:
            score = "-"
        return score

    def match_on(self, matchday):
        return (Match.query.filter_by(matchday_id=matchday.id, home_team_id=self.player.team_id).first() or
                Match.query.filter_by(matchday_id=matchday.id, away_team_id=self.player.team_id).first())

    def subbed_in_on(self, matchday):
        for p in self.fantasy_team.get_players_of_pos(self.position):
            if p.raw_score(matchday) == "-":
                return True
        return False

    def matchday_score(self, matchday):
        if not self.sub:
            return self.raw_score(matchday)
        else:
            if self.subbed_in_on(matchday):
                return self.raw_score(matchday)
            else:
                return "-"


class SquadAppearance(db.Model):
    player_id = db.Column(db.Integer, db.ForeignKey('player.id'), primary_key=True)
    match_id = db.Column(db.Integer, db.ForeignKey('match.id'), primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    starting = db.Column(db.Boolean, nullable=False)

    player = db.relationship('Player', backref='squad_appearances')
    match = db.relationship('Match', backref='squads')
    team = db.relationship('Team', backref='squad')

    def __repr__(self):
        if self.starting:
            return '<Squad Appearance from {} in match {} in the starting lineup>'.format(self.player.name, self.match)
        else:
            return '<Squad Appearance from {} in match {} as a substitute>'.format(self.player.name, self.match)

    def count_field_goals(self):
        return Goal.query.filter_by(scorer_id=self.player_id, match_id=self.match_id, goal_type='field_goal').count()

    def count_penalties_scored(self):
        return Goal.query.filter_by(scorer_id=self.player_id, match_id=self.match_id, goal_type='penalty_scored').count()

    def count_own_goals(self):
        return Goal.query.filter_by(scorer_id=self.player_id, match_id=self.match_id, goal_type='own_goal').count()

    def count_yellow_cards(self):
        return Card.query.filter_by(player_id=self.player_id, match_id=self.match_id, card_type='yellow').count()

    def count_second_yellow_cards(self):
        return Card.query.filter_by(player_id=self.player_id, match_id=self.match_id, card_type='second_yellow').count()

    def count_red_cards(self):
        return Card.query.filter_by(player_id=self.player_id, match_id=self.match_id, card_type='red').count()

    def get_subbed_out_minute(self):
        sub = Substitution.query.filter_by(player_out_id=self.player_id, match_id=self.match_id).first()
        if sub:
            return sub.minute
        else:
            return None

    def get_subbed_in_minute(self):
        sub = Substitution.query.filter_by(player_in_id=self.player_id, match_id=self.match_id).first()
        if sub:
            return sub.minute
        else:
            return None

    # TODO: fix time issues (final time of each match should be saved to calculate real minutes played)
    def minutes_played(self):
        if self.starting:
            if self.get_subbed_out_minute():
                return self.get_subbed_out_minute() if self.get_subbed_out_minute() < 90 else 90
            else:
                return 90
        else:
            if self.get_subbed_in_minute() and self.get_subbed_in_minute() < 90:
                if not self.get_subbed_out_minute():
                    return 90 - self.get_subbed_in_minute()
                else:
                    return self.get_subbed_out_minute() - self.get_subbed_in_minute()
            else:
                return 0


class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    match_id = db.Column(db.Integer, db.ForeignKey('match.id'))
    minute = db.Column(db.Integer, nullable=False)
    home = db.Column(db.Boolean)
    # possible types: 'goal', 'card', 'substitution', 'penalty_missed'
    type = db.Column(db.String(10))

    match = db.relationship('Match', backref='events')

    __mapper_args__ = {
        'polymorphic_identity': 'event',
        'polymorphic_on': type
    }


class Goal(Event):
    id = db.Column(db.Integer, db.ForeignKey('event.id'), primary_key=True)
    scorer_id = db.Column(db.Integer, db.ForeignKey('player.id'), nullable=False)
    assist_giver_id = db.Column(db.Integer, db.ForeignKey('player.id'))
    keeper_id = db.Column(db.Integer, db.ForeignKey('player.id'))
    home_score = db.Column(db.Integer)
    away_score = db.Column(db.Integer)
    # possible types: 'field_goal', 'penalty_scored', 'own_goal'
    goal_type = db.Column(db.String(10))

    scorer = db.relationship('Player', foreign_keys=[scorer_id], backref='goals')
    assist_giver = db.relationship('Player', foreign_keys=[assist_giver_id], backref='assists')
    keeper = db.relationship('Player', foreign_keys=[keeper_id], backref='goals_conceded')

    __mapper_args__ = {
        'polymorphic_identity': 'goal',
    }

    def for_team(self):
        if self.home:
            return self.match.home_team
        else:
            return self.match.away_team

    def describe(self):
        desc = "{}': {} - {}! ".format(self.minute, self.home_score, self.away_score)
        if self.goal_type == 'field_goal':
            desc += '{} scores for {}.'.format(self.scorer.name, self.for_team().teamname)
            if self.assist_giver_id:
                desc += 'Assist by {}'.format(self.assist_giver.name)
        if self.goal_type == 'penalty_scored':
            desc += 'Penalty for {} scored by {}'.format(self.for_team().teamname, self.scorer.name)
        if self.goal_type == 'own_goal':
            desc += 'Goal for {}. Own-goal by {}'.format(self.for_team().teamname, self.scorer.name)
        return desc


class Card(Event):
    id = db.Column(db.Integer, db.ForeignKey('event.id'), primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey('player.id'))
    # possible types: 'yellow', 'second_yellow', 'red'
    card_type = db.Column(db.String(10))

    player = db.relationship('Player', backref='cards')

    __mapper_args__ = {
        'polymorphic_identity': 'card',
    }

    def describe(self):
        return "{}': {} card for {}".format(self.minute, self.card_type.capitalize(), self.player.name)


class Substitution(Event):
    id = db.Column(db.Integer, db.ForeignKey('event.id'), primary_key=True)
    player_in_id = db.Column(db.Integer, db.ForeignKey('player.id'))
    player_out_id = db.Column(db.Integer, db.ForeignKey('player.id'))

    player_in = db.relationship('Player', foreign_keys=[player_in_id], backref='substitutions_in')
    player_out = db.relationship('Player', foreign_keys=[player_out_id], backref='substitutions_out')

    __mapper_args__ = {
        'polymorphic_identity': 'substitution',
    }

    def describe(self):
        return "{}': Substitution: {} out, {} in".format(self.minute, self.player_out.name, self.player_in.name)


class PenaltyMissed(Event):
    id = db.Column(db.Integer, db.ForeignKey('event.id'), primary_key=True)
    taker_id = db.Column(db.Integer, db.ForeignKey('player.id'))
    keeper_id = db.Column(db.Integer, db.ForeignKey('player.id'))
    # possible types: 'missed', 'stopped'
    stopped_by_keeper = db.Column(db.Boolean)

    taker = db.relationship('Player', foreign_keys=[taker_id], backref='penalties_missed')
    keeper = db.relationship('Player', foreign_keys=[keeper_id], backref='penalties_missed_against')

    __mapper_args__ = {
        'polymorphic_identity': 'penalty_missed',
    }

    def describe(self):
        if self.stopped_by_keeper:
            "{}': Penalty from {} stopped by {}".format(self.minute, self.taker.name, self.keeper.name)
        else:
            "{}': Penalty missed by {}".format(self.minute, self.taker.name)
