from datetime import datetime
from flask import render_template, flash, redirect, url_for, request, current_app, jsonify
from flask_login import current_user, login_required
from app import db
from app.main.forms import EditProfileForm, PostForm, FantasyTeamForm
from app.models import User, Post, Team, Player, Match, FantasyPlayer, FantasyTeam
from app.main import bp

position = {
    '433': ['GK', 'D', 'D', 'D', 'D', 'M', 'M', 'M', 'A', 'A', 'A', 'GK', 'D', 'M', 'A'],
    '442': ['GK', 'D', 'D', 'D', 'D', 'M', 'M', 'M', 'M', 'A', 'A', 'GK', 'D', 'M', 'A'],
    '352': ['GK', 'D', 'D', 'D', 'M', 'M', 'M', 'M', 'M', 'A', 'A', 'GK', 'D', 'M', 'A']
}

@bp.before_app_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()


@bp.route('/', methods=['GET', 'POST'])
@bp.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(body=form.post.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash('Your post is now live!')
        return redirect(url_for('main.index'))
    page = request.args.get('page', 1, type=int)
    posts = current_user.followed_posts().paginate(page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('main.index', page=posts.next_num) if posts.has_next else None
    prev_url = url_for('main.index', page=posts.prev_num) if posts.has_prev else None
    return render_template('index.html', title='Home Page', form=form, posts=posts.items,
                           next_url=next_url, prev_url=prev_url)


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


@bp.route('/follow/<username>')
@login_required
def follow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('User {} not found'.format(username))
        return redirect(url_for('main.index'))
    if user == current_user:
        flash('You can not follow yourself')
        return redirect(url_for('main.user', username=username))
    current_user.follow(user)
    db.session.commit()
    flash('You are now following {}'.format(username))
    return redirect(url_for('main.user', username=username))


@bp.route('/unfollow/<username>')
@login_required
def unfollow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('User {} not found'.format(username))
        return redirect(url_for('main.index'))
    if user == current_user:
        flash('You can not unfollow yourself')
        return redirect(url_for('main.user', username=username))
    current_user.unfollow(user)
    db.session.commit()
    flash('You are not following {}'.format(username))
    return redirect(url_for('main.user', username=username))


@bp.route('/explore')
@login_required
def explore():
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.timestamp.desc()).paginate(page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('main.explore', page=posts.next_num) if posts.has_next else None
    prev_url = url_for('main.explore', page=posts.prev_num) if posts.has_prev else None
    return render_template('index.html', title="Explore", posts=posts.items,
                           next_url=next_url, prev_url=prev_url)


@bp.route('/view_teams')
@login_required
def view_teams():
    teams = Team.query.all()
    return render_template('view_teams.html', title="View Teams", teams=teams)


@bp.route('/view_players')
@login_required
def view_players():
    players = Player.query.all()
    return render_template('view_players.html', title="View Players", players=players)


@bp.route('/matches')
@login_required
def matches():
    matches = Match.query.order_by(Match.matchday).all()
    return render_template('matches.html', title='Matches', matches=matches)


@bp.route('/<team_name>')
@login_required
def my_fantasy_team(team_name):
    team = FantasyTeam.query.filter_by(name=team_name).first()
    return render_template('fantasy_team.html', title='Fantasy Team', team=team)


@bp.route('/players')
@login_required
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
@login_required
def match(match_id):
    match = Match.query.get(match_id)
    print(match.events)
    return render_template('match_detail.html', match=match)