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
- [docs/parity_phone_preset_followup.md](docs/parity_phone_preset_followup.md)
  - issue `#18` 的 Phone preset follow-up、Phone-only 幾何修正、以及保留 parity-fit curve 的驗證
- [docs/amodel_gain_trend_experiment.md](docs/amodel_gain_trend_experiment.md)
  - issue `#20` 的 A-model gain-trend experiment、現有 release profiles 的趨勢比較、以及尚未解決的 gain-dependent mismatch
- [docs/imatest_parity_sensor_compensation_followup.md](docs/imatest_parity_sensor_compensation_followup.md)
  - issue `#29` 的第一個 source-backed sensor-compensation pass，顯示 literal parity 的 MTF / curve 可改善，但 end-to-end preset / Quality Loss 仍未完成
- [docs/imatest_parity_oecf_sensor_compensation_followup.md](docs/imatest_parity_oecf_sensor_compensation_followup.md)
  - issue `#29` 的第二個 multi-family follow-up，加入 toe-style OECF linearization 後，literal parity 的 curve 與 overall Quality Loss 都進一步改善，但 preset Acutance 仍未完全對齊
- [docs/imatest_parity_oetf_family_followup.md](docs/imatest_parity_oetf_family_followup.md)
  - issue `#29` 的第三個 linearization-family follow-up，比較標準 `sRGB / Rec.709` inverse-OETF 與 toe proxy，結果顯示標準 OETF 分支明顯較差，toe proxy 仍是目前較好的 OECF 近似方向
- [docs/imatest_parity_reference_refined_followup.md](docs/imatest_parity_reference_refined_followup.md)
  - issue `#29` 的第四個 registration follow-up，使用 reference-guided ROI refinement 後，toe-plus-sensor 分支在 curve、preset Acutance、與 overall Quality Loss 都有小幅進一步改善
- [docs/imatest_parity_reference_anchor_followup.md](docs/imatest_parity_reference_anchor_followup.md)
  - issue `#29` 的第五個 intrinsic/reference-family follow-up，使用 matched `ori` reference anchor 後，preset Acutance 與 overall Quality Loss 明顯改善，但 curve fidelity 反而變差，顯示這個 family 有潛力但目前仍過強
- [docs/imatest_parity_reference_anchor_ramped_followup.md](docs/imatest_parity_reference_anchor_ramped_followup.md)
  - issue `#29` 的第六個 reference-anchor follow-up，將 matched `ori` anchor 改成 half-strength ramp 後，大致收回 curve 損失，但 preset Acutance 與 overall Quality Loss 的改善也一起消失，排除了簡單頻率 ramp 就能解 trade-off 的假設
- [docs/imatest_parity_reference_anchor_acutance_only_followup.md](docs/imatest_parity_reference_anchor_acutance_only_followup.md)
  - issue `#29` 的第七個 reference-anchor follow-up，將 matched `ori` anchor 限定在 acutance path 後，保住了 reference-refined 分支的 reported MTF residual，同時保留 full anchor 的 preset / Quality Loss 改善，顯示剩餘 gap 更集中在 Acutance-side correction family
- [docs/imatest_parity_reference_anchor_acutance_only_strength_followup.md](docs/imatest_parity_reference_anchor_acutance_only_strength_followup.md)
  - issue `#29` 的第八個 acutance-side follow-up，將 `acutance_only` anchor 強度調到 `0.85` 後，Acutance curve residual 有小幅改善，同時仍保留大部分 preset / Quality Loss 改善，說明剩餘 miss 可在 acutance-side 再細化
- [docs/imatest_parity_reference_anchor_acutance_only_piecewise_followup.md](docs/imatest_parity_reference_anchor_acutance_only_piecewise_followup.md)
  - issue `#29` 的第九個 acutance-side follow-up，測試 low/high piecewise strength 後結果比 `0.85` scalar 更差，排除了最簡單的雙頻帶 shape 假設
- [docs/imatest_parity_reference_anchor_acutance_only_mid_dip_followup.md](docs/imatest_parity_reference_anchor_acutance_only_mid_dip_followup.md)
  - issue `#29` 的第十個 acutance-side follow-up，使用 mid-band dip strength curve 後，成為目前 acutance-only family 中最好的折衷分支，同時改善 preset / Quality Loss 並保留 fixed reported-MTF branch
- [docs/imatest_parity_reference_anchor_acutance_only_shoulder_trim_followup.md](docs/imatest_parity_reference_anchor_acutance_only_shoulder_trim_followup.md)
  - issue `#29` 的第十一個 acutance-side follow-up，驗證 mid-dip 周邊的 shoulder-trim strength curves 後都沒有超過目前 mid-dip 分支，顯示這個 local tuning neighborhood 已接近飽和
- [docs/imatest_parity_reference_anchor_acutance_curve_followup.md](docs/imatest_parity_reference_anchor_acutance_curve_followup.md)
  - issue `#29` 的第十二個 acutance-side follow-up，將 matched `ori` correction 直接移到 observable Acutance curve domain 後，幾乎收回剩餘 curve gap 並明顯改善 overall Quality Loss，但也重新帶回部分 Phone preset 誤差
- [docs/imatest_parity_reference_anchor_acutance_curve_fade_followup.md](docs/imatest_parity_reference_anchor_acutance_curve_fade_followup.md)
  - issue `#29` 的第十三個 acutance-side follow-up，驗證 direct Acutance-curve anchor 在 observable curve range 之外做 fade-out 後仍無法有效收回 Phone preset regression，排除了最直接的 boundary taper 解法
- [docs/imatest_parity_reference_anchor_acutance_curve_phoneaware_followup.md](docs/imatest_parity_reference_anchor_acutance_curve_phoneaware_followup.md)
  - issue `#29` 的第十四個 acutance-side follow-up，將 direct Acutance-curve anchor 只在 high-scale phone region 弱化後，同時保住大部分 curve gain 並明顯收回 Phone preset regression，成為目前最好的 overall compromise branch
- [docs/imatest_parity_reference_anchor_acutance_curve_preset_phoneaware_followup.md](docs/imatest_parity_reference_anchor_acutance_curve_preset_phoneaware_followup.md)
  - issue `#29` 的第十五個 acutance-side follow-up，將 phone-aware shaping 拆成 preset-only path 後，保留 direct Acutance-curve branch 的較強 curve fit，同時維持 phone-aware preset 改善，成為目前最好的 overall branch
- [docs/imatest_parity_reference_anchor_acutance_curve_preset_phoneaware_curve070_followup.md](docs/imatest_parity_reference_anchor_acutance_curve_preset_phoneaware_curve070_followup.md)
  - issue `#29` 的第十六個 acutance-side follow-up，驗證 preset-only 結構下 curve-side strength 的 bounded scalar search 後，將最佳 local scalar 從 `0.75` 收斂到 `0.70`，在不改變 preset 指標的前提下再縮小一點剩餘 curve gap
- [docs/imatest_parity_reference_anchor_acutance_curve_preset_phoneaware_curve_shape_gentle_down_followup.md](docs/imatest_parity_reference_anchor_acutance_curve_preset_phoneaware_curve_shape_gentle_down_followup.md)
  - issue `#29` 的第十七個 acutance-side follow-up，根據 curve-side residual 的 relative-scale 形狀改用 gentle-down strength curve，在不改變 preset 指標的前提下再進一步縮小剩餘 curve gap，成為目前最好的 overall branch
- [docs/imatest_parity_reference_anchor_acutance_curve_delta_power_followup.md](docs/imatest_parity_reference_anchor_acutance_curve_delta_power_followup.md)
  - issue `#29` 的第十八個 acutance-side follow-up，驗證 direct Acutance correction delta 做 nonlinear compression 後雖然能進一步改善 Phone preset，但會明顯拉壞 curve，因此屬於 bounded negative result
- [docs/imatest_parity_reference_anchor_acutance_curve_curve_clip_split_followup.md](docs/imatest_parity_reference_anchor_acutance_curve_curve_clip_split_followup.md)
  - issue `#29` 的第十九個 acutance-side follow-up，將 curve-side 與 preset-side 的 direct Acutance correction clip 分開後，能在完全不改變 preset 指標的前提下把 `curve_mae_mean` 進一步降到 `0.03806777`，成為目前最好的 overall branch
- [docs/imatest_parity_reference_anchor_acutance_curve_clip_shape_followup.md](docs/imatest_parity_reference_anchor_acutance_curve_clip_shape_followup.md)
  - issue `#29` 的第二十個 acutance-side follow-up，將 curve-side 的 direct Acutance correction `clip_hi` 做成 relative-scale shape 後，再把 `curve_mae_mean` 進一步降到 `0.03803290`，而 preset 與 Quality Loss 指標維持不變，成為目前最好的 overall branch
- [docs/imatest_parity_reference_anchor_acutance_curve_curve_delta_power_split_followup.md](docs/imatest_parity_reference_anchor_acutance_curve_curve_delta_power_split_followup.md)
  - issue `#29` 的第二十一個 acutance-side follow-up，將 nonlinear `delta_power` 分成 curve-side 與 preset-side 後，發現 curve-side `0.95` 可以把 `curve_mae_mean` 再降到 `0.03776865`，同時完全保留目前最好的 preset 與 Quality Loss 指標
- [docs/imatest_parity_reference_anchor_acutance_curve_preset_delta_power_split_followup.md](docs/imatest_parity_reference_anchor_acutance_curve_preset_delta_power_split_followup.md)
  - issue `#29` 的第二十二個 acutance-side follow-up，將 nonlinear `delta_power` 只加到 preset-side 後，發現 mild expansion `1.05` 可以在完全保留目前最佳 curve branch 的前提下，把 focus-preset Acutance、overall Quality Loss、與 Phone preset 再往前推一小步
- [docs/imatest_parity_reference_anchor_acutance_curve_preset_clip_shape_followup.md](docs/imatest_parity_reference_anchor_acutance_curve_preset_clip_shape_followup.md)
  - issue `#29` 的第二十三個 acutance-side follow-up，加入 preset-side `clip_hi` relative-scale shaping 並修正其套用路徑後，驗證 moderate phone-region clip relief (`1.12 / 1.14`) 對目前最佳分支完全沒有可觀察效果，說明剩餘 gap 不是被這個 local preset clip cap 限制
- [docs/imatest_parity_reference_anchor_acutance_curve_preset_delta_power_curve_followup.md](docs/imatest_parity_reference_anchor_acutance_curve_preset_delta_power_curve_followup.md)
  - issue `#29` 的第二十四個 acutance-side follow-up，將 preset-side nonlinear `delta_power` 做成 relative-scale shape 後，發現 phone-region `1.15` 可以在完全保留目前最佳 curve branch 的前提下，再把 focus-preset Acutance、overall Quality Loss、與 Phone preset 往前推一小步
- [docs/imatest_parity_reference_anchor_acutance_curve_preset_delta_power_curve_refine_followup.md](docs/imatest_parity_reference_anchor_acutance_curve_preset_delta_power_curve_refine_followup.md)
  - issue `#29` 的第二十五個 acutance-side follow-up，沿著同一個 preset-side `delta_power` curve neighborhood 再往上探到 phone-region `1.25` 後，發現它比 `1.15` 與 `1.20` 都更好，且仍完全保留目前最佳 curve branch
- [docs/imatest_parity_reference_anchor_acutance_curve_preset_delta_power_curve_extend_followup.md](docs/imatest_parity_reference_anchor_acutance_curve_preset_delta_power_curve_extend_followup.md)
  - issue `#29` 的第二十六個 acutance-side follow-up，沿著同一個 preset-side `delta_power` curve neighborhood 再往上延伸到 phone-region `1.35` 後，發現它比 `1.25` 與 `1.30` 都更好，且仍完全保留目前最佳 curve branch
- [docs/imatest_parity_reference_anchor_acutance_curve_preset_delta_power_curve_further_followup.md](docs/imatest_parity_reference_anchor_acutance_curve_preset_delta_power_curve_further_followup.md)
  - issue `#29` 的第二十七個 acutance-side follow-up，沿著同一個 preset-side `delta_power` curve neighborhood 再往上探到 phone-region `1.50` 後，發現它仍持續單調改善，表示這個局部 family 目前尚未飽和
- [docs/imatest_parity_reference_anchor_acutance_curve_preset_delta_power_curve_outer_followup.md](docs/imatest_parity_reference_anchor_acutance_curve_preset_delta_power_curve_outer_followup.md)
  - issue `#29` 的第二十八個 acutance-side follow-up，沿著同一個 preset-side `delta_power` curve neighborhood 再往外探到 phone-region `1.70` 後，發現它仍持續單調改善，表示這個 uniform phone-region local family 依然尚未飽和
- [docs/imatest_parity_reference_anchor_acutance_curve_preset_delta_power_curve_rollover_followup.md](docs/imatest_parity_reference_anchor_acutance_curve_preset_delta_power_curve_rollover_followup.md)
  - issue `#29` 的第二十九個 acutance-side follow-up，將同一個 uniform phone-region `delta_power` curve family 往外推到 `1.85 / 2.00 / 2.25` 後，第一次看見 bounded rollover，當前局部最佳點落在 `1.85`
- [docs/imatest_parity_reference_anchor_acutance_curve_preset_clip_lo_shape_followup.md](docs/imatest_parity_reference_anchor_acutance_curve_preset_clip_lo_shape_followup.md)
  - issue `#29` 的第三十個 acutance-side follow-up，加入 preset-side `clip_lo` relative-scale shape 支援並驗證 phone-region `0.98 / 1.00` low-floor probes 後，確認這個 family 在目前最佳 `phone185` 分支上是 exact no-op
- [docs/imatest_parity_reference_anchor_acutance_curve_preset_strength_curve_followup.md](docs/imatest_parity_reference_anchor_acutance_curve_preset_strength_curve_followup.md)
  - issue `#29` 的第三十一個 acutance-side follow-up，沿著目前 `phone185` 分支的 preset-side phone-region strength curve 做 bounded retune 後，確認這個 family 只會在 phone Acutance 與 phone Quality Loss 之間做小幅 trade，沒有超過目前最佳分支
- [docs/imatest_parity_reference_anchor_acutance_curve_preset_phone_display_mtf_followup.md](docs/imatest_parity_reference_anchor_acutance_curve_preset_phone_display_mtf_followup.md)
  - issue `#29` 的第三十二個 acutance-side follow-up，驗證 phone preset definition 上加入 `display_mtf_c50_cpd` family 後發現它會明顯惡化 phone 與 overall 指標，排除這條 preset-definition 解釋路徑
- [docs/imatest_parity_reference_anchor_acutance_curve_quality_loss_fit_followup.md](docs/imatest_parity_reference_anchor_acutance_curve_quality_loss_fit_followup.md)
  - issue `#29` 的第三十三個 quality-side follow-up，加入 per-sample Quality Loss record export 並在目前 `phone185` 分支上重擬 global quadratic 後，首次把 overall Quality Loss MAE 從 `2.33309` 明顯降到 `1.85163`
- [docs/imatest_parity_reference_anchor_acutance_curve_quality_loss_phoneoverride_followup.md](docs/imatest_parity_reference_anchor_acutance_curve_quality_loss_phoneoverride_followup.md)
  - issue `#29` 的第三十四個 quality-side follow-up，將新的 global Quality Loss fit 再加上一個 phone-only preset override 後，同時保住 overall 改善並把 phone Quality Loss MAE 從 `0.38082` 拉回到 `0.16934`
- [release/deadleaf_13b10_release/README.md](/Users/kevinhuang/work/acutance/release/deadleaf_13b10_release/README.md)
  - issue `#13`、`#18`、`#29` 的 release-facing parity-fit / reference profiles、預設 release 執行入口、以及保留的 diagnostic profiles
- [algo/README.md](/Users/kevinhuang/work/acutance/algo/README.md)
  - 演算法原型、數學流程、校準與 benchmark 記錄
  - 可交付的 release 包與批次執行方式
