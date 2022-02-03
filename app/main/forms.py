from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, RadioField, FieldList
from wtforms.validators import DataRequired, ValidationError, Length
from app.models import User
from flask import flash
from decimal import *


class EditProfileForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    about_me = TextAreaField('About me', validators=[Length(min=0, max=140)])
    submit = SubmitField('Submit')

    def __init__(self, original_username, *args, **kwargs):
        super(EditProfileForm, self).__init__(*args, **kwargs)
        self.original_username = original_username
    
    def validate_username(self, username):
        if username.data != self.original_username:
            user = User.query.filter_by(username=self.username.data).first()
            if user is not None:
                raise ValidationError('Please use different username.')


class PostForm(FlaskForm):
    post = TextAreaField('Say something', validators=[DataRequired(), Length(min=1, max=140)])
    submit = SubmitField('Submit')


class FantasyTeamForm(FlaskForm):
    teamname = StringField('Team Name', validators=[DataRequired(), Length(max=40)])
    formation = RadioField(
        label='Formation', 
        choices=[
            ('433', '433'), 
            ('442', '442'), 
            ('352', '352'), 
            ('343', '343'),
            ('451', '451'),
            ('523', '523'),
            ('532', '532'),
            ('541', '541'),
        ], 
        default='433'
    )
    players = FieldList(StringField('Name', validators=[DataRequired()]), min_entries=15)

    def validate(self):
        if not FlaskForm.validate(self):
            return False
        result = True
        # check if not two the same players are selected
        picked = []
        for player in self.players:
            if player.data in picked:
                player.errors.append('Please select distinct players')
                result = False
            else:
                picked.append(player.data)

        # check if more than max amount of players from the same team is picked
        # players_per_team = dict()
        # for player in self.players:
        #     team = player.data.split(" - ")[1]
        #     if players_per_team.get(team):
        #         if players_per_team[team] == 3:
        #             player.errors.append('Please select maximum 3 players of the same team')
        #             result = False
        #         else:
        #             players_per_team[team] += 1
        #     else:
        #         players_per_team[team] = 1

        # check if players per team is valid
        players_per_team = dict()
        for player in self.players:
            team = player.data.split(" - ")[1]
            if players_per_team.get(team):
                players_per_team[team] += 1
            else:
                players_per_team[team] = 1
        players_per_team_list = list(players_per_team.values())
        players_per_team_list.sort(reverse=True)
        if players_per_team_list[0] > 3 or players_per_team_list[1] > 2:
            flash(f"You can choose maximum 3 players from 1 team and maximum 2 players of the rest, please choose other players", 'alert-danger')
            result = False


        # check if total value is less than max value
        total_value = 0
        for player in self.players:
            value = Decimal(player.data.split(" - ")[2])
            total_value += value
        if total_value > 100:
            flash('The maximum value is 100, the total value of these players is ' + str(total_value) + ', please choose cheaper players', 'alert-danger')
            result = False

        return result
