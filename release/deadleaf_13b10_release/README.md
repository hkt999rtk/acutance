# Deadleaf 13B10 Release

這個目錄是可獨立交付的 release 包，內容包含：

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
目前 release 文件需要先說清楚兩件事：

- golden sample / Imatest report 中可直接觀察到的欄位，包含 `Gamma = 0.5`、`Color channel = R`
- 但目前原型還沒把這條 full-parity pipeline 完整擬合好

因此目前 release 預設使用的是一個 interim workaround，將「分析參數」和「報告欄位」分開：

- `report gamma = 0.5`
- `report color channel = R`
- `analysis gamma = 1.0`
- `analysis bayer_mode = demosaic_red`

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

Imatest 輸入條件對標 profile：

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
    - 這只是目前的 interim workaround，方便先產生較穩定的結果
    - 不能把它視為最終 fitting target
  - `imatest_parity_profile.release.json`
    - full-parity profile
    - 報告欄位與分析路徑都使用 `gamma=0.5 + demosaic_red`
    - 這個 profile 才代表目前真正要擬合的 observable target
    - 目前 benchmark 顯示誤差顯著較大，因此仍待後續繼續擬合
  - `legacy_linear_profile.release.json`
    - 舊的 linear/gray baseline，保留做比較
- `Gamma, 0.5` 這個報告欄位目前屬於 observable target condition。
- 但現有 sample 與整批 benchmark 都顯示，若把 analysis gamma 也直接硬設成 `0.5`，
  `MTF / Acutance` 會整體失配很多。
- 這代表目前最缺的不是改文件或改欄位，而是把 full-parity pipeline 的 black box 繼續擬合下去。
