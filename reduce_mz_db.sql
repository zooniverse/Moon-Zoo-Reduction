drop table if exists x;
create table `x` (
  `annotation_id` int(11) primary key,
  `classification_id` int(11) not null,
  `task_id` int(11) not null,
  `answer_id` int(11) not null,
  `asset_id` int(11) not null,
  `value` text not null,
  `zooniverse_user_id` int(11) not null,
  `classification_created_at` datetime not null,
  `time_spent` int(11) not null,
  index (classification_id),
  index (asset_id),
  index (task_id)
);
insert into x
select a.id as annotation_id, a.classification_id, a.task_id, a.answer_id, b.asset_id, replace(a.value, '\n', '| ') as value,
       c.zooniverse_user_id, c.created_at as classification_created_at, c.time_spent
from annotations as a, asset_classifications as b, classifications as c
where a.classification_id = c.id
and a.classification_id = b.classification_id
and workflow_id = 1;

drop table if exists results;
create table `results` (
  `annotation_id` int(11) primary key,
  `classification_id` int(11) default null,
  `task_id` int(11) default null,
  `answer_id` int(11) default null,
  `nac_name` varchar(255) default null,
  `asset_id` int(11) default null,
  `name` varchar(255) default null,
  `asset_created_at` datetime default null,
  `value` text default null,
  `xmin` int(11) default null,
  `xmax` int(11) default null,
  `ymin` int(11) default null,
  `ymax` int(11) default null,
  `parent_trim_left` int(11) default null,
  `parent_trim_right` int(11) default null,
  `zoom` real default null,
  `resolution` real default null,
  `longitude` real default null,
  `latitude` real default null,
  `transfo` int(11) default null,
  `parent_image_width` int(11) default null,
  `parent_image_height` int(11) default null,
  `zooniverse_user_id` int(11) default null,
  `classification_created_at` datetime default null,
  `time_spent` int(11) default null,
  index (classification_id),
  index (asset_id),
  index (task_id)
);
insert into results
select annotation_id, classification_id, task_id, answer_id, parent_name as nac_name, asset_id, name, assets.created_at as asset_created_at, value, x_min, x_max, y_min, y_max, parent_trim_left, parent_trim_right, zoom, slice_resolution, slice_center_longitude, slice_center_latitude, transfo, parent_image_width, parent_image_height, zooniverse_user_id, classification_created_at, time_spent
from x, assetinfo as assets
where x.asset_id=assets.id;

select * into outfile '/tmp/mz_results_craters.csv'
fields terminated by ',' optionally enclosed by '"' escaped by '\\'
lines terminated by '\n'
from results
where task_id=1 and answer_id=1;

select * into outfile '/tmp/mz_results_regions.csv'
fields terminated by ',' optionally enclosed by '"' escaped by '\\'
lines terminated by '\n'
from results
where task_id=2 and answer_id=3;

-- boulders are more complicated as need to get both asset_ids

drop table if exists asset_counts;
create table `asset_counts`
select asset_id, count(*) as nviews from asset_classifications group by asset_id;

drop table if exists slice_counts;
create table `slice_counts` (
  `asset_id` int(11) default null,
  `nviews` int(11) default null,
  `nac_name` varchar(255) default null,
  `zoom` real default null,
  `x_min` int(11) default null,
  `x_max` int(11) default null,
  `y_min` int(11) default null,
  `y_max` int(11) default null,
  `long_min` real default null,
  `long_max` real default null,
  `lat_min` real default null,
  `lat_max` real default null,
  index (asset_id)
);
insert into slice_counts (asset_id, nviews, nac_name, zoom, x_min, x_max, y_min, y_max)
select asset_id, nviews, parent_name, zoom,
case
    when transfo % 2 = 0 then x_min + parent_trim_left
    else x_min + parent_trim_right
end as x_min,
case
    when transfo % 2 = 0 then x_max + parent_trim_left
    else x_max + parent_trim_right
end as x_max,
case
    when transfo < 2 then y_min
    else parent_image_height - y_min
end as y_min,
case
    when transfo < 2 then y_max
    else parent_image_height - y_max
end as y_max
from asset_counts, assetinfo
where asset_id = id;
