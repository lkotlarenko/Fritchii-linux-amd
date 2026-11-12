# Linux AppImage releases

Repository: https://github.com/lkotlarenko/Fritchii-linux-amd. The port's published
branch is `main`; upstream Fritchii's Windows branch remains the source base.
Do not merge generic Lichii over Fritchii or force-push a published release tag.

## Automatic builds and releases

`.github/workflows/linux-appimage.yml` builds pushes/PRs to `main`, can be started
manually with **Actions → Linux AppImage → Run workflow**, and publishes on tags:

```text
linux-v5.8.4-r1
linux-v5.8.4-r2
```

The version must match `dist/frizti_version.txt`; `rN` identifies a Linux port
revision. A main-branch or manual run uploads build artifacts but does not publish
a release. A tagged push publishes only after Release/CTest, Python regression
tests, AppImage packaging, checksum verification and an Xvfb GUI smoke succeed.
An existing release's assets are left unchanged, so a retry cannot replace an
already published owner-tested binary. Use a new revision tag for a new binary.

From a clone of this fork, after local validation and pushing the intended source:

```sh
git switch main
git status --short
version=$(tr -d '\r\n' < dist/frizti_version.txt)
# Choose the next unused port revision; do not reuse this example blindly.
tag="linux-v${version}-r2"
git tag -a "$tag" -m "Fritchii $version native Linux port revision 2"
git push origin main
git push origin "$tag"
```

Push only the intended branch/tag, not every inherited upstream ref. GitHub
Actions must be enabled on the fork. No personal token is needed in CI: build
permissions are read-only; only the publish job receives `contents: write` with
the built-in `GITHUB_TOKEN`. A maintainer pushing workflow changes needs GitHub
credentials authorized for workflows. Never commit credentials or local profiles.

## Build environment and checks

The job runs on an Ubuntu x86_64 host **inside an Arch Linux container** and
installs dependencies there, not on the owner's computer. It uses generic x86_64
Clang Release `-O3 -DNDEBUG`, two jobs, Qt6, bundled fmt and no unsafe fast-math,
CPU affinity changes, imported PGO profile or Windows updater. Compiler/dependency
versions are retained in the logs. Arch packages and the base image roll forward;
this records a reproducible procedure, not a bit-for-bit pinned distro snapshot.
The resulting AppImage targets current Arch/CachyOS glibc, not all old Linux distros.

Official checkout/cache/artifact actions are pinned to verified commit SHAs.
`scripts/fetch-appimage-tools.sh` checks official packaging tools against
`dist/linux-appimage-tools.sha256`. Their upstream continuous URLs can change:
a mismatched download fails closed. Review the new upstream asset digest and
packaging behavior before updating the manifest; use a fresh tools directory when
validating changed versions. linuxdeploy may additionally fetch its AppImage runtime.

Local publication must use clean public history based on the official upstream
revision. Do not push a private development branch whose earlier commits contain
machine-specific handoffs, personal paths or private author metadata. Archive those
reports under ignored local storage, rewrite the public documentation, and publish
reviewed changes with non-personal author metadata while preserving upstream credits.

Linux compiler prefix mapping removes checkout paths from compiled diagnostics.
Packaging runs `tools/nx2/audit_linux_release.py` on the unpacked directory and fails
on local home/checkout markers or user-data filenames. The checks have regression
tests; inspect source/history and intended asset selection separately. Do not upload
raw local build logs, source maps, capture files or configuration. CI logs come from
the disposable runner and must not contain owner credentials.

The build includes the full Qt GUI and official shader-preparation recipe. The
headless smoke starts a newly isolated empty profile under Xvfb, opens home and
Settings, and closes it; it takes no screenshots. CI's software Vulkan enumeration
is not an RX 7600 game/rendering test. It does not download games, keys or firmware.
CPU/GPU/gameplay regressions still require local testing on an isolated profile.

Successful builds remove temporary test data; successful packaging removes staging
unless `FRITCHII_KEEP_APPDIR=1`. Failed runs preserve diagnostics. Artifacts and
logs are retained for 14 days; published release assets remain downloadable.

## Local artifact validation and manual publication

```sh
./scripts/build-linux.sh -DENABLE_DEBUG_TOOLS=OFF
./scripts/fetch-appimage-tools.sh
./scripts/package-appimage.sh
QT_QPA_PLATFORM=wayland ./scripts/test-linux-appimage.sh
QT_QPA_PLATFORM=xcb ./scripts/test-linux-appimage.sh
# Headless CI equivalent:
# xvfb-run -a ./scripts/test-linux-appimage.sh
```

The GUI smoke compiles a test-only Qt preload and uses a fresh temporary XDG
profile; normal launches never load it. Logs are under `build/runtime-tests/`.
Failed smoke profiles remain there for investigation. Do not run it with game
arguments or repoint its temporary directories at personal data.

A maintainer may publish an already tested local AppImage instead of replacing it
with CI's rebuild. Verify the tag/source and `.sha256`, record the binary's embedded
source revision and test conditions in release notes, then use `gh release create`
with `--verify-tag` and the AppImage plus checksum as assets. The automation detects
that release and retains its files. Do not upload `build/`, NAND/SDMC, cache/profile
copies, console keys, firmware, games, captures or credentials as release assets.

## Updating upstream safely

1. Preserve the current working artifact, checksum, source checkpoint and prepared
   profile. Keep saves outside the checkout's disposable build directories.
2. Fetch the official `Frizti/Fritchii` Windows branch/tag; review its diff and merge
   it on an isolated Linux branch. Preserve Fritchii's Zelda and shader-cache behavior.
3. Build/test, validate both desktop backends and actual gameplay, and check native
   and AppImage warm-cache reuse. A changed translator hash may require preparation
   once; do not delete existing v54 caches to force it.
4. Update the handoff, progress and optimization ledger with actual results, then
   merge/push the tested Linux source and create the next version/revision tag.
5. Replace only the executable/AppImage. Retain the prior release for rollback;
   never let Linux self-update to a Windows `.exe`.
