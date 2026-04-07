# Acutance / Dead Leaves

這個專案的初衷是：

- 針對同一批 `dead leaves` 測試 `raw`
- 不依賴 Imatest
- 用 Python、可解釋的數學、以及公開可查的定義
- 重建 Imatest `Random / Dead Leaves` 報告中的核心輸出
- 最終對同樣的 input 產生相同或近似的 `Acutance`

## 核心原則

這個專案不是只做一個近似的 sharpness 指標，而是要在以下約束下擬合 Imatest 的 black box：

1. input 要對標 Imatest
- 包含 `gamma`
- 包含 `color channel`
- 包含分析口徑與前處理條件

2. output 也要對標 Imatest
- 輸出格式
- 欄位口徑
- `MTF / PSD / Acutance` 的結果定義

因此真正要重建的是這條流程：

`raw -> ROI -> PSD -> MTF -> Acutance`

## 目前重要結論

目前已經確認：

- `Color channel = R` 應該保留
- 但 Imatest sample 報告中的 `Gamma, 0.5`，不能直接等同於分析前處理的 `gamma`

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

- [algo/README.md](/Users/kevinhuang/work/acutance/algo/README.md)
  - 演算法原型、數學流程、校準與 benchmark 記錄
- [release/deadleaf_13b10_release/README.md](/Users/kevinhuang/work/acutance/release/deadleaf_13b10_release/README.md)
  - 可交付的 release 包與批次執行方式
