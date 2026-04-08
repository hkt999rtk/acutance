# Dead Leaves / Acutance 原型

這個目錄包含一套純 Python 原型，用來在不依賴 Imatest 的前提下，
重建 `Random / Dead Leaves` 報告中的核心數值與流程。

在看這份 README 前，先看 canonical observable target：

- [../docs/observable_target_from_golden_samples.md](../docs/observable_target_from_golden_samples.md)
- [../docs/gamma_0_5_hypothesis_matrix.md](../docs/gamma_0_5_hypothesis_matrix.md)

這份 README 會討論目前的模型與校準結論，但其中凡是沒有直接出現在 golden CSV 的內容，
都應視為工程推論或暫時假設，而不是 Imatest 已明示的內部條件。

整體設計刻意拆成兩層：

- `raw -> ROI -> PSD -> MTF`
- `MTF -> Acutance / CPIQ 衍生指標`

## 目標

針對與現有資料集相同的 `.raw` 輸入，產生可重複、可比對的輸出，
並盡量貼近既有 Imatest 報告：

- crop 範圍
- 徑向 PSD
- noise PSD
- signal PSD
- `MTF` / `MTF w/noise`
- `MTF20 / MTF30 / MTF50 / MTF70`
- 由 MTF 推得的 `Acutance`

## 使用的學理

這個原型只使用公開公式與可查證的做法，不呼叫任何 Imatest API：

- Dead-leaves texture SFR 由徑向 PSD 比值推得
- noise-corrected SFR 由 `sqrt((PSD_signal+noise - PSD_noise) / PSD_ideal)` 推得
- Acutance 依 CPIQ 形式的積分定義計算

目前的 Acutance 實作使用：

```text
Acutance = ∫ SFR(v) * CSF(v) dv / ∫ CSF(v) dv
CSF(v) = 75 * v^0.8 * exp(-0.2 v) / 34.05
```

其中 `v` 的單位是 cycles/degree。

對 dead-leaves 的 ideal PSD，目前支援三種模式：

- `quadratic_log`
  依公開 dead-leaves 文獻，以 `ln(f)` 的二次模型估計 ideal PSD
- `power_law`
  簡化版 `1 / f^p`
- `calibrated_log`
  由既有 Imatest CSV 反推，再擬合成 dataset/profile 專用的 empirical 模型

## 目前已實作

- 16-bit raw 載入
- 中央紋理區 ROI 偵測
- 背景 noise patch 擷取
- 徑向 PSD 估計
- dead-leaves MTF 估計
- 第一個下降分支的 threshold 指標讀值
- Acutance 計算
- 既有 Imatest CSV 解析與比對
- Bayer pattern / Bayer mode 支援
- raw 線性化參數控制
- empirical ideal PSD 校準
- empirical frequency-axis scaling 校準
- 參考 Imatest 頻率格點的 `reference bins`
  現在使用與 CSV 一致的 64 點中心頻率
- 固定 ROI 尺寸覆寫
- 紋理支撐區估測細節輸出
  包含 `bbox / component_area_px / border_margin_px / center_offset_px / aspect_ratio`
- 實驗性的 ROI center fine search
  規則是先保留近似最大支撐區面積，再優先選邊界餘量較大、中心偏移較小的裁切
- 可配置的 threshold readout policy
  支援 `readout_smoothing_window` 與 `readout_interpolation`
- `unnormalized MTF` 與 `normalized MTF` 分離輸出
- `Acutance curve` 輸出
  目前會輸出 `40 cm / 1..100 cm` 的完整曲線
- `Acutance preset` 輸出
  目前已接上 `Computer Monitor / 5.5" Phone / UHDTV / Small Print / Large Print`
  並已針對目前資料集把 `5.5" Phone` 的 viewing geometry 校準到較接近 CSV

預設分析使用線性 raw 域，也就是 `gamma=1.0`。
這比先套 display gamma 再做 Fourier 分析更符合 dead-leaves / PSD 的學理假設。

另外，針對這批資料已額外驗證一個重要差異：

- golden sample 報告中的 `Gamma, 0.5`
- 不應直接等同於本原型分析前處理的 `gamma`

在 `demosaic_red` 條件下，若把分析 gamma 也硬設成 `0.5`，
整批 40 份資料的 `curve_mae_mean` 會惡化到約 `0.131`；
而採用 `analysis gamma = 1.0`、但在報告層仍輸出 `Gamma = 0.5`，
整批 `curve_mae_mean` 可回到約 `0.0469`。

這表示目前較合理的工程做法是把：

- `analysis pipeline`
- `report metadata`

分開處理。

## 尚未完全對齊 Imatest 的部分

目前還沒有保證和 Imatest 完全一致，尤其以下幾點仍可能造成差距：

- CPIQ 顯示情境 preset
  例如 `Computer Monitor`、`5.5" Phone`、`UHDTV`、`Small Print`
- 實體 chart 的精確 ideal PSD
  目前已能用 empirical calibration 逼近，但仍不是物理 chart 的完整顯式模型
- Imatest 內部的 ROI policy
  目前可用自動 ROI，也可覆寫固定尺寸，但不保證與 Imatest 完全同一套規則
- frequency mapping 的內部定義
  目前 `texture_support_scale` 可以用「crop 支撐尺寸 / 有效紋理支撐尺寸」來解釋
  但和 Imatest 完全一致的底層定義仍未完全反推
- 特定 CFA / color channel 的內部處理細節
  目前資料中 CSV 全部觀測到 `Color channel, R`，但 Imatest 的最終 channel pipeline
  仍可能有未完全重現之處

## 目前已驗證出的校準結論

對 `20260318_deadleaf_13b10` 這批資料，目前驗證結果如下：

- Bayer pattern 不是主要誤差來源
- noise subtraction 對 `MTF20 / 30 / 50` 的影響很小
- `ideal PSD calibration` 是必要的
- `reference bins` 能讓頻率取樣更貼近 Imatest CSV
- 全域 `frequency_scale` 是目前最有效的補償量之一

目前觀察到的 empirical scale：

- 只看 `output2_Bmodel` 的 20 份 `R_Random.csv`，最佳 `frequency_scale` 約為 `1.095`
- 把整包 `20260318_deadleaf_13b10` 的 40 份 `R_Random.csv` 一起納入，最佳 `frequency_scale` 約為 `1.135`

對單張 sample 而言，使用下列組合：

- `ideal_psd_mode = calibrated_log`
- `reference_bins = true`
- `roi_width = 1655`
- `roi_height = 1673`
- `frequency_scale = 1.12`

可以得到大致如下的結果：

- `MTF20 = 0.2071`，對照 reference `0.2008`
- `MTF30 = 0.1697`，對照 reference `0.1662`
- `MTF50 = 0.1135`，對照 reference `0.1199`

這表示目前 `MTF20 / MTF30` 已相當接近，`MTF50` 仍有小幅差距。
到目前為止，剩餘誤差更像是 `frequency mapping / ROI policy / readout policy`
的組合，而不是 Bayer、noise 或簡單 gamma 問題。

另外，這一輪也驗證了另一件事：

- 以「最大化完整紋理連通區」為原則做 ROI center fine search 是可解釋的
- 但在目前這批資料上，這個 fine search 並沒有穩定優於既有 seed ROI
- 因此它目前仍維持為實驗選項，不建議當成預設流程

對 `MTF50` 的 readout policy 也已做整批 benchmark：

- baseline: `window=1, interpolation=linear`
  - `MAE50 = 0.00624`
  - `MAE30 = 0.02695`
  - `MAE20 = 0.01148`
- `window=7, interpolation=linear`
  - `MAE50 = 0.00588`
  - `MAE30 = 0.01150`
  - `MAE20 = 0.01816`

這代表 smoothing 確實能讓 `MTF50` 再靠近一點，但改善幅度很有限，
而且會明顯拉壞 `MTF20`。因此目前判斷：

- `MTF50` 剩餘誤差不主要來自 threshold interpolation 公式
- readout policy 可以當成研究選項，但不建議當成預設修正手段
- `Acutance` 主流程已串通
  目前會明確使用 `unnormalized MTF`
  並且先用低頻 anchor 估計 `DC = 1` 的 MTF 基準，再保留 sharpening peak

對 `Acutance` 的主流程，最新一輪的可解釋定義是：

1. `Acutance` 使用 `unnormalized MTF`
2. 但 dead-leaves PSD 比值本身不直接提供 `f=0` 的 DC 錨點
3. 因此先用低頻穩定區 `0.017 ~ 0.035 c/p` 的平均值估計 `DC = 1`
4. 再保留該曲線中高頻因 sharpening 帶來的 peak
5. `Acutance` 的分母使用完整 `∫ CSF(v) dv`，而不是截斷到相機 Nyquist

另外要注意，這裡的角頻率換算只依賴 `viewing_distance_cm / picture_height_cm`。
也就是說，對 preset 的校準，本質上是在校準「觀看放大倍率」，
而不是兩個幾何參數各自獨立的絕對值。程式中仍然保留
`picture_height_cm` 與 `viewing_distance_cm`，只是用一組 canonical pair
來承載這個 ratio，方便和實際裝置情境對應。

這樣做之後，整批 36 份資料的誤差顯著下降：

- `curve_mae_mean = 0.0354`
- `Computer Monitor Acutance MAE = 0.0171`
- `UHDTV Display Acutance MAE = 0.0139`
- `Large Print Acutance MAE = 0.0324`
- `Small Print Acutance MAE = 0.0337`
- `5.5" Phone Display Acutance MAE = 0.0077`

這表示：

- `Acutance curve` 已經進入接近可用的狀態
- 五個 preset 都已進入可用範圍
- `Phone` preset 的主要差異來自 viewing geometry，而不是 Acutance 積分公式本身
- 對 `20260318_deadleaf_13b10` 這批資料，將 `5.5" Phone` 校準為
  `picture_height_cm = 5.1`、`viewing_distance_cm = 29.5`
  後，整批 MAE 可降到約 `0.0077`
- 其餘 preset 也可以用 viewing magnification 來解釋：
  `Computer Monitor ≈ 1.31x`、`UHDTV ≈ 2.268x`、
  `Small Print ≈ 2.586x`、`Large Print ≈ 2.131x`

進一步把 40 份整批資料納入，並對 `Small Print / Large Print`
加入一個可解釋的 print-system display MTF，再把 `Acutance` 路徑的 noise PSD
改成依 `high_frequency_noise_share` 自適應調整後，目前推薦 profile 的整體結果是：

- `curve_mae_mean = 0.03197`
- `Computer Monitor Acutance MAE = 0.01916`
- `5.5" Phone Display Acutance MAE = 0.00873`
- `UHDTV Display Acutance MAE = 0.01286`
- `Small Print Acutance MAE = 0.02852`
- `Large Print Acutance MAE = 0.02773`

這裡的 print-system MTF 使用 `ideal low-pass`：

```text
MTF_display(v) = 1,  v <= f_c
MTF_display(v) = 0,  v > f_c
```

這和 Imatest 文件中對 display resize 的 first-order low-pass 描述更接近。
對目前這批資料，`Small Print` 與 `Large Print` 都以
`cutoff = 18 cycles/degree` 最接近 Imatest 報告。

另外，目前推薦的 `Acutance` noise 補償不再是固定常數，而是：

```text
noise_share_hf = mean( PSD_noise / PSD_signal+noise ),  f in [0.36, 0.5] c/p
acutance_noise_scale = clip(
    521.0818 * noise_share_hf^2 - 26.6291 * noise_share_hf + 1.5962,
    1.0,
    3.5
)
```

這個模型的解釋是：

- 若影像在高頻端看起來更接近 noise-dominated，則 `Acutance` 路徑應採用更保守的 noise subtraction
- 若高頻 noise share 較低，則保留較小的補償，避免過度拉低 `Computer Monitor`
- 這條補償只作用在 `mtf_for_acutance`
- `MTF20 / MTF30 / MTF50` 的主讀值路徑仍維持 `noise_psd_scale = 1.0`

## 實務建議

如果目標是先建立一個可用、可批次跑、可比對的流程，建議先採用 profile 化策略：

1. 以 dataset 或 chart 為單位建立 `ideal PSD calibration`
2. 固定 `reference bins`
3. 固定一組 ROI policy
4. 固定一個 empirical `frequency_scale`
5. 在這個基礎上再往 `Acutance / CPIQ preset` 推進

## 建議 Profile

目前針對 [20260318_deadleaf_13b10](/Users/kevinhuang/work/acutance/20260318_deadleaf_13b10)
收斂出的建議參數已整理在：

- [deadleaf_13b10_recommended_profile.json](/Users/kevinhuang/work/acutance/algo/deadleaf_13b10_recommended_profile.json)

核心建議如下：

**Shared**
- `width = 4032`
- `height = 3024`
- `gamma = 1.0`
- `ideal_psd_mode = calibrated_log`
- `calibration_file = deadleaf_13b10_psd_calibration.json`
- `reference_bins = true`
- `roi_width = 1655`
- `roi_height = 1673`

**MTF**
- `normalization_band = 0.01 ~ 0.03`
- `normalization_mode = max`
- `readout_smoothing_window = 1`
- `readout_interpolation = linear`
- `texture_support_scale = true`
- `high_frequency_guard = off`

**Acutance**
- `acutance_band = 0.017 ~ 0.035`
- `acutance_band_mode = mean`
- `acutance_noise_scale_mode = high_frequency_noise_share_quadratic`
- `acutance_noise_share_band = 0.36 ~ 0.5`
- `acutance_noise_share_scale_coefficients = [521.0818, -26.6291, 1.5962]`
- `high_frequency_guard_start_cpp = 0.36`
- `high_frequency_guard_stop_cpp = 0.5`
- `Small Print display_mtf_model = ideal_lowpass`
- `Small Print display_mtf_cutoff_cpd = 18`
- `Large Print display_mtf_model = ideal_lowpass`
- `Large Print display_mtf_cutoff_cpd = 18`
- `quality_loss_mode = om_quadratic_global`
- `quality_loss_om_ceiling = 0.8851`

這裡要特別注意：

- `high_frequency_guard` 是 `Acutance-specific` 修正
- 它應該只影響 `mtf_for_acutance`
- 不應該用來調 `MTF20 / MTF30 / MTF50`

對目前 40 份資料來說，`guard_start_cpp = 0.36` 是比較平衡的折衷點：

- 比 baseline 明顯改善 `Acutance curve`
- 不會改變 `MTF50`
- 不像 `0.28` 那樣過度偏向 curve-only optimum
- 也不像 `0.42` 那樣雖然 preset 平均較好，但 curve 回升較多

`Quality Loss` 目前也已經串上，使用的可解釋形式是：

```text
OM = max(0, 0.8851 - Acutance)
QualityLoss ≈ 64.9925 * OM^2 + 9.3797 * OM + 0.7223
```

這裡的 `0.8851` 來自 Imatest 文件對 CPIQ objective metric 的說明；
二次式則是以這批 40 份資料的 `Acutance / Quality Loss` 對照擬合出的全域近似。

用這個全域公式，在目前推薦 profile 下的 40 份整批誤差是：

- `Phone Quality Loss MAE = 0.116`
- `UHDTV Quality Loss MAE = 0.682`
- `Computer Monitor Quality Loss MAE = 1.410`
- `Small Print Quality Loss MAE = 1.591`
- `Large Print Quality Loss MAE = 1.707`
- `overall_mae_mean = 1.101`

若改用 experimental shape-correction profile：

- `Phone Quality Loss MAE = 0.116`
- `UHDTV Quality Loss MAE = 0.629`
- `Computer Monitor Quality Loss MAE = 1.333`
- `Small Print Quality Loss MAE = 1.572`
- `Large Print Quality Loss MAE = 1.684`
- `overall_mae_mean = 1.066`

也就是說，experimental profile 不只改善 `Acutance`，也會連帶改善 `Quality Loss`；
但它目前仍保留為 experimental，因為 `ori` 這組的 `curve` 還有很小的退步。

另外也做了上限檢查：

- 若固定 `OM ceiling = 0.8851`
- 但改用「我們目前估到的 Acutance」重新擬合同一條全域二次式
- 則 `overall_mae_mean` 可降到約 `0.939`

這表示 `Quality Loss` 映射本身不是完全沒有誤差，但主瓶頸仍然是前面的 `Acutance` 誤差。
如果目標是把整份 report 再往 Imatest 靠近，下一步仍應優先追 `Acutance / MTF / PSD`，
而不是先把 `Quality Loss` 做 profile-specific 補償。

如果目標是再往 Imatest 更靠近，下一步優先順序建議是：

1. 追 `signal PSD / ideal PSD` 在中高頻段的殘差來源
2. 檢查各 preset 是否還需要額外的 display low-pass / px/cm 模型
3. 集中處理 `ori` 這組為什麼比 model-output 更差

另外，現在也有一個獨立的 experimental shape-correction profile：

- [deadleaf_13b10_experimental_shape_profile.json](/Users/kevinhuang/work/acutance/algo/deadleaf_13b10_experimental_shape_profile.json)

它不是直接改 PSD，而是在 `MTF / mtf_for_acutance` 上套一個受約束的、由
`high_frequency_noise_share` gating 的 correction。對 40 份整批 benchmark，
它比目前 base profile 更進一步：

- `MTF20 MAE = 0.01479`
- `MTF30 MAE = 0.02971`
- `MTF50 MAE = 0.01878`
- `curve_mae_mean = 0.03171`
- `Computer Monitor Acutance MAE = 0.01814`
- `preset_mae_mean = 0.01893`
- `Quality Loss overall_mae_mean = 1.066`

這條 correction 的數學形式是：

```text
gate = clip((share_hi - noise_share_hf) / (share_hi - share_lo), 0, 1)
correction = exp(gain * gate * shape(f))
```

其中 `shape(f)` 由兩個 cosine bump 組成：

- 中頻 `0.095 ~ 0.19 c/p` 做小幅 boost
- 高頻 `0.36 ~ 0.49 c/p` 做較弱的 attenuation

目前它先保留成 experimental profile，而不直接覆蓋 base profile，
因為它屬於 post-MTF correction，而且 `ori` 子集的 curve 仍有很小的退步。

我也做了更小的 local sweep，試過降低 `gain`、縮窄 `share_gate`、以及減弱高頻 attenuation。
結果是：

- `current-exp` 仍是整體最佳
- 低 gain 版本能把 `ori curve` 的退步縮小一點
- 但同時會讓 `overall curve / Monitor / preset_mae_mean` 一起變差

所以目前 experimental profile 的參數不再往下改，除非之後找到能在 `PSD` 層解決 `ori` 殘差的更底層方法。

## 主要工具

- [cli.py](/Users/kevinhuang/work/acutance/algo/cli.py)
  主分析 CLI
- [dead_leaves.py](/Users/kevinhuang/work/acutance/algo/dead_leaves.py)
  核心演算法
- [calibrate_bayer.py](/Users/kevinhuang/work/acutance/algo/calibrate_bayer.py)
  比較 Bayer pattern / Bayer mode
- [calibrate_psd.py](/Users/kevinhuang/work/acutance/algo/calibrate_psd.py)
  擬合 ideal PSD calibration
- [calibrate_linearization.py](/Users/kevinhuang/work/acutance/algo/calibrate_linearization.py)
  掃描 raw 線性化參數
- [calibrate_frequency_scale.py](/Users/kevinhuang/work/acutance/algo/calibrate_frequency_scale.py)
  擬合全域 frequency scale
- [calibrate_readout.py](/Users/kevinhuang/work/acutance/algo/calibrate_readout.py)
  比較 smoothing / interpolation 對 `MTF20 / 30 / 50` 誤差的影響
- [calibrate_acutance.py](/Users/kevinhuang/work/acutance/algo/calibrate_acutance.py)
  比較 `Acutance curve` 與 preset 的整批誤差
- [analyze_mtf_residuals.py](/Users/kevinhuang/work/acutance/algo/analyze_mtf_residuals.py)
  分析 `MTF / signal PSD / ideal PSD` 的頻段殘差與 shape mismatch
- [deadleaf_13b10_psd_calibration.json](/Users/kevinhuang/work/acutance/algo/deadleaf_13b10_psd_calibration.json)
  目前這批資料的 empirical ideal PSD calibration
- [deadleaf_13b10_psd_calibration_cubic.json](/Users/kevinhuang/work/acutance/algo/deadleaf_13b10_psd_calibration_cubic.json)
  實驗性的三次式 ideal PSD calibration，用來研究中高頻殘差
- [deadleaf_13b10_psd_calibration_piecewise.json](/Users/kevinhuang/work/acutance/algo/deadleaf_13b10_psd_calibration_piecewise.json)
  自由度較高的 piecewise calibration，能改善 `MTF50`，但會拉壞整體 `Acutance`
- [deadleaf_13b10_psd_calibration_anchored_s018.json](/Users/kevinhuang/work/acutance/algo/deadleaf_13b10_psd_calibration_anchored_s018.json)
  受約束的高頻 residual correction 範例，保留可解釋性，但目前收益有限

## 中高頻殘差追查結論

目前對 `MTF / PSD` 的殘差追查有六個明確結論：

1. `reference bins` 必須和 Imatest CSV 完全一致
   先前用 `np.arange(0.002, 0.4981, 0.0079)` 會少掉最後一格，且中心頻率會略偏。
   現在已統一改成固定 64 點的 `IMATEST_REFERENCE_BINS`。

2. `PSD` 的絕對量級和 Imatest 不同，但這不是目前最該修的點
   比較整批資料後可看出，絕對 `signal PSD / noise PSD` 的尺度差異很大，
   更像 FFT/window normalization 定義不同；真正影響 `MTF20 / 30 / 50`
   的，是 `signal PSD / ideal PSD` 的 shape mismatch。

3. 三次式 `ideal PSD` 可以改善 `MTF50`，但會拖壞整體 `Acutance`
   以 `log(PSD)` 對 `log(f)` 的三次式 calibration 來看，
   `MTF50` 的 batch MAE 可從約 `0.0188` 降到 `0.0061`；
   但 `Acutance curve` 和 preset MAE 會整體變差。
   因此目前預設仍維持 quadratic calibration，cubic calibration 只保留作研究用途。

4. 自由 piecewise 比 quadratic 更會動到 `MTF50`，但整體仍不如 current profile
   目前的 piecewise calibration 會把 `MTF50` MAE 從約 `0.0253` 降到 `0.0238`，
   但同時讓：
   - `Acutance curve MAE`: `0.0343 -> 0.0360`
   - `preset MAE mean`: `0.0243 -> 0.0287`

   也就是說，它確實碰到了中高頻 shape，但自由度還是太高，會把後段 `Acutance`
   一起拉走。因此目前也不作為預設 calibration。

5. 高頻 guard 適合只接在 `Acutance` 路徑，不適合動 `MTF20 / 30 / 50`
   目前已實作 `high_frequency_guard_start_cpp`，以 cosine taper 的方式，
   只在 `mtf_for_acutance` 對應的高頻尾端降低權重。
   這樣做有兩個好處：
   - `MTF50` 不會改變
   - `Acutance curve` 會明顯改善

   以 `20260318_deadleaf_13b10` 的 40 份驗證來看：
   - baseline: `curve_mae_mean = 0.0445`
   - `guard_start = 0.28`: `curve_mae_mean = 0.0329`
   - `guard_start = 0.42`: `preset_mae_mean = 0.0243`

   如果以 `curve + Computer Monitor` 的折衷來看，
   `guard_start ≈ 0.36 c/p` 是比較平衡的點。
   目前程式預設仍維持不開 guard，避免在不同 target 上過度先驗化；
   但對 Acutance 專用 profile，`0.36 ~ 0.42 c/p` 是合理的候選範圍。

6. 受約束的 anchored high-frequency correction 比自由 piecewise 更可解釋，但目前改善幅度太小
   `anchored_high_frequency` 的做法是：
   - 保留同一條 quadratic `log(PSD)` 當基線
   - 只在 `split_cpp` 以上擬合 residual
   - residual 以 `Δlog(f)^2, Δlog(f)^3, ...` 為基底，因此 split 點自動滿足
     value / slope 連續
   - 對 `0.35 c/p` 以上的點降低 fitting 權重，避免 Nyquist 附近 alias/noise 主導

   這個方向在數學上比自由 piecewise 乾淨，但目前最佳候選只把：
   - `curve_mae`: `0.03432 -> 0.03425`
   - `preset_mae_mean`: `0.02430 -> 0.02430`
   - `MTF50 MAE`: 幾乎不變

   所以目前結論是：方向合理，但還不值得取代 current quadratic calibration。

7. `signal PSD` 的 mid-band correction 只適合當 `MTF` 研究選項，不適合目前的 Acutance profile
   目前以 `0.08 ~ 0.22 c/p` 的 smooth bump 測試過 `signal PSD` mid-band correction。
   它確實能改善：
   - `MTF20`
   - `MTF30`
   - `MTF50`

   例如 `gain = 0.10` 時：
   - `MTF20 MAE`: `0.02747 -> 0.02088`
   - `MTF30 MAE`: `0.04565 -> 0.04391`
   - `MTF50 MAE`: `0.02526 -> 0.02169`

   但同時會讓：
   - `curve_mae`: `0.03432 -> 0.03456`
   - `preset_mae_mean`: `0.02430 -> 0.02484`

   所以目前判定：這條路可以保留給 MTF-only profile，但不該放進目前的 Acutance 推薦設定。

8. `Small Print / Large Print` 的主要殘差，更像 display / print chain，而不是 camera MTF 本體
   目前觀察到 `Small Print` 與 `Large Print` 的 signed error 都偏正，
   也就是我們算出的 Acutance 系統性偏高。這代表比起再動相機端 `MTF / PSD`，
   更合理的修正是替這兩個 preset 補上一個 print-system low-pass。

   以 print-system MTF 的 shape sweep 來看：
   - baseline `preset_mae_mean = 0.02430`
   - Gaussian `c50 = 24` 可降到 `0.02089`
   - `ideal_lowpass cutoff = 18` 可再降到約 `0.02040`

   這是目前最有效、且物理上最可解釋的後續改善。

## CLI 範例

分析單一 raw：

```bash
python3 -m algo.cli analyze \
  /Users/kevinhuang/work/acutance/20260318_deadleaf_13b10/OV13B10_AI_NR_OV13B10_ori/OV13b10_AG1_ET40000_deadleaf_12M_1.raw \
  --width 4032 \
  --height 3024
```

對照既有 Imatest CSV：

```bash
python3 -m algo.cli analyze \
  /Users/kevinhuang/work/acutance/20260318_deadleaf_13b10/output2_Bmodel/OV13B10_AI_NR_OV13B10_20251205_v2_2650_ppqpkl_0.25/OV13b10_AG1_ET40000_deadleaf_12M_1_denoised.raw \
  --width 4032 \
  --height 3024 \
  --compare-csv \
  /Users/kevinhuang/work/acutance/20260318_deadleaf_13b10/output2_Bmodel/OV13B10_AI_NR_OV13B10_20251205_v2_2650_ppqpkl_0.25/Results/OV13b10_AG1_ET40000_deadleaf_12M_1_denoised_R_Random.csv
```

使用目前較接近 reference 的 profile 參數：

```bash
python3 -m algo.cli analyze \
  /Users/kevinhuang/work/acutance/20260318_deadleaf_13b10/output2_Bmodel/OV13B10_AI_NR_OV13B10_20251205_v2_2650_ppqpkl_0.25/OV13b10_AG1_ET40000_deadleaf_12M_1_denoised.raw \
  --width 4032 \
  --height 3024 \
  --ideal-psd-mode calibrated_log \
  --calibration-file /Users/kevinhuang/work/acutance/algo/deadleaf_13b10_psd_calibration.json \
  --reference-bins \
  --roi-width 1655 \
  --roi-height 1673 \
  --frequency-scale 1.12 \
  --compare-csv \
  /Users/kevinhuang/work/acutance/20260318_deadleaf_13b10/output2_Bmodel/OV13B10_AI_NR_OV13B10_20251205_v2_2650_ppqpkl_0.25/Results/OV13b10_AG1_ET40000_deadleaf_12M_1_denoised_R_Random.csv
```

使用可解釋的支撐區比例縮放：

```bash
python3 -m algo.cli analyze \
  /Users/kevinhuang/work/acutance/20260318_deadleaf_13b10/output2_Bmodel/OV13B10_AI_NR_OV13B10_20251205_v2_2650_ppqpkl_0.25/OV13b10_AG1_ET40000_deadleaf_12M_1_denoised.raw \
  --width 4032 \
  --height 3024 \
  --ideal-psd-mode calibrated_log \
  --calibration-file /Users/kevinhuang/work/acutance/algo/deadleaf_13b10_psd_calibration.json \
  --reference-bins \
  --roi-width 1655 \
  --roi-height 1673 \
  --texture-support-scale
```

若要試驗 ROI center fine search，可額外加上：

```bash
--refine-roi-center --roi-search-radius 12 --roi-search-step 2
```

但目前驗證下來，這個 fine search 尚未穩定優於未 fine-tune 的 seed ROI。

若要試驗不同的 readout policy，可額外加上：

```bash
--readout-smoothing-window 7 --readout-interpolation linear
```

若要批次 benchmark readout policy：

```bash
python3 -m algo.calibrate_readout \
  /Users/kevinhuang/work/acutance/20260318_deadleaf_13b10 \
  --calibration-file /Users/kevinhuang/work/acutance/algo/deadleaf_13b10_psd_calibration.json \
  --windows 1 5 7 \
  --interpolations linear log_frequency
```

若要批次 benchmark `Acutance curve` 與 preset：

```bash
python3 -m algo.calibrate_acutance \
  /Users/kevinhuang/work/acutance/20260318_deadleaf_13b10 \
  --calibration-file /Users/kevinhuang/work/acutance/algo/deadleaf_13b10_psd_calibration.json
```
