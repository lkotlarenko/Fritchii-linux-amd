#!/usr/bin/env bash
set -euo pipefail
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
build=${FRITCHII_BUILD_DIR:-"$root/build/linux-release"}
build=$(realpath -m -- "$build")
jobs=${JOBS:-2}
bash "$root/scripts/check-linux-recipes.sh"
cmake -S "$root" -B "$build" -G Ninja \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_C_COMPILER="${CC:-clang}" -DCMAKE_CXX_COMPILER="${CXX:-clang++}" \
    -DENABLE_QT=ON -DYUZU_USE_BUNDLED_QT=OFF \
    -Dfmt_FORCE_BUNDLED=ON -DENABLE_UPDATE_CHECKER=OFF \
    -DBUILD_TESTING=ON -DYUZU_TESTS=ON -DENABLE_WERROR=OFF "$@"
cmake --build "$build" --parallel "$jobs"
if [[ -d "$root/dist/recipes" ]]; then
    mkdir -p "$build/bin/recipes"
    cp -- "$root/dist/recipes/"*.nx2recipe "$build/bin/recipes/"
fi
test_root=$(mktemp -d "$build/test-data.XXXXXX")
env XDG_DATA_HOME="$test_root/data" XDG_CONFIG_HOME="$test_root/config" \
    XDG_CACHE_HOME="$test_root/cache" \
    ctest --test-dir "$build" --output-on-failure
rm -rf -- "$test_root"
