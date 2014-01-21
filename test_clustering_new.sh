python scripts/mz_cluster.py -f clusters/715_a_2_uw markings/M104311715RE.csv M104311715RE New_CC/truth.csv New_CC/ROI_715.png 1.0 2 10 3 4.0 0.4 100 30.699 30.880 20.200 20.275 &> 715_a_2_uw.out &
python scripts/mz_cluster.py -f clusters/715_b_2_uw markings/M104311715RE.csv M104311715RE New_CC/truth.csv New_CC/ROI_715.png 1.5 2 10 3 4.0 0.4 100 30.699 30.880 20.200 20.275 &> 715_b_2_uw.out &
python scripts/mz_cluster.py -f clusters/715_c_2_uw markings/M104311715RE.csv M104311715RE New_CC/truth.csv New_CC/ROI_715.png 0.75 2 10 3 4.0 0.4 100 30.699 30.880 20.200 20.275 &> 715_c_2_uw.out &

cd markings
head -1 M104311715RE.csv > ALL_A17.csv
cat *.csv | grep -v long >> ALL_A17.csv
cd ..

python scripts/mz_cluster.py -f clusters/all_a17_a_2_uw markings/ALL_A17.csv M104311715RE,M101949648RE,M104318871RE,M180966380LE New_CC/truth.csv New_CC/ROI_715.png 1.0 2 40 3 4.0 0.4 100 30.699 30.880 20.200 20.275 &> all_a17_a_2_uw.out &
python scripts/mz_cluster.py -f clusters/all_a17_b_2_uw markings/ALL_A17.csv M104311715RE,M101949648RE,M104318871RE,M180966380LE New_CC/truth.csv New_CC/ROI_715.png 1.5 2 40 3 4.0 0.4 100 30.699 30.880 20.200 20.275 &> all_a17_b_2_uw.out &
python scripts/mz_cluster.py -f clusters/all_a17_c_2_uw markings/ALL_A17.csv M104311715RE,M101949648RE,M104318871RE,M180966380LE New_CC/truth.csv New_CC/ROI_715.png 0.75 2 40 3 4.0 0.4 100 30.699 30.880 20.200 20.275 &> all_a17_c_2_uw.out &
