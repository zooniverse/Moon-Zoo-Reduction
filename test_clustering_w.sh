cat create_user_weights.sql | mysql -uroot moonzoo

( cat selected_nacs | xargs -I{} python mz_cluster.py clusters/{}_A17_a_2.0_w markings/{}.csv expert_new.csv\
    1.0 2.0 10 3 4.0 0.4 0.5 30.655 30.800 20.125 20.255 &> mz_cluster_A17_a_2.0_w.py.out ) &

( cat selected_nacs | xargs -I{} python mz_cluster.py clusters/{}_A17_a_2.5_w markings/{}.csv expert_new.csv\
    1.0 2.5 10 3 4.0 0.4 0.5 30.655 30.800 20.125 20.255 &> mz_cluster_A17_a_2.5_w.py.out ) &

( cat selected_nacs | xargs -I{} python mz_cluster.py clusters/{}_A17_a_3.0_w markings/{}.csv expert_new.csv\
    1.0 3.0 10 3 4.0 0.4 0.5 30.655 30.800 20.125 20.255 &> mz_cluster_A17_a_3.0_w.py.out )

( cat selected_nacs | xargs -I{} python mz_cluster.py clusters/{}_A17_b_2.0_w markings/{}.csv expert_new.csv\
    1.5 2.0 10 3 4.0 0.4 0.5 30.655 30.800 20.125 20.255 &> mz_cluster_A17_b_2.0_w.py.out ) &

( cat selected_nacs | xargs -I{} python mz_cluster.py clusters/{}_A17_b_2.5_w markings/{}.csv expert_new.csv\
    1.5 2.5 10 3 4.0 0.4 0.5 30.655 30.800 20.125 20.255 &> mz_cluster_A17_b_2.5_w.py.out ) &

( cat selected_nacs | xargs -I{} python mz_cluster.py clusters/{}_A17_b_3.0_w markings/{}.csv expert_new.csv\
    1.5 3.0 10 3 4.0 0.4 0.5 30.655 30.800 20.125 20.255 &> mz_cluster_A17_b_3.0_w.py.out )

( cat selected_nacs | xargs -I{} python mz_cluster.py clusters/{}_A17_c_2.0_w markings/{}.csv expert_new.csv\
    0.75 2.0 10 3 4.0 0.4 0.5 30.655 30.800 20.125 20.255 &> mz_cluster_A17_c_2.0_w.py.out ) &

( cat selected_nacs | xargs -I{} python mz_cluster.py clusters/{}_A17_c_2.5_w markings/{}.csv expert_new.csv\
    0.75 2.5 10 3 4.0 0.4 0.5 30.655 30.800 20.125 20.255 &> mz_cluster_A17_c_2.5_w.py.out ) &

( cat selected_nacs | xargs -I{} python mz_cluster.py clusters/{}_A17_c_3.0_w markings/{}.csv expert_new.csv\
    0.75 3.0 10 3 4.0 0.4 0.5 30.655 30.800 20.125 20.255 &> mz_cluster_A17_c_3.0_w.py.out )
