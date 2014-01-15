# CURRENTLY NOT INTENDED TO BE RUN DIRECTLY, BUT CUT AND PASTED INTO A TERMINAL

# Once ssh'ed into the AWS machine...

# Create users
sudo useradd steven -m -s /bin/bash -G users

# Permissions in preparation for using /data as shared space
sudo sed -i.orig "s/umask 022/umask 007/" /etc/profile

# Enable login as steven
sudo mkdir ~steven/.ssh
sudo mv steven_id_rsa.pub ~steven/.ssh/authorized_keys
sudo chown -R steven.steven ~steven/.ssh
sudo chmod -R go-rwx ~steven/.ssh

# To perform administration as steven (requires manual intervention)
#sudo visudo  # add "steven  ALL=(ALL) NOPASSWD:ALL" to /etc/sudoers
# now login as steven

# install packages
sudo apt-get -y update
sudo apt-get -y upgrade
sudo apt-get -y install apparmor-utils cython ddd devscripts emacs23 expect-dev gcc git-all imagemagick ipython libhdf4-alt-dev libhdf5-openmpi-dev libmagick++-dev libmpich2-dev libnetcdf-dev libplplot-dev libwxgtk2.8-dev mysql-client python python-cheetah python-dev python-imaging python-matplotlib python-numpy python-pip python-pyfits python-scipy python-sklearn python-tables r-recommended s3cmd screen sqlite sqlite3 subversion valgrind xemacs21

sudo apt-get -y install mysql-server 
sudo pip install pymysql
sudo pip install fastcluster
# hacky fix:
sudo chmod -R a+rX /usr/local/lib/python2.7/dist-packages

# NX
sudo add-apt-repository ppa:freenx-team
sudo aptitude update
sudo aptitude install -y make openssh-server python python-pexpect \
    python-simplejson python-gtk2 python-gobject gcc autoconf automake \
    python-docutils netcat xauth x11-xserver-utils nxagent-dev
sudo aptitude install -y kubuntu-desktop
sudo ln -s /usr/bin/startkde /usr/bin/startkde4

# NeatX
svn checkout http://neatx.googlecode.com/svn/trunk/ neatx
cd neatx/neatx
sudo sed -i.orig "s/pkglib_/pkglibexec_/" Makefile.am
./autogen.sh
./configure --prefix=/usr/local/neatx
make
sudo make install
sudo ln -s /usr/local/neatx/libexec/neatx /usr/local/neatx/lib/
cd ~
sudo useradd --system -m -d /usr/local/neatx/var/lib/neatx/home -s /usr/local/neatx/lib/neatx/nxserver-login-wrapper nx
sudo install -D -m 600 -o nx /usr/local/neatx/share/neatx/authorized_keys.nomachine ~nx/.ssh/authorized_keys
sudo cp /usr/local/neatx/share/doc/neatx/neatx.conf.example /usr/local/etc/neatx.conf
rm -rf neatx

# Setup git
git config --global user.name "Steven"
git config --global user.email steven@stevenbamford.com

# add swap
sudo mkswap /dev/xvde
sudo swapon /dev/xvde

# data on /mnt from a previous run may be available on an EBS:
$ EC2VOLUME=vol-fa58ab8d
$ ec2-attach-volume $EC2VOLUME -i $EC2INSTANCE -d /dev/xvdh
sudo mkdir /mnt
sudo mount /dev/xvdh /mnt

# If need ISIS:
sudo apt-get -y install libjpeg62 libqt4-svg libfontconfig1 libxrender1 libsm6
cd /mnt
sudo mkdir isis3
sudo chown -R steven:steven /mnt/isis3
cd isis3
rsync -az --delete --partial isisdist.astrogeology.usgs.gov::x86-64_linux_UBUNTU/isis .
rsync -az --delete --partial isisdist.astrogeology.usgs.gov::isis3data/data/base data/
rsync -az --exclude='kernels' --delete --partial isisdist.astrogeology.usgs.gov::isis3data/data/lro data/
rsync -az --delete --partial isisdist.astrogeology.usgs.gov::isis3data/data/lro/kernels/tspk data/lro/kernels/
rsync -az --delete --partial isisdist.astrogeology.usgs.gov::isis3data/data/lro/kernels/pck data/lro/kernels/
echo '
export ISISROOT=/mnt/isis3/isis
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
sudo chown -R mysql:steven /mnt/csv
sudo aa-complain /usr/sbin/mysqld
sudo mysql_install_db --ldata=/mnt/lib/mysql

# copy ec2.cnf to instance and edit if necessary
emacs ec2.cnf
sudo cp ~/ec2.cnf /etc/mysql/conf.d/
sudo restart mysql

sudo mkdir /mnt/moonzoo
sudo chown -R steven:steven /mnt/moonzoo
cd /mnt/moonzoo

# get scripts
git clone git@bitbucket.org:bamford/moon-zoo-scripts.git scripts

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

cat reduce_mz_db.sql | mysql -uroot moonzoo &> reduce_mz_db.sql.out &

ln -s /mnt/csv/mz_results*csv /mnt/moonzoo/

python reduce_mz_db.py &> reduce_mz_db.py.out & # actually done function by function last time

cat read_reduced_mz_tables.sql | mysql -uroot moonzoo &> read_reduced_mz_tables.sql.out

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
wget -i selected_nac_urls
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
cat create_classification_stats.sql | mysql -uroot moonzoo
cat selected_nacs | xargs -I{} python scripts/pix2latlong.py db:moonzoo markings/{}.csv cub/{}.cub {} &> pix2latlong.py.out
cat selected_nacs | xargs -I{} python scripts/slice2latlong.py moonzoo cub/{}.cub {} &> slice2latlong.py.out

mkdir clusters
. ./test_clustering_uw.sh; wait; . ./test_clustering_w.sh

# full clustering!
cat create_user_weights.sql | mysql -uroot moonzoo
( cat selected_nacs | xargs -I{} python scripts/mz_cluster.py clusters/{} markings/{}.csv expert_new.csv\
    1.0 2 10 3 4.0 0.4 0.5 30.655 30.800 20.125 20.255 &> mz_cluster.py.out ) &
