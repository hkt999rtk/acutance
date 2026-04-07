# 實驗紀錄

這份文件只記錄 `deadleaf_13b10` 這批資料上，已經做過與尚未做的主要實驗，
目的是避免重複嘗試同一類方法。

## 目前推薦基線

- ideal PSD: [deadleaf_13b10_psd_calibration.json](/Users/kevinhuang/work/acutance/algo/deadleaf_13b10_psd_calibration.json)
- Acutance high-frequency guard: `start=0.36`, `stop=0.5`
- Acutance adaptive noise scale:
  - model: `high_frequency_noise_share_quadratic`
  - band: `0.36 ~ 0.5 c/p`
  - coefficients: `[521.0818, -26.6291, 1.5962]`
- print display MTF: `ideal_lowpass cutoff = 18 cpd` for both `Small Print` and `Large Print`
- 40 份整批結果：
  - `curve_mae = 0.03197`
  - `preset_mae_mean = 0.01940`
  - `mtf50_mae = 0.02526`

## 已做過

1. `Bayer pattern / Bayer mode`
- 結論：不是主誤差來源

2. ROI 偵測與 fixed ROI
- 結論：ROI 已接近 Imatest，不是目前主因

3. 全域 frequency scale
- 結論：可解釋版本已被 `texture_support_scale` 取代

4. readout smoothing / interpolation
- 結論：只會微調 `MTF50`，不是主因

5. cubic ideal PSD
- 檔案：[deadleaf_13b10_psd_calibration_cubic.json](/Users/kevinhuang/work/acutance/algo/deadleaf_13b10_psd_calibration_cubic.json)
- 結論：`MTF50` 變好，但 `Acutance` 明顯變差

6. free piecewise ideal PSD
- 檔案：[deadleaf_13b10_psd_calibration_piecewise.json](/Users/kevinhuang/work/acutance/algo/deadleaf_13b10_psd_calibration_piecewise.json)
- 結論：比 cubic 穩，但仍不如 current quadratic profile

7. anchored high-frequency ideal PSD residual
- 檔案：
  - [deadleaf_13b10_psd_calibration_anchored_s014.json](/Users/kevinhuang/work/acutance/algo/deadleaf_13b10_psd_calibration_anchored_s014.json)
  - [deadleaf_13b10_psd_calibration_anchored_s018.json](/Users/kevinhuang/work/acutance/algo/deadleaf_13b10_psd_calibration_anchored_s018.json)
  - [deadleaf_13b10_psd_calibration_anchored_s022.json](/Users/kevinhuang/work/acutance/algo/deadleaf_13b10_psd_calibration_anchored_s022.json)
- 結論：數學上比較乾淨，但目前改善太小，不值得取代基線

8. Acutance-specific high-frequency guard
- 結論：有效，且不會改動 `MTF20/30/50`
- 目前推薦：`start=0.36`, `stop=0.5`

9. `signal PSD` 的 mid-band correction
- 工具：[calibrate_signal_psd_correction.py](/Users/kevinhuang/work/acutance/algo/calibrate_signal_psd_correction.py)
- 結論：`gain ≈ 0.10` 可以改善 `MTF20/30/50`，但會讓 `Acutance curve / preset` 退步
- 判定：暫不採用，除非後續需要做 MTF-only profile

10. print display-MTF Gaussian c50
- 工具：[calibrate_print_display_mtf.py](/Users/kevinhuang/work/acutance/algo/calibrate_print_display_mtf.py)
- 結論：有效，且比 `signal PSD` mid-band correction 更符合最終目標
- 目前推薦：
  - 已被下一輪 `ideal_lowpass` 取代，不再是最新基線

11. colored / correlated noise PSD
- 工具：[calibrate_noise_psd_model.py](/Users/kevinhuang/work/acutance/algo/calibrate_noise_psd_model.py)
- 比較：
  - `empirical`
  - `colored_log_polynomial degree=2`
  - `colored_log_polynomial degree=3`
- 結論：幾乎沒有改善，`empirical` 仍是目前較好的基線

12. print display-MTF model shape
- 工具：[calibrate_print_display_shape.py](/Users/kevinhuang/work/acutance/algo/calibrate_print_display_shape.py)
- 比較：
  - `gaussian`
  - `exponential`
  - `lorentzian`
  - `ideal_lowpass`
- 結論：
  - `exponential / lorentzian` 都明顯過度抑制 print acutance
  - `gaussian` 已經不錯
  - `ideal_lowpass cutoff = 18 cpd` 再略優於 `gaussian c50 = 24 cpd`

13. Acutance-only conservative noise scaling
- 結論：有效，且不影響 `MTF20/30/50`
- 先前固定常數版本：
  - `noise_psd_scale_for_acutance = 2.5`
  - 40 份結果：`curve_mae = 0.03270`
- 目前推薦的自適應版本：
  - 根據 `0.36 ~ 0.5 c/p` 的 `high_frequency_noise_share`
  - 用二次式估計 `acutance_noise_scale`
  - 40 份結果：`curve_mae = 0.03197`
  - `Computer Monitor Acutance MAE = 0.01916`
  - `Phone = 0.00873`
  - `UHDTV = 0.01286`
  - `Small Print = 0.02852`
  - `Large Print = 0.02773`
- 備註：
  - 這個模型不依賴 `ori / A / B` 類別或檔名
  - 只使用影像本身量測到的高頻 noise share
  - `ori`、`Amodel`、`Bmodel` 三組都比固定 `2.5` 更好

14. PSD window / edge leakage
- 比較：
  - `Hann`
  - `Tukey alpha=0.25`
  - `Tukey alpha=0.5`
  - `no-window`
- 結論：
  - `no-window` 明顯更差，不採用
  - `Tukey alpha=0.25 / 0.5` 都不如目前的 `Hann`
  - 目前 `Hann` 仍是最佳窗函數，不建議再回頭重試這條方向

15. ROI crop detrend
- 比較：
  - `mean detrend`
  - `plane detrend`
- 結論：
  - `plane detrend` 有極小幅改善，但量級不到值得增加核心流程複雜度的程度
  - 目前仍維持 `mean detrend` 作為基線

16. Constrained smooth ratio correction
- 目的：
  - 針對平均 residual 觀察到的
    - `0.06 ~ 0.24 c/p` 偏低
    - `0.35 ~ 0.49 c/p` 偏高
    做平滑、受約束的 multiplicative correction
- 形式：
  - 中頻使用 cosine bump 做小幅 boost
  - 高頻使用另一個 cosine bump 做 mild attenuation
  - correction 在低頻維持接近 `1`
- 結果：
  - 確實可以同時改善 `curve`、`Computer Monitor`、`MTF30`、`MTF50`
  - 代表這條方向是有訊號的，不是雜訊
  - 但目前 sweep 的版本仍會把 `MTF20` 拉差
- 暫時結論：
  - 這條方向保留
  - 但在找到「不傷 `MTF20`」的頻帶與強度之前，不升級成推薦 profile

17. High-frequency-noise-share gated shape correction
- 形式：
  - 以目前最好的 constrained shape correction 為底：
    - 中頻 `0.095 ~ 0.19 c/p` 做小幅 boost
    - 高頻 `0.36 ~ 0.49 c/p` 做較弱的 attenuation
  - 再用 `high_frequency_noise_share` 做 gating：

```text
gate = clip((share_hi - noise_share_hf) / (share_hi - share_lo), 0, 1)
correction = exp(gain * gate * shape(f))
```

- 最佳實驗參數：
  - `gain = 0.035`
  - `share_gate_lo = 0.05`
  - `share_gate_hi = 0.08`
  - `mid = 0.095 / 0.145 / 0.19`
  - `high = 0.36 / 0.40 / 0.49`
  - `high_weight = 0.25`
- 40 份整批結果：
  - `MTF20 MAE = 0.01479`
  - `MTF30 MAE = 0.02971`
  - `MTF50 MAE = 0.01878`
  - `curve_mae = 0.03171`
  - `Computer Monitor Acutance MAE = 0.01814`
  - `preset_mae_mean = 0.01893`
- 對比目前推薦 profile：
  - `MTF20 / 30 / 50` 全部改善
  - `curve_mae` 改善
  - `Computer Monitor` 改善
  - `preset_mae_mean` 改善
- 分組觀察：
  - `Amodel`、`Bmodel` 都穩定改善
  - `ori` 的 `curve` 略退，但 `Monitor` 仍改善
- 局部參數收斂：
  - 額外試了 `gain = 0.025 / 0.03`
  - `share_gate_hi = 0.075`
  - `high_weight = 0.20`
  - 結果是 `ori curve` 的退步可以略微縮小，但 `overall curve / Monitor / preset_mae_mean` 都會回升
  - 目前沒有找到一組比 `current-exp` 更平衡的參數
- 結論：
  - 這是目前第一個同時改善多個主指標的 shape correction
  - 但因為它是 post-MTF correction，先保留成 experimental profile，不直接取代 base profile
  - 檔案：
    - [deadleaf_13b10_experimental_shape_profile.json](/Users/kevinhuang/work/acutance/algo/deadleaf_13b10_experimental_shape_profile.json)

18. Mid-deficit gated shape correction
- 背景：
  - `ori` 的 `mid_over_low_mean` 約 `0.577`
  - `Bmodel` 約 `0.422`
  - `Amodel` 約 `0.291`
  - 也就是 `ori` 的中頻並不缺，反而高於 model-output；這表示不該一律套用同一個 mid-band boost
- 形式：
  - 在既有 `high_frequency_noise_share` gate 之外
  - 再用 `mid_over_low = mean(MTF[0.095~0.19]) / mean(MTF[0.017~0.035])`
    作第二層 gate
  - 當 `mid_over_low` 已高時，降低 correction gain
- 測試過的 mid gate 範圍：
  - `midgate_a`: `lo=0.30`, `hi=0.55`
  - `midgate_b`: `lo=0.32`, `hi=0.50`
  - `midgate_c`: `lo=0.28`, `hi=0.52`
- 結果：
  - `midgate_a` 的 `overall curve = 0.03161`，比 `current-exp = 0.03171` 更好
  - 但 `overall Monitor = 0.01861`，比 `current-exp = 0.01814` 更差
  - `ori curve` 會回到 base profile 水準：
    - `0.05112 -> 0.05017`
- 結論：
  - 這條路是可解釋的，而且確實打到 `ori` regression 的根因
  - 但目前它是用 `Monitor` 的精度換 `ori curve`
  - 先記錄為下一輪可繼續收斂的方向，暫不納入 profile

19. Split mid-gate / high-attenuation correction
- 動機：
  - `ori` 的 regression 更像是 `mid boost` 不該套太多
  - 不是整個 correction 都該縮小
- 做法：
  - 保留既有 `high_frequency_noise_share` gate
  - `mid boost` 再額外乘上一個 `mid_deficit_gate`
  - 高頻 attenuation 維持原樣
- 定義：
  - `mid_over_low = mean(MTF[0.095~0.19]) / mean(MTF[0.017~0.035])`
  - `mid_deficit_gate = clip((hi - mid_over_low) / (hi - lo), 0, 1)`
- 候選結果：
  - `d_base (lo=0.35, hi=0.55, gain=0.035)`
    - `overall_curve = 0.03155`
    - `overall_monitor = 0.01854`
    - `overall_mean = 0.01892`
    - `overall_ql = 1.06909`
    - `ori_curve = 0.05011`
  - `d_hi060 (lo=0.35, hi=0.60, gain=0.035)`
    - `overall_curve = 0.03157`
    - `overall_monitor = 0.01847`
    - `overall_mean = 0.01892`
    - `overall_ql = 1.06856`
    - `ori_curve = 0.05023`
- 對比 `current-exp`：
  - `current-exp`
    - `overall_curve = 0.03171`
    - `overall_monitor = 0.01814`
    - `overall_mean = 0.01893`
    - `overall_ql = 1.06650`
    - `ori_curve = 0.05112`
- 結論：
  - split mid-gate 確實能把 `ori curve` 拉回來，且 `overall_curve` 還更低
  - 但 `Monitor` 與 `Quality Loss` 仍不如 `current-exp`
  - 目前最好的 split 版本是 `d_hi060`
  - 它可以作為「偏重 curve / ori 穩定性」的研究分支，但還不適合取代 `current-exp`

## 還沒做

1. 更完整的 correlated-noise model
- 目前 noise PSD 仍是 patch-based estimate，尚未引入 correlated noise / colored noise 假設

2. 非 Gaussian 的 display / print pipeline model
- `exponential / lorentzian` 已試過，效果比 Gaussian 差
- 仍未試更完整的 print chain，例如多段或 anisotropic model

3. `Quality Loss`
- 已重建全域版本：
  - `OM = max(0, 0.8851 - Acutance)`
  - `QualityLoss ≈ 64.9925 * OM^2 + 9.3797 * OM + 0.7223`
- 工具：[calibrate_quality_loss.py](/Users/kevinhuang/work/acutance/algo/calibrate_quality_loss.py)
- 目前用最新推薦 profile 的 `Acutance` 估值回推 `Quality Loss` 的 40 份誤差：
  - `Phone Quality Loss MAE = 0.116`
  - `UHDTV Quality Loss MAE = 0.682`
  - `Monitor Quality Loss MAE = 1.410`
  - `Small Print Quality Loss MAE = 1.591`
  - `Large Print Quality Loss MAE = 1.707`
  - `overall_mae_mean = 1.101`
- 再把 experimental shape-correction profile 接進去後：
  - `Phone Quality Loss MAE = 0.116`
  - `UHDTV Quality Loss MAE = 0.629`
  - `Monitor Quality Loss MAE = 1.333`
  - `Small Print Quality Loss MAE = 1.572`
  - `Large Print Quality Loss MAE = 1.684`
  - `overall_mae_mean = 1.066`
- 相對 base profile 的改善量：
  - `overall_mae_mean`: `-0.0347`
  - `Monitor`: `-0.0772`
  - `UHDTV`: `-0.0538`
  - `Small Print`: `-0.0191`
  - `Large Print`: `-0.0233`
  - `Phone`: 幾乎不變
- 上限檢查：
  - 若固定 `OM ceiling = 0.8851`，但改用「我們目前估到的 Acutance」重新擬合同一條全域二次式，
    整體 `overall_mae_mean` 可降到約 `0.939`
- 結論：
  - `Quality Loss` 映射本身不是完全沒有誤差，但主瓶頸仍然在前段 `Acutance`
  - experimental shape correction 會連帶改善 `Quality Loss`，表示它不是只對單一 preset overfit
  - 若目標是更接近 Imatest report，下一步優先順序仍應先追 `Acutance / MTF / PSD`
  - 若目標只是把 `Quality Loss` 更貼近目前資料集，可另外保留一個 profile-specific global quadratic 作為研究選項
