# Rigor re-run summary

files: data/rigor/H_bridge_rcvbuf4m_4senders.csv; 634 transfers, failures counted at 40s

## Per protocol

```
topology offloads  rcvbuf quicgo_gso  rtt_ms  loss_pct protocol  n  fails  median_s    p25    p75  loss_events  pkts  drop_pct  tcp_retx  rcvbuf_err  cpu_client  cpu_server
  bridge      off 4194304         on      50         0       h2 20      0     0.603  0.531  0.653          0.0 736.0     0.000       0.0           0       0.016       0.010
  bridge      off 4194304         on      50         0       h3 20      0     0.474  0.466  0.480          0.0 812.0     0.000       0.0           0       0.016       0.010
  bridge      off 4194304         on      50         0     h3qc 20      0     0.485  0.479  0.509          0.0 817.0     0.000       0.0           0       0.015       0.010
  bridge      off 4194304         on      50         0     h3qg 20      0     0.355  0.351  0.358          0.0 902.5     0.000       0.0           0       0.020       0.020
  bridge      off 4194304         on      50         1       h2 20      0     2.278  1.422  2.707          7.5 735.0     1.009       7.5           0       0.020       0.010
  bridge      off 4194304         on      50         1       h3 20      0     4.434  3.627  5.178          7.0 776.5     0.903       0.0           0       0.033       0.020
  bridge      off 4194304         on      50         1     h3qc 20      0     1.882  0.867  2.968          9.0 820.0     1.078       0.0           0       0.023       0.015
  bridge      off 4194304         on      50         1     h3qg 20      0     1.417  0.750  1.718          8.0 854.5     0.904       0.0           0       0.032       0.040
  bridge      off 4194304         on      50         2       h2 20      0     4.318  3.346  5.801         13.0 735.0     1.738      13.0           0       0.024       0.010
  bridge      off 4194304         on      50         2       h3 20      0     7.743  6.719  8.081         17.0 768.5     2.151       0.0           0       0.046       0.025
  bridge      off 4194304         on      50         2     h3qc 20      0     3.550  2.891  4.747         17.0 837.5     2.008       0.0           0       0.028       0.020
  bridge      off 4194304         on      50         2     h3qg 20      0     2.610  2.176  3.569         16.0 837.5     1.872       0.0           0       0.036       0.040
  bridge      off 4194304         on      50         5       h2 18      0    10.161  8.105 11.753         41.0 735.5     5.263      41.0           0       0.037       0.010
  bridge      off 4194304         on      50         5       h3 18      0    11.248 10.981 11.954         41.5 783.0     5.030       0.0           0       0.062       0.035
  bridge      off 4194304         on      50         5     h3qc 19      0     7.785  6.769  8.557         48.0 884.0     5.150       0.0           0       0.046       0.040
  bridge      off 4194304         on      50         5     h3qg 20      0     6.037  5.633  6.524         42.5 829.5     4.888       0.0           0       0.048       0.050
  bridge      off 4194304         on     100         0       h2 20      0     0.962  0.954  1.056          0.0 739.0     0.000       0.0           0       0.018       0.010
  bridge      off 4194304         on     100         0       h3 20      0     0.852  0.847  0.857          0.0 793.0     0.000       0.0           0       0.020       0.010
  bridge      off 4194304         on     100         0     h3qc 20      0     0.863  0.858  0.875          0.0 824.0     0.000       0.0           0       0.018       0.015
  bridge      off 4194304         on     100         0     h3qg 19      0     0.676  0.674  0.679          0.0 900.0     0.000       0.0           0       0.033       0.040
  bridge      off 4194304         on     100         1       h2 20      0     2.419  1.611  3.496          7.0 736.0     0.942       7.0           0       0.024       0.010
  bridge      off 4194304         on     100         1       h3 20      0     6.433  5.076  8.166          5.5 765.5     0.715       0.0           0       0.046       0.030
  bridge      off 4194304         on     100         1     h3qc 20      0     2.346  1.700  4.996          9.0 822.0     1.082       0.0           0       0.025       0.020
  bridge      off 4194304         on     100         1     h3qg 20      0     2.197  1.192  3.834          7.5 860.0     0.865       0.0           0       0.052       0.055
  bridge      off 4194304         on     100         2       h2 20      0     7.021  5.435  7.680         15.5 736.0     2.064      15.5           0       0.038       0.010
  bridge      off 4194304         on     100         2       h3 20      0    10.680  9.460 13.106         13.5 769.0     1.730       0.0           0       0.059       0.035
  bridge      off 4194304         on     100         2     h3qc 20      0     5.412  3.106  6.890         15.5 832.0     1.811       0.0           0       0.037       0.030
  bridge      off 4194304         on     100         2     h3qg 20      0     5.028  3.492  6.329         17.0 834.0     1.987       0.0           0       0.060       0.065
  bridge      off 4194304         on     100         5       h2 20      0    19.213 17.168 20.989         42.0 737.0     5.388      43.5           0       0.058       0.010
  bridge      off 4194304         on     100         5       h3 20      0    19.679 18.191 21.473         39.5 787.0     4.731       0.0           0       0.098       0.060
  bridge      off 4194304         on     100         5     h3qc 20      0    13.951 12.416 15.592         51.5 887.5     5.390       0.0           0       0.078       0.055
  bridge      off 4194304         on     100         5     h3qg 20      0    10.778  9.143 11.530         44.0 835.0     4.954       0.0           0       0.079       0.090
```

## Paired ratios vs h2 (median of per-iteration ratios; Bonferroni over all rows)

```
topology offloads  rcvbuf quicgo_gso  rtt_ms  loss_pct proto  n  ratio  ci_lo  ci_hi      p  p_bonf            verdict
  bridge      off 4194304         on      50         0    h3 20 0.7920 0.7428 0.8669 0.0000  0.0000          h3 faster
  bridge      off 4194304         on      50         0  h3qg 20 0.5954 0.5432 0.6501 0.0000  0.0000        h3qg faster
  bridge      off 4194304         on      50         0  h3qc 20 0.8434 0.7810 0.9163 0.0000  0.0002        h3qc faster
  bridge      off 4194304         on      50         1    h3 20 1.8626 1.7052 2.6626 0.0014  0.0344          h2 faster
  bridge      off 4194304         on      50         1  h3qg 20 0.6137 0.4338 1.0551 0.0240  0.5748 no sig. difference
  bridge      off 4194304         on      50         1  h3qc 20 0.9703 0.8075 1.1762 0.5459  1.0000 no sig. difference
  bridge      off 4194304         on      50         2    h3 20 1.4856 1.3370 2.0910 0.0001  0.0015          h2 faster
  bridge      off 4194304         on      50         2  h3qg 20 0.6196 0.4241 0.8639 0.0012  0.0290        h3qg faster
  bridge      off 4194304         on      50         2  h3qc 20 0.8379 0.5423 0.9985 0.0826  1.0000 no sig. difference
  bridge      off 4194304         on      50         5    h3 16 1.2157 0.9625 1.3637 0.0290  0.6958 no sig. difference
  bridge      off 4194304         on      50         5  h3qg 18 0.5818 0.5516 0.7093 0.0000  0.0002        h3qg faster
  bridge      off 4194304         on      50         5  h3qc 18 0.7811 0.6535 0.9363 0.0019  0.0463        h3qc faster
  bridge      off 4194304         on     100         0    h3 20 0.8866 0.8039 0.8955 0.0000  0.0000          h3 faster
  bridge      off 4194304         on     100         0  h3qg 19 0.7033 0.6408 0.7114 0.0000  0.0001        h3qg faster
  bridge      off 4194304         on     100         0  h3qc 20 0.8913 0.8220 0.9041 0.0037  0.0877 no sig. difference
  bridge      off 4194304         on     100         1    h3 20 2.6206 1.6799 3.5636 0.0001  0.0025          h2 faster
  bridge      off 4194304         on     100         1  h3qg 20 0.9365 0.5643 1.1386 0.3300  1.0000 no sig. difference
  bridge      off 4194304         on     100         1  h3qc 20 1.0061 0.5756 2.1502 0.5706  1.0000 no sig. difference
  bridge      off 4194304         on     100         2    h3 20 1.5051 1.3348 2.1687 0.0003  0.0063          h2 faster
  bridge      off 4194304         on     100         2  h3qg 20 0.7889 0.5224 0.9334 0.0083  0.1994 no sig. difference
  bridge      off 4194304         on     100         2  h3qc 20 0.8525 0.5149 0.9704 0.0107  0.2565 no sig. difference
  bridge      off 4194304         on     100         5    h3 20 1.0880 0.9192 1.1616 0.3683  1.0000 no sig. difference
  bridge      off 4194304         on     100         5  h3qg 20 0.5358 0.5010 0.6245 0.0000  0.0001        h3qg faster
  bridge      off 4194304         on     100         5  h3qc 20 0.6962 0.6449 0.8071 0.0000  0.0001        h3qc faster
```
