# Rigor re-run summary

files: data/rigor/A_offon.csv; 479 transfers, failures counted at 40s

## Per protocol

```
topology offloads  rcvbuf quicgo_gso  rtt_ms  loss_pct protocol  n  fails  median_s    p25    p75  loss_events  pkts  drop_pct  tcp_retx  rcvbuf_err  cpu_client  cpu_server
  direct       on  212992         on      50         0       h2 20      0     0.570  0.558  0.603          0.0 742.0     0.000       0.0           0       0.016       0.010
  direct       on  212992         on      50         0       h3 20      0     0.723  0.678  0.799          0.0 994.0     0.000       0.0        3603       0.019       0.010
  direct       on  212992         on      50         0     h3qg 20      0     0.356  0.348  0.360          0.0 903.5     0.000       0.0           0       0.020       0.020
  direct       on  212992         on      50         1       h2 20      0     0.937  0.654  1.990          2.5 737.0     0.337       6.5           0       0.017       0.010
  direct       on  212992         on      50         1       h3 19      0     4.602  3.194  5.453          7.0 776.0     0.907       0.0         745       0.040       0.020
  direct       on  212992         on      50         1     h3qg 20      0     0.814  0.397  1.130          4.0 872.5     0.452       0.0           0       0.031       0.030
  direct       on  212992         on      50         2       h2 20      0     1.500  1.117  3.087          7.0 736.0     0.941      14.5           0       0.021       0.010
  direct       on  212992         on      50         2       h3 20      0     7.281  6.587  8.322         15.5 773.0     1.973       0.0         234       0.058       0.030
  direct       on  212992         on      50         2     h3qg 20      0     0.984  0.605  1.585          5.0 863.0     0.573       0.0           0       0.035       0.040
  direct       on  212992         on      50         5       h2 20      0     4.470  3.070  7.561         19.0 736.0     2.512      36.0           0       0.028       0.010
  direct       on  212992         on      50         5       h3 20      0    11.704 10.806 12.351         41.5 786.0     5.008       0.0           0       0.078       0.040
  direct       on  212992         on      50         5     h3qg 20      0     2.989  2.374  3.785         17.0 833.5     2.017       0.0           0       0.044       0.050
  direct       on  212992         on     100         0       h2 20      0     1.002  0.977  1.077          0.0 749.0     0.000       0.0           0       0.015       0.005
  direct       on  212992         on     100         0       h3 20      0     1.358  1.253  1.538          0.0 931.5     0.000       0.0        3128       0.020       0.015
  direct       on  212992         on     100         0     h3qg 20      0     0.684  0.678  0.689          0.0 900.0     0.000       0.0           0       0.025       0.025
  direct       on  212992         on     100         1       h2 20      0     1.553  1.200  4.201          3.0 739.0     0.401       6.0           0       0.020       0.005
  direct       on  212992         on     100         1       h3 20      0     8.417  5.471 10.683          7.5 768.0     0.971       0.0         307       0.048       0.030
  direct       on  212992         on     100         1     h3qg 20      0     1.162  0.788  2.527          3.0 877.0     0.341       0.0           0       0.038       0.045
  direct       on  212992         on     100         2       h2 20      0     2.464  1.421  4.712          7.0 737.0     0.935      13.0           0       0.022       0.010
  direct       on  212992         on     100         2       h3 20      0    12.713 11.672 13.990         16.5 768.0     2.040       0.0         128       0.066       0.030
  direct       on  212992         on     100         2     h3qg 20      0     2.088  1.292  3.528          7.0 852.5     0.828       0.0           0       0.040       0.050
  direct       on  212992         on     100         5       h2 20      0    10.972  8.243 13.064         21.5 736.0     2.838      39.5           0       0.038       0.010
  direct       on  212992         on     100         5       h3 20      0    20.215 19.140 21.755         43.5 784.0     5.217       0.0           0       0.096       0.050
  direct       on  212992         on     100         5     h3qg 20      0     6.042  5.495  7.005         18.5 829.5     2.166       0.0           0       0.068       0.075
```

## Paired ratios vs h2 (median of per-iteration ratios; Bonferroni over all rows)

```
topology offloads  rcvbuf quicgo_gso  rtt_ms  loss_pct proto  n  ratio  ci_lo  ci_hi      p  p_bonf            verdict
  direct       on  212992         on      50         0    h3 20 1.2337 1.1195 1.4096 0.0000  0.0002          h2 faster
  direct       on  212992         on      50         0  h3qg 20 0.6244 0.5976 0.6324 0.0000  0.0000        h3qg faster
  direct       on  212992         on      50         1    h3 19 3.5410 2.6404 7.2325 0.0002  0.0026          h2 faster
  direct       on  212992         on      50         1  h3qg 20 0.6484 0.4303 0.9207 0.0637  1.0000 no sig. difference
  direct       on  212992         on      50         2    h3 20 4.6946 3.0584 5.9451 0.0000  0.0002          h2 faster
  direct       on  212992         on      50         2  h3qg 20 0.7558 0.3391 0.9143 0.0240  0.3832 no sig. difference
  direct       on  212992         on      50         5    h3 20 2.5045 1.6460 3.4504 0.0000  0.0000          h2 faster
  direct       on  212992         on      50         5  h3qg 20 0.5219 0.4332 0.8234 0.0009  0.0136        h3qg faster
  direct       on  212992         on     100         0    h3 20 1.3386 1.2129 1.5341 0.0000  0.0000          h2 faster
  direct       on  212992         on     100         0  h3qg 20 0.6843 0.6451 0.6996 0.0000  0.0000        h3qg faster
  direct       on  212992         on     100         1    h3 20 4.2269 1.9532 6.9077 0.0001  0.0021          h2 faster
  direct       on  212992         on     100         1  h3qg 20 0.8477 0.4821 1.1510 0.2774  1.0000 no sig. difference
  direct       on  212992         on     100         2    h3 20 6.1128 3.2395 8.1285 0.0000  0.0001          h2 faster
  direct       on  212992         on     100         2  h3qg 20 0.7759 0.5229 1.3449 0.4091  1.0000 no sig. difference
  direct       on  212992         on     100         5    h3 20 1.8776 1.5706 2.4524 0.0000  0.0000          h2 faster
  direct       on  212992         on     100         5  h3qg 20 0.5564 0.4977 0.7148 0.0003  0.0052        h3qg faster
```
