from datetime import datetime
from flask import render_template, flash, redirect, url_for, request, current_app, jsonify
from flask_login import current_user, login_required
from app import db
from app.main.forms import EditProfileForm, PostForm, FantasyTeamForm
from app.models import User, Post, Team, Player, Match, FantasyPlayer, FantasyTeam, Matchday
from app.main import bp

position = {
    '433': ['GK', 'D', 'D', 'D', 'D', 'M', 'M', 'M', 'A', 'A', 'A', 'GK', 'D', 'M', 'A'],
    '442': ['GK', 'D', 'D', 'D', 'D', 'M', 'M', 'M', 'M', 'A', 'A', 'GK', 'D', 'M', 'A'],
    '352': ['GK', 'D', 'D', 'D', 'M', 'M', 'M', 'M', 'M', 'A', 'A', 'GK', 'D', 'M', 'A'],
    '343': ['GK', 'D', 'D', 'D', 'M', 'M', 'M', 'M', 'A', 'A', 'A', 'GK', 'D', 'M', 'A'],
    '451': ['GK', 'D', 'D', 'D', 'D', 'M', 'M', 'M', 'M', 'M', 'A', 'GK', 'D', 'M', 'A'],
    '523': ['GK', 'D', 'D', 'D', 'D', 'D', 'M', 'M', 'A', 'A', 'A', 'GK', 'D', 'M', 'A'],
    '532': ['GK', 'D', 'D', 'D', 'D', 'D', 'M', 'M', 'M', 'A', 'A', 'GK', 'D', 'M', 'A'],
    '541': ['GK', 'D', 'D', 'D', 'D', 'D', 'M', 'M', 'M', 'M', 'A', 'GK', 'D', 'M', 'A'],
}

@bp.before_app_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()


@bp.route('/', methods=['GET', 'POST'])
@bp.route('/index', methods=['GET', 'POST'])
def index():
    return render_template('index.html', title='Home Page')


@bp.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    posts = user.posts.order_by(Post.timestamp.desc()).paginate(page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('main.user', username=username, page=posts.next_num) if posts.has_next else None
    prev_url = url_for('main.user', username=username, page=posts.prev_num) if posts.has_prev else None
    return render_template('user.html', user=user, posts=posts.items, next_url=next_url, prev_url=prev_url)


@bp.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash('Your changes have been saved')
        return redirect(url_for('main.edit_profile'))
    elif request.method == "GET":
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title='Edit Profile', form=form)


@bp.route('/view_teams')
def view_teams():
    teams = Team.query.all()
    return render_template('view_teams.html', title="View Teams", teams=teams)


@bp.route('/view_players')
def view_players():
    players = Player.query.all()
    return render_template('view_players.html', title="View Players", players=players)


@bp.route('/matches')
def matches():
    matches = Match.query.all()
    matchdays = Matchday.query.all()
    return render_template('matches.html', title='Matches', matches=matches, matchdays=matchdays)


@bp.route('/teams/<team_name>')
@login_required
def my_fantasy_team(team_name):
    fteam = FantasyTeam.query.filter_by(name=team_name).first()
    matchdays = Matchday.query.filter_by(finished=True).order_by(Matchday.id).all()
    score_table = fteam.score_table()
    score_dict = {}
    total_score_per_player = {}
    total_score_per_matchday = {}
    for player_id, matchday, score in score_table:
        score_dict.setdefault(player_id, []).append(score if score is not None else '-')
        total_score_per_player.setdefault(player_id, 0)
        total_score_per_player[player_id] += (score if score is not None else 0)
        total_score_per_matchday.setdefault(matchday, 0)
        total_score_per_matchday[matchday] += (score if score is not None else 0)
    total_score = sum(total_score_per_player.values())
    return render_template(
        'fantasy_team.html', 
        title='Fantasy Team', 
        fteam=fteam, 
        matchdays=matchdays, 
        score_dict=score_dict, 
        total_score_per_player=total_score_per_player, 
        total_score_per_matchday=total_score_per_matchday,
        total_score=total_score
    )


@bp.route('/players')
def players_dict():
    players = Player.query.all()
    list_players = [player.as_dict() for player in players]
    return jsonify(list_players)


@bp.route('/create_team', methods=['GET', 'POST'])
@login_required
def create_team():
    form = FantasyTeamForm()
    if form.validate_on_submit():
        fteam = FantasyTeam(name=form.teamname.data, formation=form.formation.data, user_id=current_user.id)
        db.session.add(fteam)
        db.session.flush()
        for playerform in form.players:
            player_name = playerform.data.split(" - ")[0]
            player_number = int(playerform.name.split("-")[1])
            player = Player.query.filter_by(name=player_name).one()
            fplayer = FantasyPlayer(player_id=player.id, team_id=fteam.id, number=player_number, position=position[fteam.formation][player_number])
            db.session.add(fplayer)
        db.session.commit()
        flash('Your team: {} has been submitted'.format(fteam.name))
        return redirect(url_for('main.my_fantasy_team', team_name=fteam.name))

    players = Player.query.all()
    return render_template('create_team.html', form=form, players=players)


@bp.route('/matches/<match_id>')
def match(match_id):
    match = Match.query.get(match_id)
    return render_template('match_detail.html', match=match)


@bp.route('/players/<player_id>')
@login_required
def player(player_id):
    player = Player.query.get(player_id)
    return render_template('player_detail.html', player=player)