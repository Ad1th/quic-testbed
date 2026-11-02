# Rigor re-run summary

files: data/rigor/G_bridge_rcvbuf4m.csv; 480 transfers, failures counted at 40s

## Per protocol

```
topology offloads  rcvbuf quicgo_gso  rtt_ms  loss_pct protocol  n  fails  median_s    p25    p75  loss_events  pkts  drop_pct  tcp_retx  rcvbuf_err  cpu_client  cpu_server
  bridge      off 4194304         on      50         0       h2 20      0     0.554  0.518  0.622          0.0 742.0     0.000       0.0           0       0.014       0.010
  bridge      off 4194304         on      50         0       h3 20      0     0.471  0.467  0.477          0.0 813.0     0.000       0.0           0       0.016       0.010
  bridge      off 4194304         on      50         0     h3qg 20      0     0.353  0.349  0.357          0.0 903.0     0.000       0.0           0       0.020       0.020
  bridge      off 4194304         on      50         1       h2 20      0     1.624  1.256  3.231          6.0 736.0     0.809       6.5           0       0.021       0.010
  bridge      off 4194304         on      50         1       h3 20      0     4.580  3.818  5.876          8.0 768.5     1.016       0.0           0       0.046       0.020
  bridge      off 4194304         on      50         1     h3qg 20      0     1.190  0.510  2.212          8.0 861.0     0.912       0.0           0       0.036       0.040
  bridge      off 4194304         on      50         2       h2 20      0     4.286  2.569  5.708         15.0 736.0     1.995      15.0           0       0.030       0.010
  bridge      off 4194304         on      50         2       h3 20      0     6.863  5.732  7.393         16.0 776.0     2.013       0.0           0       0.058       0.030
  bridge      off 4194304         on      50         2     h3qg 20      0     2.859  2.254  3.075         16.5 835.5     1.909       0.0           0       0.054       0.060
  bridge      off 4194304         on      50         5       h2 20      0     9.581  8.485 11.054         40.5 736.0     5.219      40.5           0       0.048       0.010
  bridge      off 4194304         on      50         5       h3 20      0    11.186 10.560 11.752         42.5 783.5     5.180       0.0           0       0.086       0.050
  bridge      off 4194304         on      50         5     h3qg 20      0     6.033  5.352  6.359         42.5 833.5     4.822       0.0           0       0.064       0.080
  bridge      off 4194304         on     100         0       h2 20      0     0.992  0.970  1.076          0.0 748.0     0.000       0.0           0       0.016       0.010
  bridge      off 4194304         on     100         0       h3 20      0     0.875  0.859  0.886          0.0 793.0     0.000       0.0           0       0.017       0.010
  bridge      off 4194304         on     100         0     h3qg 20      0     0.686  0.681  0.689          0.0 900.0     0.000       0.0           0       0.025       0.030
  bridge      off 4194304         on     100         1       h2 20      0     4.445  2.764  5.565          8.0 736.0     1.074       8.0           0       0.024       0.010
  bridge      off 4194304         on     100         1       h3 20      0     8.141  6.785 10.582          8.0 770.0     1.022       0.0           0       0.044       0.020
  bridge      off 4194304         on     100         1     h3qg 20      0     2.701  1.603  4.299          8.0 851.5     0.937       0.0           0       0.054       0.060
  bridge      off 4194304         on     100         2       h2 20      0     7.716  4.389 10.594         15.0 736.0     2.000      15.0           0       0.035       0.010
  bridge      off 4194304         on     100         2       h3 20      0    12.950 11.033 13.435         15.5 767.5     1.964       0.0           0       0.069       0.040
  bridge      off 4194304         on     100         2     h3qg 20      0     5.389  3.313  6.403         18.0 839.0     2.133       0.0           0       0.060       0.075
  bridge      off 4194304         on     100         5       h2 20      0    17.045 15.366 18.867         38.0 737.0     4.900      38.5           0       0.052       0.020
  bridge      off 4194304         on     100         5       h3 20      0    20.404 18.829 21.380         42.5 787.5     5.081       0.0           0       0.100       0.055
  bridge      off 4194304         on     100         5     h3qg 20      0    10.384  9.226 11.032         43.5 836.0     4.963       0.0           0       0.076       0.080
```

## Paired ratios vs h2 (median of per-iteration ratios; Bonferroni over all rows)

```
topology offloads  rcvbuf quicgo_gso  rtt_ms  loss_pct proto  n  ratio  ci_lo  ci_hi      p  p_bonf            verdict
  bridge      off 4194304         on      50         0    h3 20 0.8466 0.7716 0.9079 0.0000  0.0000          h3 faster
  bridge      off 4194304         on      50         0  h3qg 20 0.6334 0.5770 0.6714 0.0000  0.0000        h3qg faster
  bridge      off 4194304         on      50         1    h3 20 2.7239 1.7665 3.2803 0.0000  0.0004          h2 faster
  bridge      off 4194304         on      50         1  h3qg 20 0.7003 0.2751 1.5449 0.1650  1.0000 no sig. difference
  bridge      off 4194304         on      50         2    h3 20 1.6341 1.3436 2.3061 0.0001  0.0010          h2 faster
  bridge      off 4194304         on      50         2  h3qg 20 0.6182 0.5191 0.8089 0.0042  0.0675 no sig. difference
  bridge      off 4194304         on      50         5    h3 20 1.1513 1.0393 1.2399 0.0004  0.0063          h2 faster
  bridge      off 4194304         on      50         5  h3qg 20 0.5745 0.5484 0.6929 0.0000  0.0001        h3qg faster
  bridge      off 4194304         on     100         0    h3 20 0.8723 0.8212 0.8921 0.0000  0.0000          h3 faster
  bridge      off 4194304         on     100         0  h3qg 20 0.6897 0.6380 0.7082 0.0000  0.0000        h3qg faster
  bridge      off 4194304         on     100         1    h3 20 2.0730 1.6713 2.8648 0.0000  0.0002          h2 faster
  bridge      off 4194304         on     100         1  h3qg 20 0.7701 0.4903 1.1057 0.0400  0.6398 no sig. difference
  bridge      off 4194304         on     100         2    h3 20 1.6005 1.2437 2.3939 0.0003  0.0042          h2 faster
  bridge      off 4194304         on     100         2  h3qg 20 0.6355 0.4227 0.9096 0.0049  0.0778 no sig. difference
  bridge      off 4194304         on     100         5    h3 20 1.2320 1.0507 1.3229 0.0042  0.0675 no sig. difference
  bridge      off 4194304         on     100         5  h3qg 20 0.5861 0.5248 0.6210 0.0000  0.0000        h3qg faster
```
