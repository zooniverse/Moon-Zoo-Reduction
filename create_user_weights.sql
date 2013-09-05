DROP TABLE IF EXISTS user_stats;
CREATE TABLE user_stats
SELECT zooniverse_user_id, count(*) as count, sum((abs(x_diameter - 20.0) + abs(y_diameter - 20.0)) < 1.0e-5) as count_minsize
FROM craters
GROUP BY zooniverse_user_id;

DROP TABLE IF EXISTS user_weights;
CREATE TABLE user_weights
-- SELECT *, ((1.0 + 0.25*arcsinh(count / 100.0)) * (1.0 - count_minsize / count)) as weight
SELECT *, ((1.0 + 0.25*LOG((count / 100.0) + SQRT(POW(count / 100.0, 2)+1))) * SQRT(1.0 - count_minsize / count)) as weight
FROM user_stats;

