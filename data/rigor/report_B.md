# Rigor re-run summary

files: data/rigor/B_offoff.csv; 480 transfers, failures counted at 40s

## Per protocol

```
topology offloads  rcvbuf quicgo_gso  rtt_ms  loss_pct protocol  n  fails  median_s    p25    p75  loss_events  pkts  drop_pct  tcp_retx  rcvbuf_err  cpu_client  cpu_server
  direct      off  212992         on      50         0       h2 20      0     0.538  0.515  0.586          0.0 742.0     0.000       0.0           0       0.014       0.010
  direct      off  212992         on      50         0       h3 20      0     0.732  0.682  0.794          0.0 951.5     0.000       0.0        3072       0.019       0.010
  direct      off  212992         on      50         0     h3qg 20      0     0.356  0.352  0.361          0.0 902.5     0.000       0.0           0       0.022       0.020
  direct      off  212992         on      50         1       h2 20      0     0.941  0.670  1.312          3.0 737.0     0.405       6.0           0       0.016       0.010
  direct      off  212992         on      50         1       h3 20      0     4.730  2.149  5.462          8.0 776.0     0.961       0.0        1079       0.044       0.020
  direct      off  212992         on      50         1     h3qg 20      0     0.688  0.429  1.097          2.0 884.5     0.224       0.0           0       0.028       0.030
  direct      off  212992         on      50         2       h2 20      0     2.092  0.750  3.975          7.5 737.0     1.008      16.0           0       0.022       0.010
  direct      off  212992         on      50         2       h3 20      0     6.392  5.055  7.165         15.0 775.5     1.830       0.0         371       0.058       0.030
  direct      off  212992         on      50         2     h3qg 20      0     1.448  0.483  2.192          6.0 851.0     0.722       0.0           0       0.040       0.040
  direct      off  212992         on      50         5       h2 20      0     6.938  5.013  8.003         23.0 738.0     3.028      38.5           0       0.038       0.010
  direct      off  212992         on      50         5       h3 20      0    11.135 10.253 11.747         39.0 787.0     4.685       0.0           0       0.086       0.040
  direct      off  212992         on      50         5     h3qg 20      0     3.010  1.894  3.445         16.0 833.5     1.897       0.0           0       0.046       0.055
  direct      off  212992         on     100         0       h2 20      0     0.974  0.962  0.983          0.0 749.0     0.000       0.0           0       0.016       0.010
  direct      off  212992         on     100         0       h3 20      0     1.295  1.199  1.510          0.0 934.5     0.000       0.0        2962       0.021       0.015
  direct      off  212992         on     100         0     h3qg 20      0     0.681  0.679  0.688          0.0 900.0     0.000       0.0           0       0.023       0.020
  direct      off  212992         on     100         1       h2 20      0     1.582  1.156  3.900          4.0 737.0     0.540       9.0           0       0.021       0.010
  direct      off  212992         on     100         1       h3 20      0     8.295  6.463  9.848          7.5 767.0     0.971       0.0         372       0.047       0.025
  direct      off  212992         on     100         1     h3qg 20      0     1.866  0.838  3.172          3.0 855.0     0.353       0.0           0       0.040       0.050
  direct      off  212992         on     100         2       h2 20      0     5.304  2.642  7.466          9.0 737.0     1.208      16.5           0       0.028       0.010
  direct      off  212992         on     100         2       h3 20      0    13.720 12.268 14.200         17.5 766.5     2.211       0.0           0       0.065       0.030
  direct      off  212992         on     100         2     h3qg 20      0     2.682  1.933  3.735          7.0 845.0     0.831       0.0           0       0.059       0.065
  direct      off  212992         on     100         5       h2 20      0    11.916 10.365 13.669         24.0 737.5     3.152      39.0           0       0.038       0.020
  direct      off  212992         on     100         5       h3 20      0    19.049 17.874 20.121         36.0 782.0     4.411       0.0           0       0.088       0.050
  direct      off  212992         on     100         5     h3qg 20      0     5.850  4.895  6.843         18.5 828.0     2.148       0.0           0       0.060       0.070
```

## Paired ratios vs h2 (median of per-iteration ratios; Bonferroni over all rows)

```
topology offloads  rcvbuf quicgo_gso  rtt_ms  loss_pct proto  n  ratio  ci_lo  ci_hi      p  p_bonf            verdict
  direct      off  212992         on      50         0    h3 20 1.3115 1.2336 1.4349 0.0000  0.0000          h2 faster
  direct      off  212992         on      50         0  h3qg 20 0.6602 0.6112 0.6842 0.0000  0.0000        h3qg faster
  direct      off  212992         on      50         1    h3 20 3.2850 1.6562 6.0684 0.0002  0.0027          h2 faster
  direct      off  212992         on      50         1  h3qg 20 0.5554 0.4148 1.3742 0.3300  1.0000 no sig. difference
  direct      off  212992         on      50         2    h3 20 3.7026 1.4618 7.6881 0.0001  0.0021          h2 faster
  direct      off  212992         on      50         2  h3qg 20 0.6898 0.3414 1.5415 0.0973  1.0000 no sig. difference
  direct      off  212992         on      50         5    h3 20 1.5551 1.3632 1.9408 0.0000  0.0002          h2 faster
  direct      off  212992         on      50         5  h3qg 20 0.3688 0.2801 0.5152 0.0000  0.0006        h3qg faster
  direct      off  212992         on     100         0    h3 20 1.3136 1.2582 1.5084 0.0000  0.0000          h2 faster
  direct      off  212992         on     100         0  h3qg 20 0.7027 0.6914 0.7095 0.0000  0.0000        h3qg faster
  direct      off  212992         on     100         1    h3 20 3.8691 1.6258 7.0176 0.0000  0.0006          h2 faster
  direct      off  212992         on     100         1  h3qg 20 0.6583 0.4595 1.3723 0.2611  1.0000 no sig. difference
  direct      off  212992         on     100         2    h3 20 2.6613 1.8607 4.6170 0.0000  0.0001          h2 faster
  direct      off  212992         on     100         2  h3qg 20 0.5942 0.3822 0.7679 0.0004  0.0063        h3qg faster
  direct      off  212992         on     100         5    h3 20 1.5825 1.4281 1.9317 0.0000  0.0000          h2 faster
  direct      off  212992         on     100         5  h3qg 20 0.4536 0.3649 0.5907 0.0000  0.0000        h3qg faster
```
