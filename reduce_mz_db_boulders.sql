drop table if exists xb;
create table `xb` (
  `classification_id` int(11) primary key,
  `first_asset_id` int(11) not null,
  `second_asset_id` int(11) not null,
  `winner_asset_id` text not null,
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
  `winner` int(11) default null,
  `first_name` varchar(255) default null,
  `first_zoom` real default null,
  `first_resolution` real default null,
  `first_longitude` real default null,
  `first_latitude` real default null,
  `first_emission_angle` real default null,
  `first_incidence_angle` real default null,
  `first_sub_solar_azimuth` real default null,
  `first_north_azimuth` real default null,
  `first_sun_angle` real default null,
  `first_transfo` int(11) default null,
  `second_name` varchar(255) default null,
  `second_zoom` real default null,
  `second_resolution` real default null,
  `second_longitude` real default null,
  `second_latitude` real default null,
  `second_emission_angle` real default null,
  `second_incidence_angle` real default null,
  `second_sub_solar_azimuth` real default null,
  `second_north_azimuth` real default null,
  `second_sun_angle` real default null,
  `second_transfo` int(11) default null,
  `zooniverse_user_id` int(11) default null,
  index (first_asset_id),
  index (second_asset_id)
);
insert into boulder_results
select classification_id, first_asset_id, second_asset_id, (case winner_asset_id when cast(first_asset_id as char) then 1 when cast(second_asset_id as char) then 2 else 0 end), first_assets.name, first_assets.zoom, first_assets.slice_resolution, first_assets.slice_center_longitude, first_assets.slice_center_latitude, first_assets.emission_angle, first_assets.incidence_angle, first_assets.sub_solar_azimuth, first_assets.north_azimuth, first_assets.sun_angle, first_assets.transfo, second_assets.name, second_assets.zoom, second_assets.slice_resolution, second_assets.slice_center_longitude, second_assets.slice_center_latitude, second_assets.emission_angle, second_assets.incidence_angle, second_assets.sub_solar_azimuth, second_assets.north_azimuth, second_assets.sun_angle, second_assets.transfo, zooniverse_user_id
from xb, assetinfo as first_assets, assetinfo as second_assets
where xb.first_asset_id=first_assets.id
and xb.second_asset_id=second_assets.id;


select GROUP_CONCAT(column_name)
into outfile '/tmp/mz_results_boulders.csvheader'
from information_schema.columns
where table_name = 'boulder_results'
and table_schema = 'moonzoo'
order by ordinal_position;

select * into outfile '/tmp/mz_results_boulders.csv'
fields terminated by ',' optionally enclosed by '"' escaped by '\\'
lines terminated by '\n'
from boulder_results;

select GROUP_CONCAT(column_name)
into outfile '/tmp/mz_images_boulders.csvheader'
from information_schema.columns
where table_name = 'assetinfo'
and table_schema = 'moonzoo'
order by ordinal_position;

select * into outfile '/tmp/mz_images_boulders.csv'
fields terminated by ',' optionally enclosed by '"' escaped by '\\'
lines terminated by '\n'
from assetinfo
where criterion = 'boulders';
