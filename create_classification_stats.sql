DROP TABLE IF EXISTS classification_stats;
CREATE TABLE classification_stats
SELECT classification_id, count(*) as count
FROM craters
GROUP BY classification_id;