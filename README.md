# Acutance / Dead Leaves

先看這份 canonical target 定義：

- [docs/observable_target_from_golden_samples.md](docs/observable_target_from_golden_samples.md)

這份文件明確區分：

- golden CSV 直接可觀測到的條件與輸出
- 尚未解開的 black-box latent variables
- 目前原型採用的工程假設

這個專案的初衷是：

- 針對同一批 `dead leaves` 測試 `raw`
- 不依賴 Imatest
- 用 Python、可解釋的數學、以及公開可查的定義
- 重建 Imatest `Random / Dead Leaves` 報告中的核心輸出
- 最終對同樣的 input 產生相同或近似的 `Acutance`

## 核心原則

這個專案不是只做一個近似的 sharpness 指標，而是要在以下約束下擬合 Imatest 的 black box：

1. input 要對標 Imatest
- 先對標 golden CSV 中直接可觀測到的欄位
- 例如 `Gamma`、`Color channel`、`Crop`、`L R T B`
- 但不要把未觀測到的內部前處理條件當成已知事實

2. output 也要對標 Imatest
- 輸出格式
- 欄位口徑
- `MTF / PSD / Acutance` 的結果定義

因此真正要重建的是這條流程：

`raw -> ROI -> PSD -> MTF -> Acutance`

## 擬合目標怎麼定義

這個專案的擬合目標，不是先由我們主觀指定某個內部參數，而是：

- 緊跟 golden sample / Imatest report 中可直接觀察到的 input 與 output
- 再反推中間看不到的 black box

目前從 golden sample 可直接觀察到的條件包括：

- `Gamma = 0.5`
- `Color channel = R`
- `Image pixels (WxH) = 4032 x 3024`
- `Crop`
- `L R T B`
- `Use unnormalized MTF for Acutance calculation`

因此：

- `Gamma 0.5`
- `Color channel R`

是目前已知、必須對標的 observable conditions。

## 目前重要結論

目前已經確認：

- `Color channel = R` 是 golden sample 中可直接觀察到、必須保留的條件
- `Gamma = 0.5` 也是 golden sample 中可直接觀察到的條件
- 但我們還**不能直接假設**報告欄位中的 `Gamma = 0.5` 就等於 black box 內部實際使用的 analysis gamma

實際 benchmark 顯示：

- 若直接使用 full parity analysis：
  - `analysis gamma = 0.5`
  - `bayer_mode = demosaic_red`
  - 整體誤差會明顯惡化

- 目前暫時存在一個 split workaround：
  - 報告欄位維持對標 Imatest sample
  - 但分析路徑會用 `analysis_gamma = 1.0`
- 這個 workaround 只能視為當前 release / 診斷用折衷
- 不能把它當成最終擬合目標

這表示這個專案現在的核心工作是：

- 在 Imatest 的 input / output 約束下
- 持續把中間的 Python black box 擬合得更接近它

## 目錄

- [docs/observable_target_from_golden_samples.md](docs/observable_target_from_golden_samples.md)
  - golden sample 的 canonical observable target 定義
- [docs/gamma_0_5_hypothesis_matrix.md](docs/gamma_0_5_hypothesis_matrix.md)
  - `Gamma = 0.5` 的假設矩陣與目前可排除的解讀
- [docs/dead_leaves_black_box_research.md](docs/dead_leaves_black_box_research.md)
  - Imatest / ISP / dead-leaves black-box 公式與變數盤點
- [docs/parity_refit_benchmarks_2026-04-08.md](docs/parity_refit_benchmarks_2026-04-08.md)
  - issue `#4` 的 parity re-fit benchmark 狀態、已驗證無效的修正方向、以及目前阻塞點
- [docs/parity_input_pipeline_candidates.md](docs/parity_input_pipeline_candidates.md)
  - issue `#10` 的 input-path benchmark、目前鎖定的 parity input pipeline、以及被排除的候選路徑
- [docs/parity_psd_mtf_refit.md](docs/parity_psd_mtf_refit.md)
  - issue `#11` 的 parity PSD/MTF refit、基線與新 profile 比較、以及後續 validation 邊界
- [docs/parity_acutance_quality_loss_validation.md](docs/parity_acutance_quality_loss_validation.md)
  - issue `#12` 的 Acutance / Quality Loss validation、整體改善、以及 `Phone` preset 殘餘回歸
- [release/deadleaf_13b10_release/README.md](/Users/kevinhuang/work/acutance/release/deadleaf_13b10_release/README.md)
  - issue `#13` 的 release-facing parity-fit profile、預設 release 執行入口、以及保留的 reference/diagnostic profiles
- [algo/README.md](/Users/kevinhuang/work/acutance/algo/README.md)
  - 演算法原型、數學流程、校準與 benchmark 記錄
  - 可交付的 release 包與批次執行方式
