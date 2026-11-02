# Rigor re-run summary

files: data/rigor/P_nginx_patched.csv; 477 transfers, failures counted at 40s

## Per protocol

```
topology offloads  rcvbuf quicgo_gso  rtt_ms  loss_pct protocol  n  fails  median_s    p25    p75  loss_events  pkts  drop_pct  tcp_retx  rcvbuf_err  cpu_client  cpu_server
  bridge      off 4194304         on      50         0       h2 20      0     0.578  0.560  0.628          0.0 743.0     0.000       0.0           0       0.015        0.01
  bridge      off 4194304         on      50         0       h3 20      0     0.472  0.457  0.478          0.0 814.0     0.000       0.0           0       0.017        0.01
  bridge      off 4194304         on      50         0     h3qg 20      0     0.355  0.351  0.358          0.0 903.0     0.000       0.0           0       0.022        0.02
  bridge      off 4194304         on      50         1       h2 19      0     2.601  1.042  3.113          7.0 737.0     0.937       7.0           0       0.022        0.01
  bridge      off 4194304         on      50         1       h3 20      0     2.045  1.010  3.640          7.5 780.0     0.960       0.0           0       0.032        0.02
  bridge      off 4194304         on      50         1     h3qg 20      0     1.166  0.617  1.590          6.0 858.0     0.695       0.0           0       0.040        0.04
  bridge      off 4194304         on      50         2       h2 19      0     5.274  3.693  5.853         16.0 736.0     2.130      16.0           0       0.031        0.01
  bridge      off 4194304         on      50         2       h3 19      0     3.768  2.848  4.339         16.0 780.0     2.023       0.0           0       0.038        0.02
  bridge      off 4194304         on      50         2     h3qg 20      0     2.861  2.251  3.299         17.0 836.0     1.958       0.0           0       0.046        0.05
  bridge      off 4194304         on      50         5       h2 20      0    10.575  9.717 11.498         41.0 737.0     5.273      42.0           0       0.038        0.01
  bridge      off 4194304         on      50         5       h3 20      0     6.733  5.595  7.494         40.0 776.5     4.852       0.0           0       0.046        0.02
  bridge      off 4194304         on      50         5     h3qg 20      0     6.121  5.106  6.588         42.0 828.0     4.805       0.0           0       0.046        0.05
  bridge      off 4194304         on     100         0       h2 20      0     1.035  0.974  1.086          0.0 749.0     0.000       0.0           0       0.016        0.01
  bridge      off 4194304         on     100         0       h3 20      0     0.882  0.871  0.889          0.0 793.0     0.000       0.0           0       0.017        0.01
  bridge      off 4194304         on     100         0     h3qg 20      0     0.687  0.682  0.689          0.0 898.5     0.000       0.0           0       0.025        0.03
  bridge      off 4194304         on     100         1       h2 20      0     5.395  1.884  6.468          6.0 737.0     0.808       6.0           0       0.025        0.01
  bridge      off 4194304         on     100         1       h3 20      0     1.812  1.478  4.249          7.5 779.5     0.965       0.0           0       0.022        0.01
  bridge      off 4194304         on     100         1     h3qg 20      0     4.098  2.828  4.629          9.0 836.5     1.062       0.0           0       0.044        0.05
  bridge      off 4194304         on     100         2       h2 20      0     8.451  6.542  9.898         17.0 736.0     2.253      17.0           0       0.032        0.01
  bridge      off 4194304         on     100         2       h3 20      0     4.313  2.133  6.994         16.0 774.5     2.008       0.0           0       0.030        0.02
  bridge      off 4194304         on     100         2     h3qg 20      0     5.254  4.270  6.365         18.0 836.5     2.080       0.0           0       0.048        0.05
  bridge      off 4194304         on     100         5       h2 20      0    15.949 14.248 17.696         36.0 736.5     4.651      36.0           0       0.041        0.01
  bridge      off 4194304         on     100         5       h3 20      0    13.730 11.704 14.659         40.0 781.0     4.879       0.0           0       0.058        0.03
  bridge      off 4194304         on     100         5     h3qg 20      0    10.517  9.470 11.177         40.5 831.0     4.661       0.0           0       0.055        0.06
```

## Paired ratios vs h2 (median of per-iteration ratios; Bonferroni over all rows)

```
topology offloads  rcvbuf quicgo_gso  rtt_ms  loss_pct proto  n  ratio  ci_lo  ci_hi      p  p_bonf            verdict
  bridge      off 4194304         on      50         0    h3 20 0.8132 0.7799 0.8429 0.0000  0.0000          h3 faster
  bridge      off 4194304         on      50         0  h3qg 20 0.6071 0.5875 0.6258 0.0000  0.0000        h3qg faster
  bridge      off 4194304         on      50         1    h3 19 1.3123 0.4864 1.4854 0.9843  1.0000 no sig. difference
  bridge      off 4194304         on      50         1  h3qg 19 0.4650 0.3123 0.6574 0.0008  0.0126        h3qg faster
  bridge      off 4194304         on      50         2    h3 18 0.8390 0.5287 1.1901 0.1187  1.0000 no sig. difference
  bridge      off 4194304         on      50         2  h3qg 19 0.4775 0.3718 0.7541 0.0002  0.0034        h3qg faster
  bridge      off 4194304         on      50         5    h3 20 0.6419 0.5770 0.6841 0.0000  0.0001          h3 faster
  bridge      off 4194304         on      50         5  h3qg 20 0.5393 0.4900 0.6113 0.0000  0.0000        h3qg faster
  bridge      off 4194304         on     100         0    h3 20 0.8673 0.8057 0.9049 0.0000  0.0000          h3 faster
  bridge      off 4194304         on     100         0  h3qg 20 0.6618 0.6357 0.6992 0.0000  0.0000        h3qg faster
  bridge      off 4194304         on     100         1    h3 20 0.6563 0.3650 1.0504 0.0759  1.0000 no sig. difference
  bridge      off 4194304         on     100         1  h3qg 20 0.8070 0.6298 1.5494 0.2943  1.0000 no sig. difference
  bridge      off 4194304         on     100         2    h3 20 0.6483 0.2974 0.8075 0.0007  0.0113          h3 faster
  bridge      off 4194304         on     100         2  h3qg 20 0.6637 0.5754 0.8484 0.0007  0.0113        h3qg faster
  bridge      off 4194304         on     100         5    h3 20 0.8663 0.7763 0.8970 0.0049  0.0778 no sig. difference
  bridge      off 4194304         on     100         5  h3qg 20 0.5984 0.5752 0.7112 0.0001  0.0010        h3qg faster
```
