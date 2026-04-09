# Deadleaf 13B10 Release

這個目錄是可獨立交付的 release 包，內容包含：

- canonical observable target 定義：
  - [../../docs/observable_target_from_golden_samples.md](../../docs/observable_target_from_golden_samples.md)
  - [../../docs/gamma_0_5_hypothesis_matrix.md](../../docs/gamma_0_5_hypothesis_matrix.md)
  - [../../docs/parity_refit_benchmarks_2026-04-08.md](../../docs/parity_refit_benchmarks_2026-04-08.md)

- `algo/`
  - 演算法程式碼
- `config/`
  - release 專用設定檔
- `data/20260318_deadleaf_13b10/`
  - 驗證資料集
- `scripts/run_release_batch.py`
  - 批次跑完整資料集並產出 JSON 結果
- `scripts/run_release.sh`
  - shell 包裝腳本
- `results/`
  - 執行後的輸出目錄

## 執行

在 release 根目錄下執行：

```bash
./scripts/run_release.sh
```

這個預設模式現在會跑主要的 parity-fit release profile，不做 regression comparison。
目前 release 文件需要先說清楚兩件事：

- golden sample / Imatest report 中可直接觀察到的欄位，包含 `Gamma = 0.5`、`Color channel = R`
- 目前的 parity-fit release profile 仍然沿用同一條 PSD/MTF baseline，但 issue `#18` 另外加入了 `5.5" Phone` 的窄幅 viewing-geometry 修正

目前 release 的 primary target profile 是：

- `report gamma = 0.5`
- `report color channel = R`
- `analysis gamma = 1.0`
- `analysis bayer_mode = demosaic_red`
- `frequency_scale = 1.17`
- `5.5" Phone viewing_distance_cm = 25.55`

其中前兩者是目前 golden CSV 可直接觀測到的 report fields；
後三者則是目前 release 採用、並已在 repo benchmark 中驗證過的工程分析假設。

或明確指定 profile：

```bash
python3 scripts/run_release_batch.py \
  --profile config/parity_fit_profile.release.json
```

保留的 split-workaround reference profile：

```bash
python3 scripts/run_release_batch.py \
  --profile config/recommended_profile.release.json
```

experimental shape profile：

```bash
python3 scripts/run_release_batch.py \
  --profile config/experimental_shape_profile.release.json
```

`Gamma = 0.5` literal-analysis hypothesis profile：

```bash
python3 scripts/run_release_batch.py \
  --profile config/imatest_parity_profile.release.json
```

`Gamma = 0.5` literal-analysis plus sensor-compensation follow-up：

```bash
python3 scripts/run_release_batch.py \
  --profile config/imatest_parity_sensor_comp_profile.release.json
```

`Gamma = 0.5` literal-analysis plus sensor-compensation and toe-linearization follow-up：

```bash
python3 scripts/run_release_batch.py \
  --profile config/imatest_parity_sensor_comp_toe_profile.release.json
```

舊的 linear/gray 版本如果要保留做比較，請改用：

```bash
python3 scripts/run_release_batch.py \
  --profile config/legacy_linear_profile.release.json
```

## 輸出

- 預設輸出到：
  - `results/parity_fit/`
  - 或 `results/experimental_shape/`
- 每個 `.raw` 會對應一個 Imatest 風格的：
  - `Results/<raw_stem>_R_Random.csv`
- 另外會產生：
  - `summary.json`

## 注意

- 這個 release 會直接呼叫 `algo.dead_leaves` 核心函式做分析
- profile 裡的路徑都寫成 release root 相對路徑，方便整包移動
- 目前有六類 profile：
  - `parity_fit_profile.release.json`
    - 現在的 release 預設與 primary target profile
    - 報告欄位對標 golden sample：`Gamma=0.5`, `Color channel=R`
    - 分析路徑使用 `analysis_gamma=1.0 + demosaic_red + frequency_scale=1.17`
    - issue `#18` 在不改動這條 parity-fit PSD/MTF baseline 的前提下，加入 `5.5" Phone viewing_distance_cm = 25.55` 的 preset override
    - 這樣可以把 `Phone` preset 拉回到比舊 baseline 更接近 CSV 的區間，同時保留 Monitor/UHDTV/print 的既有改善
  - `recommended_profile.release.json`
    - 保留的 split-workaround reference profile
    - 不再是 primary target profile
    - 仍使用 `analysis_gamma=1.0 + demosaic_red`
    - 但它依賴較舊的 `texture_support_scale` workaround 路徑
  - `imatest_parity_profile.release.json`
    - literal Gamma-hypothesis profile
    - 報告欄位與分析路徑都使用 `gamma=0.5 + demosaic_red`
    - 這個 profile 對應的是目前真正要擬合的 observable target conditions
    - 但它同時也只是目前一個已測試過的 literal-Gamma hypothesis，不代表 `Gamma = 0.5` 的內部意義已被證實
    - `2026-04-08` 的 parity re-fit note 已確認：
      - 現有 shape correction reuse 沒有 material improvement
      - 直接改用觀測 ROI 反而更差
    - 因此在後續擬合真正改善前，這個 profile 目前仍應視為 reference-only hypothesis
  - `imatest_parity_sensor_comp_profile.release.json`
    - issue `#29` 的第一個 source-backed compensation follow-up profile
    - 保留 literal observable-parity 路徑：`gamma=0.5 + demosaic_red`
    - 額外加上一個簡化的 `sensor_aperture_sinc` compensation
    - 目前 benchmark 顯示它能改善 literal parity 的 MTF residual 與 curve MAE
    - 但它還沒有改善整體 preset Acutance / Quality Loss，所以仍應視為 reference-only experiment
  - `imatest_parity_sensor_comp_toe_profile.release.json`
    - issue `#29` 的第二個 multi-family follow-up profile
    - 在 literal parity + sensor compensation 之上，再加入 `toe_power` 線性化 proxy
    - 目前 benchmark 顯示它能把 literal parity 的 `curve_mae_mean` 與 `overall_quality_loss_mae_mean` 再往前推進
    - 但 focus preset Acutance MAE 仍未整體改善，因此仍應視為 reference-only experiment
  - `legacy_linear_profile.release.json`
    - 舊的 linear/gray baseline，保留做比較
- `Gamma, 0.5` 這個報告欄位目前屬於 observable target condition。
- 但現有 sample 與整批 benchmark 都顯示，若把 analysis gamma 也直接硬設成 `0.5`，
  `MTF / Acutance` 會整體失配很多。
- `parity_fit_profile.release.json` 已經是目前最好的整體 release profile，
  現在則另外帶入 issue `#18` 的 Phone-only 幾何修正，而不是回頭改壞整條 parity-fit 主線。
