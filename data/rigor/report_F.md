# Rigor re-run summary

files: data/rigor/F_bridge.csv; 480 transfers, failures counted at 40s

## Per protocol

```
topology offloads  rcvbuf quicgo_gso  rtt_ms  loss_pct protocol  n  fails  median_s    p25    p75  loss_events  pkts  drop_pct  tcp_retx  rcvbuf_err  cpu_client  cpu_server
  bridge      off  212992         on      50         0       h2 20      0     0.591  0.543  0.618          0.0 742.0     0.000       0.0           0       0.014       0.000
  bridge      off  212992         on      50         0       h3 20      0     0.726  0.647  0.818          0.0 959.0     0.000       0.0        3082       0.019       0.010
  bridge      off  212992         on      50         0     h3qg 20      0     0.355  0.351  0.357          0.0 902.5     0.000       0.0           0       0.021       0.020
  bridge      off  212992         on      50         1       h2 20      0     2.313  1.177  2.912          7.5 736.0     1.007       7.5           0       0.022       0.010
  bridge      off  212992         on      50         1       h3 20      0     4.819  2.034  5.689          9.0 773.0     1.047       0.0        1104       0.040       0.020
  bridge      off  212992         on      50         1     h3qg 20      0     1.656  0.690  1.889          9.0 848.5     1.055       0.0           0       0.040       0.040
  bridge      off  212992         on      50         2       h2 20      0     4.646  3.846  5.679         16.5 736.0     2.196      16.5           0       0.031       0.010
  bridge      off  212992         on      50         2       h3 20      0     7.382  6.545  8.284         16.0 767.5     2.053       0.0           0       0.069       0.030
  bridge      off  212992         on      50         2     h3qg 20      0     2.796  2.041  3.168         18.5 837.5     2.155       0.0           0       0.048       0.055
  bridge      off  212992         on      50         5       h2 20      0    10.502  9.518 10.958         38.0 736.0     4.913      38.5           0       0.049       0.010
  bridge      off  212992         on      50         5       h3 20      0    11.057 10.296 11.554         41.5 783.0     5.018       0.0           0       0.092       0.050
  bridge      off  212992         on      50         5     h3qg 20      0     5.456  4.901  5.734         42.5 829.5     4.891       0.0           0       0.056       0.070
  bridge      off  212992         on     100         0       h2 20      0     0.970  0.964  0.979          0.0 747.0     0.000       0.0           0       0.016       0.010
  bridge      off  212992         on     100         0       h3 20      0     1.312  1.192  1.517          0.0 925.5     0.000       0.0        2649       0.022       0.020
  bridge      off  212992         on     100         0     h3qg 20      0     0.682  0.679  0.689          0.0 899.5     0.000       0.0          12       0.025       0.030
  bridge      off  212992         on     100         1       h2 20      0     4.171  1.531  5.675          7.0 736.0     0.943       7.0           0       0.029       0.010
  bridge      off  212992         on     100         1       h3 20      0     8.429  5.970  9.249          7.0 766.0     0.914       0.0         576       0.047       0.030
  bridge      off  212992         on     100         1     h3qg 20      0     3.075  1.717  4.289          8.5 846.0     0.982       0.0           0       0.050       0.060
  bridge      off  212992         on     100         2       h2 20      0     6.375  5.716  9.525         15.5 736.0     2.056      16.0           0       0.032       0.010
  bridge      off  212992         on     100         2       h3 20      0    12.893 11.731 13.664         16.0 767.5     1.997       0.0         262       0.064       0.040
  bridge      off  212992         on     100         2     h3qg 20      0     3.938  3.110  5.967         16.0 840.5     1.852       0.0           0       0.056       0.065
  bridge      off  212992         on     100         5       h2 20      0    18.668 15.635 21.196         39.5 737.0     5.080      41.0           0       0.054       0.015
  bridge      off  212992         on     100         5       h3 20      0    19.967 18.319 21.541         38.5 780.0     4.678       0.0           0       0.100       0.060
  bridge      off  212992         on     100         5     h3qg 20      0    10.649  9.655 12.061         44.5 836.0     5.060       0.0           0       0.076       0.080
```

## Paired ratios vs h2 (median of per-iteration ratios; Bonferroni over all rows)

```
topology offloads  rcvbuf quicgo_gso  rtt_ms  loss_pct proto  n  ratio  ci_lo  ci_hi      p  p_bonf            verdict
  bridge      off  212992         on      50         0    h3 20 1.1666 1.0556 1.4132 0.0005  0.0077          h2 faster
  bridge      off  212992         on      50         0  h3qg 20 0.6058 0.5716 0.6505 0.0000  0.0000        h3qg faster
  bridge      off  212992         on      50         1    h3 20 2.1049 1.4882 2.6734 0.0056  0.0893 no sig. difference
  bridge      off  212992         on      50         1  h3qg 20 0.8798 0.3272 1.2602 0.0973  1.0000 no sig. difference
  bridge      off  212992         on      50         2    h3 20 1.5492 1.3041 1.9783 0.0000  0.0000          h2 faster
  bridge      off  212992         on      50         2  h3qg 20 0.6065 0.4595 0.7370 0.0001  0.0017        h3qg faster
  bridge      off  212992         on      50         5    h3 20 1.0761 0.9472 1.1812 0.1140  1.0000 no sig. difference
  bridge      off  212992         on      50         5  h3qg 20 0.4985 0.4679 0.6191 0.0000  0.0003        h3qg faster
  bridge      off  212992         on     100         0    h3 20 1.3562 1.2291 1.5215 0.0000  0.0000          h2 faster
  bridge      off  212992         on     100         0  h3qg 20 0.7043 0.6905 0.7101 0.0000  0.0000        h3qg faster
  bridge      off  212992         on     100         1    h3 20 1.9865 1.2807 3.7133 0.0020  0.0318          h2 faster
  bridge      off  212992         on     100         1  h3qg 20 0.7560 0.5289 1.5650 0.2943  1.0000 no sig. difference
  bridge      off  212992         on     100         2    h3 20 2.0194 1.1953 2.2762 0.0000  0.0006          h2 faster
  bridge      off  212992         on     100         2  h3qg 20 0.5035 0.3950 0.7163 0.0012  0.0193        h3qg faster
  bridge      off  212992         on     100         5    h3 20 1.1038 0.9007 1.3016 0.1893  1.0000 no sig. difference
  bridge      off  212992         on     100         5  h3qg 20 0.5890 0.5018 0.6610 0.0000  0.0001        h3qg faster
```
