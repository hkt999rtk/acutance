# Validation And Build

Use this reference when implementation or review touches code, runtime behavior, tools, firmware, or tests.

## Host validation

Prefer host validation for fast feedback.

Typical host flow:

```bash
cmake -S . -B build -DMINICLAW_TARGET_OS=host
cmake --build build -j2
ctest --test-dir build --output-on-failure
```

## WSL guidance

1. Prefer running host validation inside WSL even when the checkout lives on Windows.
2. Refresh submodules in the active worktree before configuring.
3. Treat CRLF-sensitive shell failures as environment problems first.
4. `set: pipefail\r: invalid option name` usually means line-ending cleanup is needed before deeper debugging.

Useful baseline packages in WSL:
- `cmake`
- `ninja-build`
- `pkg-config`
- `ffmpeg`

## Firmware guidance

1. AmebaPro2 firmware builds use tracked `pro2_sdk/` plus `.local/` sandboxed artifacts.
2. Prefer documented WSL flow for firmware builds on Windows.
3. Keep build artifacts under `.local/`.
4. Avoid modifying tracked SDK inputs unless the task explicitly requires it.

## High-signal tests

When runtime, tool, planner, or prompt behavior changes, prioritize:
- `miniclaw_foundation_tests`
- `miniclaw_runtime_tests`
- `miniclaw_tool_tests`

## Reporting validation

Always distinguish:
- PR-specific failures
- pre-existing baseline failures
- environment/setup failures

When full validation is blocked, still run the highest-signal targeted tests you can.
