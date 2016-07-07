drop table if exists xb;
create table `xb` (
  `classification_id` int(11) primary key,
  `first_asset_id` int(11) not null,
  `second_asset_id` int(11) not null,
  `winner` text not null,
  `zooniverse_user_id` int(11) not null,
  `classification_created_at` datetime not null,
  `time_spent` int(11) not null,
  index (first_asset_id),
  index (second_asset_id)
);
insert into xb
select a.classification_id, b1.asset_id, b2.asset_id, a.value,
       c.zooniverse_user_id, c.created_at as classification_created_at, c.time_spent
from annotations as a, asset_classifications as b1, asset_classifications as b2, classifications as c
where a.classification_id = c.id
and a.classification_id = b1.classification_id
and a.classification_id = b2.classification_id
and b1.id < b2.id
and workflow_id = 2 and task_id = 3;


drop table if exists boulder_results;
create table `boulder_results` (
  `classification_id` int(11) primary key,
  `first_asset_id` int(11) default null,
  `second_asset_id` int(11) default null,
  `winner` text default null,
  `first_nac_name` varchar(255) default null,
  `first_name` varchar(255) default null,
  `first_asset_created_at` datetime default null,
  `first_xmin` int(11) default null,
  `first_xmax` int(11) default null,
  `first_ymin` int(11) default null,
  `first_ymax` int(11) default null,
  `first_parent_trim_left` int(11) default null,
  `first_parent_trim_right` int(11) default null,
  `first_zoom` real default null,
  `first_resolution` real default null,
  `first_longitude` real default null,
  `first_latitude` real default null,
  `first_transfo` int(11) default null,
  `first_parent_image_width` int(11) default null,
  `first_parent_image_height` int(11) default null,
  `second_nac_name` varchar(255) default null,
  `second_name` varchar(255) default null,
  `second_asset_created_at` datetime default null,
  `second_xmin` int(11) default null,
  `second_xmax` int(11) default null,
  `second_ymin` int(11) default null,
  `second_ymax` int(11) default null,
  `second_parent_trim_left` int(11) default null,
  `second_parent_trim_right` int(11) default null,
  `second_zoom` real default null,
  `second_resolution` real default null,
  `second_longitude` real default null,
  `second_latitude` real default null,
  `second_transfo` int(11) default null,
  `second_parent_image_width` int(11) default null,
  `second_parent_image_height` int(11) default null,
  `zooniverse_user_id` int(11) default null,
  `classification_created_at` datetime default null,
  `time_spent` int(11) default null,
  index (first_asset_id),
  index (second_asset_id)
);
insert into boulder_results
select annotation_id, classification_id, first_assets.asset_id, second_assets.asset_id, winner, first_assets.parent_name, first_assets.name, first_assets.created_at, first_assets.x_min, first_assets.x_max, first_assets.y_min, first_assets.y_max, first_assets.parent_trim_left, first_assets.parent_trim_right, first_assets.zoom, first_assets.slice_resolution, first_assets.slice_center_longitude, first_assets.slice_center_latitude, first_assets.transfo, first_assets.parent_image_width, first_assets.parent_image_height, second_assets.parent_name, second_assets.name, second_assets.created_at, second_assets.x_min, second_assets.x_max, second_assets.y_min, second_assets.y_max, second_assets.parent_trim_left, second_assets.parent_trim_right, second_assets.zoom, second_assets.slice_resolution, second_assets.slice_center_longitude, second_assets.slice_center_latitude, second_assets.transfo, second_assets.parent_image_width, second_assets.parent_image_height, zooniverse_user_id, classification_created_at, time_spent
from xb, assetinfo as first_assets, assetinfo as second_assets
where xb.first_asset_id=first_assets.id
and xb.second_asset_id=second_assets.id;

select * into outfile '/home/ppzsb1/quickdata/moonzoo/csv/mz_results_boulders.csv'
fields terminated by ',' optionally enclosed by '"' escaped by '\\'
lines terminated by '\n'
from boulder_results;
