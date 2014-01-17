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

-- mzimages and mzslices tables from MZP.db SQLite3 database dumped to
-- a csv file, then read into the MySQL as follows:

drop table if exists mzimages;
create table `mzimages` (
volume_id varchar(255),
file_specification_name varchar(255),
instrument_host_id varchar(255),
instrument_id varchar(255),
original_product_id varchar(255),
product_id varchar(255),
product_version_id varchar(255),
target_name varchar(255),
orbit_number real,
slew_angle real,
mission_phase_name varchar(255),
rationale_desc varchar(255),
data_quality_id real,
nac_preroll_start_time datetime,
start_time datetime,
stop_time datetime,
spacecraft_clock_partition real,
nac_spacecraft_clock_preroll_count varchar(255),
spacecraft_clock_start_count varchar(255),
spacecraft_clock_stop_count varchar(255),
start_sclk_seconds real,
start_sclk_ticks real,
stop_sclk_seconds real,
stop_sclk_ticks real,
nac_line_exposure_duration real,
wac_exposure_duration real,
nac_frame_id varchar(255),
nac_dac_reset real,
nac_channel_a_offset real,
nac_channel_b_offset real,
instrument_mode_code real,
wac_instrument_mode_id varchar(255),
wac_band_code real,
wac_background_offset real,
wac_filter_name varchar(255),
wac_number_of_frames real,
wac_interframe_time real,
wac_interframe_code real,
wac_mode_polar real,
compand_select_code real,
mode_compression real,
mode_test real,
nac_temperature_scs real,
nac_temperature_fpa real,
nac_temperature_fpga real,
nac_temperature_telescope real,
wac_begin_temperature_scs real,
wac_middle_temperature_scs real,
wac_end_temperature_scs real,
wac_begin_temperature_fpa real,
wac_middle_temperature_fpa real,
wac_end_temperature_fpa real,
image_lines real,
line_samples real,
sample_bits real,
scaled_pixel_width real,
scaled_pixel_height real,
resolution real,
emmission_angle real,
incidence_angle real,
phase_angle real,
north_azimuth real,
sub_solar_azimuth real,
sub_solar_latitude real,
sub_solar_longitude real,
sub_spacecraft_latitude real,
sub_spacecraft_longitude real,
solar_distance real,
solar_longitude real,
center_latitude real,
center_longitude real,
upper_right_latitude real,
upper_right_longitude real,
lower_right_latitude real,
lower_right_longitude real,
lower_left_latitude real,
lower_left_longitude real,
upper_left_latitude real,
upper_left_longitude real,
spacecraft_altitude real,
target_center_distance real,
sliced_boulders integer default 0,
sliced_craters integer default 0,
description text
);
load data infile '/mnt/moonzoo/mzimages.csv'
into table mzimages
fields terminated by ',' optionally enclosed by '"' escaped by '\\'
lines terminated by '\n'
ignore 1 lines;

drop table if exists mzslices;
create table `mzslices` (
parentid int(11),
parent_name varchar(255),
slice_name varchar(255) unique,
criterion varchar(255) not null,
xmin int(11) not null,
xmax int(11) not null,
ymin int(11) not null,
ymax int(11) not null,
parent_trim_left int(11) not null,
parent_trim_right int(11) not null,
zoom real not null,
parent_resolution real not null,
slice_resolution real not null,
slice_center_longitude real not null,
slice_center_latitude real not null,
emmission_angle real not null,
incidence_angle real not null,
sub_solar_azimuth real not null,
north_azimuth real not null,
sun_angle real not null,
nxpix int(11) not null,
nypix int(11) not null,
nxpix_orig int(11) not null,
nypix_orig int(11) not null,
transfo int(11) not null,
created_at datetime not null,
location varchar(255) default null,
thumb_location varchar(255) default null
);
load data infile '/mnt/moonzoo/mzslices.csv'
into table mzslices
fields terminated by ',' optionally enclosed by '"' escaped by '\\'
lines terminated by '\n'
ignore 1 lines;

create unique index name on assets (name);

drop table if exists assetinfo;
create table `assetinfo` (
  `id` int(11) NOT NULL,
  `name` varchar(255) DEFAULT NULL,
  `project_id` int(11) DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  `location` varchar(255) DEFAULT NULL,
  `classification_count` int(11) DEFAULT '0',
  `external_ref` text,
  `average_score` float DEFAULT NULL,
  `active` tinyint(1) DEFAULT NULL,
  `longitude` float DEFAULT NULL,
  `latitude` float DEFAULT NULL,
  `sun_angle` float DEFAULT NULL,
  `pixel_scale` float DEFAULT NULL,
  `width` int(11) DEFAULT NULL,
  `height` int(11) DEFAULT NULL,
  `workflow_id` int(11) DEFAULT NULL,
  `thumbnail_location` varchar(255) DEFAULT NULL,
  `zooniverse_id` varchar(255) DEFAULT NULL,
  `zoom_level` int(11) DEFAULT NULL,
  `x_min` int(11) DEFAULT NULL,
  `x_max` int(11) DEFAULT NULL,
  `y_min` int(11) DEFAULT NULL,
  `y_max` int(11) DEFAULT NULL,
  `parent_image_location` varchar(255) DEFAULT NULL,
  `parent_image_width` int(11) DEFAULT NULL,
  `parent_image_height` int(11) DEFAULT NULL,
  `parent_name` varchar(255) DEFAULT NULL,
  `parent_trim_left` int(11) DEFAULT NULL,
  `parent_trim_right` int(11) DEFAULT NULL,
  `zoom` double DEFAULT NULL,
  `slice_resolution` double DEFAULT NULL,
  `slice_center_longitude` double DEFAULT NULL,
  `slice_center_latitude` double DEFAULT NULL,
  `transfo` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`)
);
insert into assetinfo
select assets.*,
       parent_name, parent_trim_left, parent_trim_right, zoom, slice_resolution, slice_center_longitude, slice_center_latitude, transfo
from assets
left join mzslices
on assets.name = mzslices.slice_name;

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

select * into outfile '/mnt/csv/mz_results_craters.csv'
fields terminated by ',' optionally enclosed by '"' escaped by '\\'
lines terminated by '\n'
from results
where task_id=1 and answer_id=1;

select * into outfile '/mnt/csv/mz_results_regions.csv'
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
