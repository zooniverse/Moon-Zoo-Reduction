drop table if exists craters;
create table `craters` (
  `annotation_id` int(11) primary key,
  `classification_id` int(11) default null,
  `task_id` int(11) default null,
  `answer_id` int(11) default null,
  `nac_name` varchar(255) default null,
  `asset_id` int(11) default null,
  `name` varchar(255) default null,
  `asset_created_at` real default null,
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
  `classification_created_at` real default null,
  `time_spent` int(11) default null,
  `id` int(11) default null,
  `x` real default null,
  `y` real default null,
  `x_diameter` real default null,
  `y_diameter` real default null,
  `angle` real default null,
  `boulderyness` int(11) default null,
  `xtranac` real default null,
  `ytranac` real default null,
  `xnac` real default null,
  `ynac` real default null,
  `x_diameter_nac` real default null,
  `y_diameter_nac` real default null,
  `angle_nac` real default null,
  index (classification_id),
  index (asset_id),
  index (task_id)
);
load data infile '/mnt/moonzoo/mz_craters.csv'
into table craters
fields terminated by ',' optionally enclosed by '"' escaped by '\\'
lines terminated by '\n'
ignore 1 lines;

drop table if exists regions;
create table `regions` (
  `annotation_id` int(11) primary key,
  `classification_id` int(11) default null,
  `task_id` int(11) default null,
  `answer_id` int(11) default null,
  `nac_name` varchar(255) default null,
  `asset_id` int(11) default null,
  `name` varchar(255) default null,
  `asset_created_at` real default null,
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
  `classification_created_at` real default null,
  `time_spent` int(11) default null,
  `id` int(11) default null,
  `x` real default null,
  `y` real default null,
  `width` real default null,
  `height` real default null,
  `selection_type` varchar(255),
  `xtranac` real default null,
  `ytranac` real default null,
  `xnac` real default null,
  `ynac` real default null,
  `width_nac` real default null,
  `height_nac` real default null,
  `angle_nac` real default null, -- this is not actually used for regions
  index (classification_id),
  index (asset_id),
  index (task_id)
);
load data infile '/mnt/moonzoo/mz_regions.csv'
into table regions
fields terminated by ',' optionally enclosed by '"' escaped by '\\'
lines terminated by '\n'
ignore 1 lines;
