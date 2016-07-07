# CURRENTLY NOT INTENDED TO BE RUN DIRECTLY, BUT CUT AND PASTED INTO A TERMINAL

# Adapted from AWS version for a local Scientific Linux machine

# Install and configure MySQL server if necessary

# Install and configure git if necessary

# install any missing packages
# sudo apt-get -y install apparmor-utils cython ddd devscripts emacs23 expect-dev gcc git-all imagemagick ipython libhdf4-alt-dev libhdf5-openmpi-dev libmagick++-dev libmpich2-dev libnetcdf-dev libplplot-dev libwxgtk2.8-dev mysql-client python python-cheetah python-dev python-imaging python-matplotlib python-numpy python-pip python-pyfits python-scipy python-sklearn python-tables r-recommended s3cmd screen sqlite sqlite3 subversion valgrind xemacs21

sudo pip install pymysql

# If need ISIS:
sudo apt-get -y install libjpeg62 libqt4-svg libfontconfig1 libxrender1 libsm6
cd /data1
sudo mkdir isis3
sudo chown -R ppzsb1:ppzsb1 /data1/isis3
cd isis3
rsync -az --delete --partial isisdist.astrogeology.usgs.gov::x86-64_linux_RHEL6/isis .
rsync -az --delete --partial isisdist.astrogeology.usgs.gov::isis3data/data/base data/
rsync -az --exclude='kernels' --delete --partial isisdist.astrogeology.usgs.gov::isis3data/data/lro data/
rsync -az --delete --partial isisdist.astrogeology.usgs.gov::isis3data/data/lro/kernels/tspk data/lro/kernels/
rsync -az --delete --partial isisdist.astrogeology.usgs.gov::isis3data/data/lro/kernels/pck data/lro/kernels/
echo '
export ISISROOT=/data1/isis3/isis
. $ISISROOT/scripts/isis3Startup.sh
' >> ~/.profile


mkdir ~/quickdata/moonzoo
cd ~/quickdata/moonzoo

# get scripts
git clone https://github.com/zooniverse/Moon-Zoo-Reduction.git scripts

wget http://zooniverse-code.s3.amazonaws.com/databases/161014/moonzoo_production_161014.sql.gz
# Get latest database:
# moonzoo_production_2016-07-05.sql.gz from Adam McMaster via Slack and Dropbox
wget http://moonzoo.s3.amazonaws.com/v10/database/MZP.db
wget -OMZP_A17.db http://moonzoo.s3.amazonaws.com/v21/database/MZP.db
wget -OMZP_A12.db http://moonzoo.s3.amazonaws.com/v23/database/MZP.db
#wget http://moonzoo.s3.amazonaws.com/reduction/sep2013/reduce_mz_db.sql
#wget http://moonzoo.s3.amazonaws.com/reduction/sep2013/reduce_mz_db.py

echo 'create database moonzoo' | mysql -uroot -ppppzsb2
cat moonzoo_production_2016-07-05.sql.gz | gunzip | mysql -uroot -ppppzsb2 moonzoo &

echo '.mode csv 
.header on 
.out mzimages.csv 
select * from mzimages;
.out mzslices.csv 
select * from mzslices;' | sqlite3 MZP.db

echo '.mode csv 
.header off
.out mzimages_a17.csv 
select * from mzimages;
.out mzslices_a17.csv 
select * from mzslices;' | sqlite3 MZP_A17.db

cat mzimages_a17.csv >> mzimages.csv
cat mzslices_a17.csv >> mzslices.csv

echo '.mode csv 
.header off
.out mzimages_a12.csv 
select * from mzimages;
.out mzslices_a12.csv 
select * from mzslices;' | sqlite3 MZP_A12.db

cat mzimages_a12.csv >> mzimages.csv
cat mzslices_a12.csv >> mzslices.csv

mkdir csv

cat scripts/read_mzp_db.sql | mysql -uroot -ppppzsb2 moonzoo &> read_mzp_db.sql.out &

cat scripts/reduce_mz_db_boulders.sql | mysql -uroot -ppppzsb2 moonzoo &> reduce_mz_db_boulders.sql.out &
cp /tmp/mz_results_boulders.csv csv/

cat scripts/reduce_mz_db.sql | mysql -uroot -ppppzsb2 moonzoo &> reduce_mz_db.sql.out &
cp /tmp/mz_results_craters.csv /tmp/mz_results_regions.csv csv/

python scripts/reduce_mz_db_boulders.py &> reduce_mz_db_boulders.py.out &

python scripts/reduce_mz_db.py &> reduce_mz_db.py.out & # actually done function by function last time

cat scripts/read_reduced_mz_tables.sql | mysql -uroot -ppppzsb2 moonzoo &> read_reduced_mz_tables.sql.out

wget -OMZP_v10_1.log.gz http://moonzoo.s3.amazonaws.com/v10/logs/MZP.log_2010-04-14T00:47:34.gz
wget -OMZP_v10_2.log.gz http://moonzoo.s3.amazonaws.com/v10/logs/MZP.log_2010-04-16T00:47:06.gz
wget -OMZP_v10_3.log.gz http://moonzoo.s3.amazonaws.com/v10/logs/MZP.log.gz
wget -OMZP_v21.log.gz http://moonzoo.s3.amazonaws.com/v21/logs/MZP.log.gz
wget -OMZP_v23.log.gz http://moonzoo.s3.amazonaws.com/v23/logs/MZP.log.gz
gunzip MZP*log.gz
cat MZP*log > MZP.log
grep 'Attempting to retrieve URL' MZP.log | colrm 1 62 | sort | uniq > nac_urls

cp nac_urls selected_nac_urls

# edit selected_nac_urls to only select those nacs interested in

mkdir img
cd img
wget -i ../selected_nac_urls_a17
wget -i ../selected_nac_urls_a12
cd ..

ls img | colrm 13 > selected_nacs

mkdir tmp
cat selected_nacs | xargs -I{} lronac2isis from=img/{}.IMG to=tmp/{}.cub
mkdir cub
cat selected_nacs | xargs -I{} lronaccal from=tmp/{}.cub to=cub/{}.cub
rm -rf tmp
cat selected_nacs | xargs -I{} spiceinit web=yes from=cub/{}.cub
mkdir fits
cat selected_nacs | xargs -I{} isis2fits from=cub/{}.cub to=fits/{}.fits

mkdir markings
cat create_classification_stats.sql | mysql -uroot -ppppzsb2 moonzoo
cat selected_nacs | xargs -I{} python /home/ppzsb1/projects/zooniverse/Moon-Zoo-Reduction/pix2latlong.py db:moonzoo markings/{}.csv cub/{}.cub {} &> pix2latlong.py.out

cat selected_nacs | xargs -I{} python /home/ppzsb1/projects/zooniverse/Moon-Zoo-Reduction/slice2latlong.py moonzoo cub/{}.cub {} &> slice2latlong.py.out

# Clustering not done...

mkdir clusters
. ./test_clustering_uw.sh; wait; . ./test_clustering_w.sh

# full clustering!
cat create_user_weights.sql | mysql -uroot moonzoo
( cat selected_nacs | xargs -I{} python /home/ppzsb1/projects/zooniverse/Moon-Zoo-Reduction/mz_cluster.py clusters/{} markings/{}.csv expert_new.csv\
    1.0 2 10 3 4.0 0.4 0.5 30.655 30.800 20.125 20.255 &> mz_cluster.py.out ) &
