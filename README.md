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

## 目前重要結論

目前已經確認：

- `Color channel = R` 是 golden CSV 的可觀測欄位
- `Gamma = 0.5` 也是 golden CSV 的可觀測欄位
- 但 `Gamma = 0.5` 目前不能直接等同於分析前處理的 `gamma`

實際 benchmark 顯示：

- 若直接使用 full parity analysis：
  - `analysis gamma = 0.5`
  - `bayer_mode = demosaic_red`
  - 整體誤差會明顯惡化

- 目前較合理的工程做法是分離：
  - `analysis pipeline`
  - `report metadata`

也就是：

- 報告欄位仍可對標 Imatest sample
  - `Gamma = 0.5`
  - `Color channel = R`
- 但分析路徑目前以 benchmark 證據較支持的條件為主
  - `analysis_gamma = 1.0`
  - `bayer_mode = demosaic_red`

這表示這個專案現在的核心工作，不是再追報告文字表面一致，而是：

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
- [algo/README.md](/Users/kevinhuang/work/acutance/algo/README.md)
  - 演算法原型、數學流程、校準與 benchmark 記錄
- [release/deadleaf_13b10_release/README.md](/Users/kevinhuang/work/acutance/release/deadleaf_13b10_release/README.md)
  - 可交付的 release 包與批次執行方式
