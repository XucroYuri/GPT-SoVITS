# Adversarial Sync Review - 2026-06-30

Scope: `XucroYuri/GPT-SoVITS` fork-recovery and upstream-integration pass.

Baseline evidence:

- Upstream baseline: `RVC-Boss/GPT-SoVITS@bf81cdb14a38b674b6e9996dabc97340bc9978d2`.
- `origin/main` was force-with-lease aligned to the same upstream commit after backups were pushed.
- Backup branches:
  - `backup/pre-sync-origin-main-20260630` -> `accd6226dc5efbe5d8db9348ae757e624351a19e`
  - `backup/pre-sync-local-dev-20260630` -> `99606c5f569451645ff4e11478baf9913381c43b`
- Product branch: `xucroyuri/proplus-hc-dev`, currently `3` commits ahead of `upstream/main`.
- Preserved local areas include Windows launch scripts, startup bootstrap/checks, portable packaging helpers, inference model defaults, reference-audio metadata helpers, ASR local-model handling, and tests.

## Findings

### High - Fork association is not restorable by normal repository settings

Evidence: GitHub metadata showed `XucroYuri/GPT-SoVITS` as `isFork=false`, `parent=null`, while `RVC-Boss/GPT-SoVITS` remains public upstream. GitHub documentation describes leaving a fork network as permanent and not reconnectable through normal settings.

Impact: GitHub compare, fork network UI, upstream PR affordances, and "Sync fork" behavior may remain unavailable unless GitHub Support manually attaches the repository.

Recommendation: Submit a GitHub Support request with the repository URLs, shared merge base `c767f0b83b998e996a4d230d86da575a03f54a3f`, desired parent `RVC-Boss/GPT-SoVITS`, and backup refs. Keep the soft-fork remote/branch workflow as the fallback.

Status: Not applied. Support submission requires external GitHub Support workflow completion.

### High - Main branch was intentionally rewritten

Evidence: `origin/main` moved from `accd6226dc5efbe5d8db9348ae757e624351a19e` to `bf81cdb14a38b674b6e9996dabc97340bc9978d2` using `--force-with-lease`.

Impact: Any collaborators basing work on the old private `main` must rebase or switch to the backup branch. Automation expecting the old `main` content may break.

Recommendation: Pin a short migration note in the repository or release notes, and keep `backup/pre-sync-origin-main-20260630` for at least one release cycle.

Status: Not applied. This report records the advice only.

### High - Large local artifacts remain present outside Git

Evidence: Previous local hygiene scan found large ignored directories, including `dist/`, `logs/`, `py312/`, `GPT_weights_v2ProPlus/`, `SoVITS_weights_v2ProPlus/`, `GPT_SoVITS/pretrained_models/`, `tools/asr/models/`, and `tools/uvr5/uvr5_weights/`.

Impact: Accidental `git add -f`, packaging scripts, or manual uploads could leak logs, model weights, generated packages, local runtimes, or private reference audio.

Recommendation: Add a pre-commit or CI guard that rejects model/audio/archive/runtime patterns and oversized files before push.

Status: Not applied. This pass only preserves `.gitignore` coverage and records the risk.

### Medium - Product branch still carries broad runtime changes

Evidence: `xucroyuri/proplus-hc-dev` changes 91 files relative to `upstream/main`, including core inference, training, text normalization, UVR, ASR, and packaging paths.

Impact: Future upstream merges may conflict in runtime-heavy files such as `GPT_SoVITS/inference_webui.py`, `GPT_SoVITS/TTS_infer_pack/TTS.py`, `tools/asr/funasr_asr.py`, and UVR helpers.

Recommendation: Split future local work into smaller topical branches or commits: startup/portable, inference UI, ASR model handling, training compatibility, and UVR changes.

Status: Not applied. Existing history was preserved as planned.

### Medium - Branch protection is absent

Evidence: GitHub branch metadata showed `main` and `codex/startup-portable-progress` as `protected=false`; backup branches are also unprotected.

Impact: Accidental force pushes or branch deletion could remove recovery points or disturb the upstream-tracking `main`.

Recommendation: Protect `main` against direct pushes except intentional sync operations, and consider protecting backup branches from deletion.

Status: Not applied. Repository settings were not changed in this pass.

### Medium - Private fork-like repository has visibility constraints

Evidence: `XucroYuri/GPT-SoVITS` is private while `RVC-Boss/GPT-SoVITS` is public.

Impact: GitHub Support may have constraints attaching a private repository to a public fork network. External contributors cannot inspect local product changes unless granted access.

Recommendation: Decide explicitly whether the product branch should stay private or whether a public mirror/PR branch is needed for upstream collaboration.

Status: Not applied.

### Medium - Inference UI merge preserved local UX over some upstream UI changes

Evidence: The final merge retained the local reference-audio/model-default/startup UI in `GPT_SoVITS/inference_webui.py`; upstream support files were retained, but UI-level upstream changes should be re-reviewed manually during future syncs.

Impact: Upstream inference UI improvements may require manual reapplication if they touched the same Gradio layout or inference callback flow.

Recommendation: Create targeted tests around reference-audio dropdown behavior, default model selection, and any upstream CUDA/FunASR UI toggles before the next upstream absorption.

Status: Not applied.

### Low - GitHub Support request is a process dependency

Evidence: There is no GitHub CLI/API endpoint that reliably reattaches a detached fork network.

Impact: The implementation can prepare evidence but cannot guarantee fork metadata restoration.

Recommendation: Track the Support ticket ID in a follow-up note once submitted, and keep the soft-fork workflow operational regardless of the response.

Status: Not applied.
