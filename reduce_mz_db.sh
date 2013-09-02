# CURRENTLY NOT INTENDED TO BE RUN DIRECTLY, BUT CUT AND PASTED INTO A TERMINAL

# Once ssh'ed into the AWS machine...

# install packages
sudo apt-get -y update
sudo apt-get -y upgrade
sudo apt-get -y install python git sqlite python-imaging python-numpy python-scipy python-cheetah emacs23-nox sqlite3 python-pyfits mysql-client s3cmd apparmor-utils
sudo apt-get -y install mysql-server

# If need ISIS:
sudo apt-get -y install libjpeg62 libqt4-svg libfontconfig1 libxrender1 libsm6
cd /mnt
mkdir isis3
cd isis3
rsync -az --delete --partial isisdist.astrogeology.usgs.gov::x86-64_linux_UBUNTU/isis .
rsync -az --delete --partial isisdist.astrogeology.usgs.gov::isis3data/data/base data/
rsync -az --exclude='kernels' --delete --partial isisdist.astrogeology.usgs.gov::isis3data/data/lro data/
rsync -az --delete --partial isisdist.astrogeology.usgs.gov::isis3data/data/lro/kernels/tspk data/lro/kernels/
rsync -az --delete --partial isisdist.astrogeology.usgs.gov::isis3data/data/lro/kernels/pck data/lro/kernels/
echo '
export ISISROOT=/work1/isis3/isis
. $ISISROOT/scripts/isis3Startup.sh
' >> ~/.profile

# Setup MySQL on mnt (where there is lots of space)
sudo mkdir /mnt/lib
sudo mkdir /mnt/lib/mysql
sudo mkdir /mnt/log
sudo mkdir /mnt/log/mysql
sudo mkdir /mnt/csv
sudo chown -R mysql:mysql /mnt/log/mysql
sudo chown -R mysql:mysql /mnt/lib/mysql
sudo chown -R mysql:ubuntu /mnt/csv
sudo aa-complain /usr/sbin/mysqld
sudo mysql_install_db --ldata=/mnt/lib/mysql

# copy ec2.cnf to instance and edit if necessary
emacs ec2.cnf
sudo cp ~/ec2.cnf /etc/mysql/conf.d/
sudo restart mysql

sudo mkdir /mnt/moonzoo
sudo chown -R ubuntu:ubuntu /mnt/moonzoo
cd /mnt/moonzoo

wget http://zooniverse-code.s3.amazonaws.com/databases/010913/moonzoo_production_010913.sql.gz
wget http://moonzoo.s3.amazonaws.com/v10/database/MZP.db
wget -OMZP_A17.db http://moonzoo.s3.amazonaws.com/v21/database/MZP.db
wget -OMZP_A12.db http://moonzoo.s3.amazonaws.com/v23/database/MZP.db
wget http://moonzoo.s3.amazonaws.com/reduction/sep2013/reduce_mz_db.sql
wget http://moonzoo.s3.amazonaws.com/reduction/sep2013/reduce_mz_db.py

echo 'create database moonzoo' | mysql -u root
cat moonzoo_production_010913.sql.gz | gunzip | mysql -u root moonzoo &

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

cat reduce_mz_db.sql | mysql -uroot moonzoo &> reduce_mz_db.sql.out

python reduce_mz_db.py &> reduce_mz_db.py.out  # actually done function by function last time

cat read_reduced_mz_tables.sql | mysql -uroot moonzoo &> read_reduced_mz_tables.sql.out

wget -OMZP_v10.log.gz http://moonzoo.s3.amazonaws.com/v10/logs/MZP.log.gz
wget -OMZP_v21.log.gz http://moonzoo.s3.amazonaws.com/v21/logs/MZP.log.gz
wget -OMZP_v23.log.gz http://moonzoo.s3.amazonaws.com/v23/logs/MZP.log.gz
gunzip MZP*log.gz
cat MZP*log > MZP.log
grep 'Attempting to retrieve URL' MZP.log | head | colrm 1 62 | sort | uniq > nac_urls

cp nac_urls selected_nac_urls

# edit selected_nac_urls to only select those nacs interested in

mkdir img
wget -i selected_nac_urls

ls img | colrm 13 > selected_nacs

mkdir tmp
cat selected_nacs | xargs -I{} lronac2isis from=img/{}.IMG to=tmp/{}.cub
mkdir cub
cat selected_nacs | xargs -I{} lronaccal from=tmp/{}.cub to=cub/{}.cub
rm -rf tmp
cat selected_nacs | xargs -I{} spiceinit from=cub/{}.cub
mkdir fits
cat selected_nacs | xargs -I{} isis2fits from=cub/{}.cub to=fits/{}.fits

mkdir markings
cat selected_nacs | xargs -I{} python pix2latlong.py db:moonzoo markings/{}.csv cub/{}.cub {}

mkdir clusters
cat selected_nacs | xargs -I{} python mz_cluster.py clusters/{}.csv markings/{}.csv
