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

- `Color channel = R` 必須保留
- `Gamma = 0.5` 是 golden sample 中可直接觀察到的條件
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

- [algo/README.md](/Users/kevinhuang/work/acutance/algo/README.md)
  - 演算法原型、數學流程、校準與 benchmark 記錄
- [release/deadleaf_13b10_release/README.md](/Users/kevinhuang/work/acutance/release/deadleaf_13b10_release/README.md)
  - 可交付的 release 包與批次執行方式
