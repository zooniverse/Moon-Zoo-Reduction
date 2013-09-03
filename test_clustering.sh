cat equal_user_weights.sql | mysql -uroot moonzoo

cat selected_nacs | xargs -I{} python mz_cluster.py clusters/{}_A17_2_uw clusters/{}.csv markings/{}.csv \
    1.0 2 10 3 4.0 0.4 0.05 30.655 30.800 20.125 20.255 &> mz_cluster_A17_2_uw.py.out

cat selected_nacs | xargs -I{} python mz_cluster.py clusters/{}_A17_3_uw clusters/{}.csv markings/{}.csv \
    1.0 3 10 3 4.0 0.4 0.05 30.655 30.800 20.125 20.255 &> mz_cluster_A17_3_uw.py.out

cat create_user_weights.sql | mysql -uroot moonzoo

cat selected_nacs | xargs -I{} python mz_cluster.py clusters/{}_A17_2_w clusters/{}.csv markings/{}.csv \
    1.0 2 10 3 4.0 0.4 0.05 30.655 30.800 20.125 20.255 &> mz_cluster_A17_2_w.py.out

cat selected_nacs | xargs -I{} python mz_cluster.py clusters/{}_A17_4_w clusters/{}.csv markings/{}.csv \
    1.0 4 10 3 4.0 0.4 0.05 30.655 30.800 20.125 20.255 &> mz_cluster_A17_4_w.py.out

cat selected_nacs | xargs -I{} python mz_cluster.py clusters/{}_A17_8_w clusters/{}.csv markings/{}.csv \
    1.0 8 10 3 4.0 0.4 0.05 30.655 30.800 20.125 20.255 &> mz_cluster_A17_8_w.py.out
