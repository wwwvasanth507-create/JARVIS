# Phase 11 CPU Performance Benchmark Comparison

- **Baseline Timestamp**: 2026-09-14T14:02:57.445360+00:00
- **Current Timestamp**: 2026-09-14T14:15:13.460918+00:00
- **PyTorch**: 2.14.0+cpu
- **Processor**: Intel64 Family 6 Model 142 Stepping 12, GenuineIntel
- **Regression Threshold**: 10.0%

| Metric | Baseline | Current | Delta | % Change | Status |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Forward Latency (b1_s16) | 2.22 ms | 0.84 ms | -1.38 ms | -62.0% | **IMPROVED** |
| Forward Throughput (b1_s16) | 7202.11 tok/s | 18926.40 tok/s | +11724.29 tok/s | +162.8% | **IMPROVED** |
| Forward Latency (b1_s64) | 2.47 ms | 1.22 ms | -1.25 ms | -50.5% | **IMPROVED** |
| Forward Throughput (b1_s64) | 25946.96 tok/s | 52427.07 tok/s | +26480.11 tok/s | +102.1% | **IMPROVED** |
| Forward Latency (b4_s16) | 2.79 ms | 1.25 ms | -1.54 ms | -55.0% | **IMPROVED** |
| Forward Throughput (b4_s16) | 22932.74 tok/s | 50976.52 tok/s | +28043.78 tok/s | +122.3% | **IMPROVED** |
| Forward Latency (b4_s64) | 4.16 ms | 1.59 ms | -2.57 ms | -61.7% | **IMPROVED** |
| Forward Throughput (b4_s64) | 61519.68 tok/s | 160766.99 tok/s | +99247.31 tok/s | +161.3% | **IMPROVED** |
| Prompt Prefill Latency | 2.86 ms | 0.96 ms | -1.91 ms | -66.5% | **IMPROVED** |
| First Token Latency | 3.23 ms | 1.06 ms | -2.17 ms | -67.2% | **IMPROVED** |
| Naive Generation Throughput | 373.03 tok/s | 989.59 tok/s | +616.56 tok/s | +165.3% | **IMPROVED** |
| Cached Generation Throughput | 468.11 tok/s | 1097.32 tok/s | +629.21 tok/s | +134.4% | **IMPROVED** |
| KV Cache Speedup | 1.25 x | 1.11 x | -0.15 x | -11.6% | **REGRESSED** |
| torch.no_grad Throughput | 402.16 tok/s | 931.15 tok/s | +528.99 tok/s | +131.5% | **IMPROVED** |
| torch.inference_mode Throughput | 543.68 tok/s | 1050.76 tok/s | +507.08 tok/s | +93.3% | **IMPROVED** |
| Tokenizer Encode (short_english) | 634048.40 tok/s | 3783102.15 tok/s | +3149053.75 tok/s | +496.7% | **IMPROVED** |
| Tokenizer Decode (short_english) | 1242493.27 tok/s | 8658008.62 tok/s | +7415515.35 tok/s | +596.8% | **IMPROVED** |
| Tokenizer Encode (medium_english) | 335803.44 tok/s | 5927011.19 tok/s | +5591207.75 tok/s | +1665.0% | **IMPROVED** |
| Tokenizer Decode (medium_english) | 1248106.80 tok/s | 10293777.48 tok/s | +9045670.68 tok/s | +724.8% | **IMPROVED** |
| Tokenizer Encode (long_english) | 209025.73 tok/s | 8147967.08 tok/s | +7938941.35 tok/s | +3798.1% | **IMPROVED** |
| Tokenizer Decode (long_english) | 1270493.51 tok/s | 11554777.90 tok/s | +10284284.39 tok/s | +809.5% | **IMPROVED** |
| Tokenizer Encode (unicode_tamil) | 206355.76 tok/s | 3615374.86 tok/s | +3409019.10 tok/s | +1652.0% | **IMPROVED** |
| Tokenizer Decode (unicode_tamil) | 1330532.21 tok/s | 9307642.07 tok/s | +7977109.86 tok/s | +599.5% | **IMPROVED** |
| Memmap Open Latency | 1.53 ms | 0.98 ms | -0.56 ms | -36.4% | **IMPROVED** |
| Sequence Retrieval | 142468.41 seq/s | 230962.88 seq/s | +88494.47 seq/s | +62.1% | **IMPROVED** |
| Batch Construction | 2736.41 batches/s | 20339.26 batches/s | +17602.85 batches/s | +643.3% | **IMPROVED** |
| Training Step Latency | 17.49 ms | 10.14 ms | -7.35 ms | -42.0% | **IMPROVED** |
| Training Throughput | 14633.63 tok/s | 25240.08 tok/s | +10606.45 tok/s | +72.5% | **IMPROVED** |
| API Health Latency | 2.24 ms | 1.12 ms | -1.12 ms | -49.9% | **IMPROVED** |
| API Chat Sync Latency | 12.44 ms | 4.75 ms | -7.69 ms | -61.8% | **IMPROVED** |
| API SSE First Token Latency | 11.88 ms | 5.56 ms | -6.32 ms | -53.2% | **IMPROVED** |
| Process RSS (Model Loaded) | 338.84 MB | 334.64 MB | -4.20 MB | -1.2% | **IMPROVED** |
| Process RSS (API Idle) | 339.54 MB | 336.95 MB | -2.59 MB | -0.8% | UNCHANGED |
| Process RSS (1 Session) | 336.48 MB | 336.72 MB | +0.24 MB | +0.1% | UNCHANGED |
| Process RSS (5 Sessions) | 336.97 MB | 337.12 MB | +0.15 MB | +0.0% | UNCHANGED |
