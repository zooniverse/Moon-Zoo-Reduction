-- Stats on 2010-10-15

use moonzoo_production;

-- number of images
select count(*) from classifications;
-- 3185858

-- number of craters / interesting features
select count(*) from annotations;
-- 10834359

-- number of users who have logged into Moon Zoo
select count(*) from zooniverse_users;
-- 94646

-- number of users who have submitted a classification
select count(*) from (select distinct zooniverse_user_id from classifications) as X;
-- 47744

-- => average images per user = 3185858/47744 = 67

-- number of images which have classifications
select count(*) from assets;
select count(*) from (select distinct asset_id from asset_classifications) as X;

-- 395109
-- 394866

-- area covered (from Moonometer)
-- 73810 sq. miles = 191167 sq. km
-- at 0.5 m/pixel resolution
-- i.e. 0.25 sq. m/pixel
-- => 765 billion pixels viewed
