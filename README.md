# megascore

This is a repository with the code for a Fantasy Football website.

The project is based on the [Flask Mega Tutorial by Miguel Grinberg](https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-i-hello-world "Flask Mega Tutorial by Miguel Grinberg") as a starting point for the login and comment functionality. 
Later the main functionality was added:
* Database structure with Teams, Players, Matches, Events and Subevents (Cards, Goals, Substitutions, Penalties) on the one hand and FantasyTeams, FantasyPlayers, SquadsAppearances on the other.
* Import scripts to scrape the match data from websites
* Logic to calculate score for every FantasyPlayer/FantasyTeam
* Views to show the info and rakings to all logged-in users

The technology used is:
* Application written in Python - Flask
* Structure in different parts with Flask Blueprints
* Database management with Flask-migrate based on Alembic
* Connection beween app and database with Flask-SQLAlchemy based on SQLAlchemy ORM
* Forms with Flask-WTF based on WTForms
* Templates with Jinja2
* CSS with Flask-Bootstrap
* Some custom JS 