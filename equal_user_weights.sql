DROP TABLE IF EXISTS user_stats;
CREATE TABLE user_stats
SELECT zooniverse_user_id, count(*) as count, sum((abs(x_diameter - 20.0) + abs(y_diameter - 20.0)) < 1.0e-5) as count_minsize
FROM craters
GROUP BY zooniverse_user_id;

DROP TABLE IF EXISTS user_weights;
CREATE TABLE user_weights
SELECT *, 1.0 as weight
FROM user_stats;
