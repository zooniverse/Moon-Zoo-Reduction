cat create_user_weights.sql | mysql -uroot moonzoo

( cat selected_nacs | xargs -I{} python mz_cluster.py clusters/{}_A17_a_2_w markings/{}.csv expert_new.csv\
    1.0 2 10 3 4.0 0.4 0.5 30.655 30.800 20.125 20.255 &> mz_cluster_A17_a_2_w.py.out ) &

( cat selected_nacs | xargs -I{} python mz_cluster.py clusters/{}_A17_a_4_w markings/{}.csv expert_new.csv\
    1.0 4 10 3 4.0 0.4 0.5 30.655 30.800 20.125 20.255 &> mz_cluster_A17_a_4_w.py.out ) &

( cat selected_nacs | xargs -I{} python mz_cluster.py clusters/{}_A17_a_8_w markings/{}.csv expert_new.csv\
    1.0 8 10 3 4.0 0.4 0.5 30.655 30.800 20.125 20.255 &> mz_cluster_A17_a_8_w.py.out ) &

( cat selected_nacs | xargs -I{} python mz_cluster.py clusters/{}_A17_b_2_w markings/{}.csv expert_new.csv\
    1.5 2 10 3 4.0 0.4 0.5 30.655 30.800 20.125 20.255 &> mz_cluster_A17_b_2_w.py.out ) &

( cat selected_nacs | xargs -I{} python mz_cluster.py clusters/{}_A17_b_4_w markings/{}.csv expert_new.csv\
    1.5 4 10 3 4.0 0.4 0.5 30.655 30.800 20.125 20.255 &> mz_cluster_A17_b_4_w.py.out ) &

( cat selected_nacs | xargs -I{} python mz_cluster.py clusters/{}_A17_b_8_w markings/{}.csv expert_new.csv\
    1.5 8 10 3 4.0 0.4 0.5 30.655 30.800 20.125 20.255 &> mz_cluster_A17_b_8_w.py.out ) &

( cat selected_nacs | xargs -I{} python mz_cluster.py clusters/{}_A17_c_2_w markings/{}.csv expert_new.csv\
    0.75 2 10 3 4.0 0.4 0.5 30.655 30.800 20.125 20.255 &> mz_cluster_A17_c_2_w.py.out ) &

( cat selected_nacs | xargs -I{} python mz_cluster.py clusters/{}_A17_c_4_w markings/{}.csv expert_new.csv\
    0.75 4 10 3 4.0 0.4 0.5 30.655 30.800 20.125 20.255 &> mz_cluster_A17_c_4_w.py.out ) &

( cat selected_nacs | xargs -I{} python mz_cluster.py clusters/{}_A17_c_8_w markings/{}.csv expert_new.csv\
    0.75 8 10 3 4.0 0.4 0.5 30.655 30.800 20.125 20.255 &> mz_cluster_A17_c_8_w.py.out ) &
