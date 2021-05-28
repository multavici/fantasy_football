WITH 
fantasy_players AS
  (
    SELECT fantasy_player.player_id AS id
    FROM fantasy_player 
    WHERE fantasy_player.team_id = :team_id
  ),
grid AS
  (
    SELECT fantasy_players.id AS id, matchday.id AS matchday 
    FROM fantasy_players 
    CROSS JOIN matchday
    WHERE matchday.finished = 1
  ),
field_goals AS
  (
    SELECT goal.scorer_id, "match".matchday_id, count(*) as field_goals
    FROM goal
    JOIN fantasy_players
      ON goal.scorer_id = fantasy_players.id
    JOIN event
      ON goal.id = event.id
    JOIN "match"
      ON event.match_id = "match".id
    WHERE goal_type = "field_goal"
    GROUP BY goal.scorer_id, "match".matchday_id
  ),
penalties_scored AS
  (
    SELECT goal.scorer_id, "match".matchday_id, count(*) as penalties_scored
    FROM goal
    JOIN fantasy_players
      ON goal.scorer_id = fantasy_players.id
    JOIN event
      ON goal.id = event.id
    JOIN "match"
      ON event.match_id = "match".id
    WHERE goal_type = "penalty_scored"
    GROUP BY goal.scorer_id, "match".matchday_id
  ),
own_goals AS
  (
    SELECT goal.scorer_id, "match".matchday_id, count(*) as own_goals
    FROM goal
    JOIN fantasy_players
      ON goal.scorer_id = fantasy_players.id
    JOIN event
      ON goal.id = event.id
    JOIN "match"
      ON event.match_id = "match".id
    WHERE goal_type = "own_goal"
    GROUP BY goal.scorer_id, "match".matchday_id
  ),
penalty_missed AS
  (
    SELECT goal.scorer_id, "match".matchday_id, count(*) as own_goals
    FROM goal
    JOIN fantasy_players
      ON goal.scorer_id = fantasy_players.id
    JOIN event
      ON goal.id = event.id
    JOIN "match"
      ON event.match_id = "match".id
    WHERE goal_type = "own_goal"
    GROUP BY goal.scorer_id, "match".matchday_id
  ),
yellow_cards AS
  (
    SELECT card.player_id, "match".matchday_id, count(*) as yellow_cards
    FROM card
    JOIN fantasy_players
      ON card.player_id = fantasy_players.id
    JOIN event
      ON card.id = event.id
    JOIN "match"
      ON event.match_id = "match".id
    WHERE card_type = "yellow"
    GROUP BY card.player_id, "match".matchday_id
  ),
red_cards AS
  (
    SELECT card.player_id, "match".matchday_id, count(*) as red_cards
    FROM card
    JOIN fantasy_players
      ON card.player_id = fantasy_players.id
    JOIN event
      ON card.id = event.id
    JOIN "match"
      ON event.match_id = "match".id
    WHERE card_type = "red"
    GROUP BY card.player_id, "match".matchday_id
  ),
starting AS
  (
    SELECT fantasy_players.id, "match".matchday_id, squad_appearance.starting 
    FROM fantasy_players
    JOIN squad_appearance
      ON fantasy_players.id = squad_appearance.player_id
    JOIN "match"
      ON squad_appearance.match_id = "match".id
  ),
subbed_in AS
  (
    SELECT fantasy_players.id, "match".matchday_id, event.minute AS subbed_in_minute
    FROM substitution
    JOIN fantasy_players
      ON substitution.player_in_id = fantasy_players.id
    JOIN event
      ON substitution.id = event.id
    JOIN "match"
      ON event.match_id = "match".id
  ),
subbed_out AS
  (
    SELECT fantasy_players.id, "match".matchday_id, event.minute AS subbed_out_minute
    FROM substitution
    JOIN fantasy_players
      ON substitution.player_out_id = fantasy_players.id
    JOIN event
      ON substitution.id = event.id
    JOIN "match"
      ON event.match_id = "match".id
  ),
minutes_played AS
  (
    SELECT grid.id AS player_id, grid.matchday AS matchday_id,
      CASE 
      WHEN starting = 1 THEN 
        CASE 
        WHEN subbed_out_minute IS NULL THEN 90 
        ELSE subbed_out_minute 
        END 
      WHEN starting = 0 THEN 
        CASE 
        WHEN subbed_in_minute IS NULL THEN 0 
        ELSE 
          CASE WHEN subbed_in_minute < 90 THEN 90 - subbed_in_minute 
          ELSE 5 
          END 
        END
      ELSE 0 
      END minutes_played
    FROM grid
    LEFT JOIN starting
      ON grid.id = starting.id AND grid.matchday = starting.matchday_id
    LEFT JOIN subbed_in
      ON grid.id = subbed_in.id AND grid.matchday = subbed_in.matchday_id
    LEFT JOIN subbed_out
      ON grid.id = subbed_out.id AND grid.matchday = subbed_out.matchday_id
  ),
game_result AS
  (
    SELECT squad_appearance.player_id, "match".matchday_id,
      CASE 
      WHEN "match".home_score = "match".away_score THEN "draw"
      WHEN "match".home_score < "match".away_score THEN 
        CASE 
        WHEN squad_appearance.team_id = "match".home_team_id THEN "loss"
        ELSE "win"
        END
      ELSE 
        CASE 
        WHEN squad_appearance.team_id = "match".home_team_id THEN "win"
        ELSE "loss"
        END
      END result
    FROM squad_appearance
    JOIN "match"
      ON squad_appearance.match_id = "match".id
  ),
game_events AS
  (
    SELECT 
      id, 
      matchday, 
      ifnull(field_goals, 0) as field_goals, 
      ifnull(penalties_scored, 0) as penalties_scored,
      ifnull(own_goals, 0) as own_goals,
      ifnull(yellow_cards, 0) as yellow_cards,
      ifnull(red_cards, 0) as red_cards,
      ifnull(minutes_played, 0) as minutes_played,
      result
    FROM grid
    LEFT JOIN field_goals
      ON grid.id = field_goals.scorer_id AND grid.matchday = field_goals.matchday_id
    LEFT JOIN penalties_scored
      ON grid.id = penalties_scored.scorer_id AND grid.matchday = penalties_scored.matchday_id
    LEFT JOIN own_goals
      ON grid.id = own_goals.scorer_id AND grid.matchday = own_goals.matchday_id
    LEFT JOIN yellow_cards
      ON grid.id = yellow_cards.player_id AND grid.matchday = yellow_cards.matchday_id
    LEFT JOIN red_cards
      ON grid.id = red_cards.player_id AND grid.matchday = red_cards.matchday_id
    LEFT JOIN minutes_played
      ON grid.id = minutes_played.player_id AND grid.matchday = minutes_played.matchday_id
    LEFT JOIN game_result
      ON grid.id = game_result.player_id AND grid.matchday = game_result.matchday_id
  )
SELECT
id,
matchday,
field_goals * 5 + penalties_scored * 3 - own_goals * 3 - yellow_cards * 1 - red_cards * 3 +
CASE 
WHEN minutes_played > 0 THEN
  CASE
  WHEN result = 'win' THEN 3
  WHEN result = 'draw' THEN 1
  END
END + 
CASE WHEN minutes_played > 60 THEN 1 END
AS points
FROM game_events