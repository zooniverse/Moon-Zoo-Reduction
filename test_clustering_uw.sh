( cat selected_nacs | xargs -I{} python mz_cluster.py clusters/{}_A17_a_2_uw markings/{}.csv expert_new.csv\
    1.0 2 10 3 4.0 0.4 100 30.655 30.800 20.125 20.255 &> mz_cluster_A17_a_2_uw.py.out ) &

( cat selected_nacs | xargs -I{} python mz_cluster.py clusters/{}_A17_a_3_uw markings/{}.csv expert_new.csv\
    1.0 3 10 3 4.0 0.4 100 30.655 30.800 20.125 20.255 &> mz_cluster_A17_a_3_uw.py.out ) &

( cat selected_nacs | xargs -I{} python mz_cluster.py clusters/{}_A17_a_4_uw markings/{}.csv expert_new.csv\
    1.0 4 10 3 4.0 0.4 100 30.655 30.800 20.125 20.255 &> mz_cluster_A17_a_4_uw.py.out )

( cat selected_nacs | xargs -I{} python mz_cluster.py clusters/{}_A17_b_2_uw markings/{}.csv expert_new.csv\
    1.5 2 10 3 4.0 0.4 100 30.655 30.800 20.125 20.255 &> mz_cluster_A17_b_2_uw.py.out ) &

( cat selected_nacs | xargs -I{} python mz_cluster.py clusters/{}_A17_b_3_uw markings/{}.csv expert_new.csv\
    1.5 3 10 3 4.0 0.4 100 30.655 30.800 20.125 20.255 &> mz_cluster_A17_b_3_uw.py.out ) &

( cat selected_nacs | xargs -I{} python mz_cluster.py clusters/{}_A17_b_4_uw markings/{}.csv expert_new.csv\
    1.5 4 10 3 4.0 0.4 100 30.655 30.800 20.125 20.255 &> mz_cluster_A17_b_4_uw.py.out )

( cat selected_nacs | xargs -I{} python mz_cluster.py clusters/{}_A17_c_2_uw markings/{}.csv expert_new.csv\
    0.75 2 10 3 4.0 0.4 100 30.655 30.800 20.125 20.255 &> mz_cluster_A17_c_2_uw.py.out ) &

( cat selected_nacs | xargs -I{} python mz_cluster.py clusters/{}_A17_c_3_uw markings/{}.csv expert_new.csv\
    0.75 3 10 3 4.0 0.4 100 30.655 30.800 20.125 20.255 &> mz_cluster_A17_c_3_uw.py.out ) &

( cat selected_nacs | xargs -I{} python mz_cluster.py clusters/{}_A17_c_4_uw markings/{}.csv expert_new.csv\
    0.75 4 10 3 4.0 0.4 100 30.655 30.800 20.125 20.255 &> mz_cluster_A17_c_4_uw.py.out )
