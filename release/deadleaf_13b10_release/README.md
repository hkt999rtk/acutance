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

這個預設模式只會直接產生分析結果，不做 regression comparison。
預設 profile 現在將「分析參數」和「報告欄位」分開：

- `report gamma = 0.5`
- `report color channel = R`
- `analysis gamma = 1.0`
- `analysis bayer_mode = demosaic_red`

其中前兩者是目前 golden CSV 可直接觀測到的 report fields；
後兩者則是目前 release 採用的工程分析假設，不是 golden sample 直接揭露的內部 black-box 條件。

或明確指定 profile：

```bash
python3 scripts/run_release_batch.py \
  --profile config/recommended_profile.release.json
```

experimental profile：

```bash
python3 scripts/run_release_batch.py \
  --profile config/experimental_shape_profile.release.json
```

`Gamma = 0.5` literal-analysis hypothesis profile：

```bash
python3 scripts/run_release_batch.py \
  --profile config/imatest_parity_profile.release.json
```

舊的 linear/gray 版本如果要保留做比較，請改用：

```bash
python3 scripts/run_release_batch.py \
  --profile config/legacy_linear_profile.release.json
```

## 輸出

- 預設輸出到：
  - `results/recommended/`
  - 或 `results/experimental_shape/`
- 每個 `.raw` 會對應一個 Imatest 風格的：
  - `Results/<raw_stem>_R_Random.csv`
- 另外會產生：
  - `summary.json`

## 注意

- 這個 release 會直接呼叫 `algo.dead_leaves` 核心函式做分析
- profile 裡的路徑都寫成 release root 相對路徑，方便整包移動
- 目前有三類 profile：
  - `recommended_profile.release.json`
    - 現在的 release 預設
    - 報告欄位對標你手上的 Imatest sample：`Gamma=0.5`, `Color channel=R`
    - 分析路徑使用 `analysis_gamma=1.0 + demosaic_red`
    - 這是目前根據 benchmark 證據較合理的設定
  - `imatest_parity_profile.release.json`
    - literal Gamma-hypothesis profile
    - 報告欄位與分析路徑都使用 `gamma=0.5 + demosaic_red`
    - 這代表一個已測試過的假設，不代表 `Gamma = 0.5` 的內部意義已被證實
    - 目前 benchmark 顯示誤差顯著較大，保留作對照
    - `2026-04-08` 的 parity re-fit note 已確認：
      - 現有 shape correction reuse 沒有 material improvement
      - 直接改用觀測 ROI 反而更差
      - 這個 profile 目前應視為 reference-only hypothesis
  - `legacy_linear_profile.release.json`
    - 舊的 linear/gray baseline，保留做比較
- `Gamma, 0.5` 這個報告欄位目前不應直接等同於分析線性化指數。
  現有 sample 與整批 benchmark 都顯示，若把分析 gamma 也硬設成 `0.5`，
  `MTF / Acutance` 會整體失配很多。
