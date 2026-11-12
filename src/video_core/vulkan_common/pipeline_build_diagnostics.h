// SPDX-License-Identifier: GPL-3.0-or-later

#pragma once

#include <array>
#include <atomic>
#include <chrono>
#include <cstdlib>
#include <utility>

#include "common/common_types.h"
#include "common/logging.h"

namespace Vulkan::PipelineBuildDiagnostics {

inline bool Enabled() {
    static const bool enabled = [] {
        const char* value = std::getenv("FRITCHII_PIPELINE_DIAGNOSTICS");
        return value && value[0] == '1';
    }();
    return enabled;
}

struct Counters {
    std::atomic<u64> calls{}, succeeded{}, failed{}, nanoseconds{}, with_app_cache{};
    std::atomic<u64> translations{}, translation_ns{};
};
inline std::array<Counters, 2> counters;

template <typename F>
decltype(auto) Translate(bool compute, F&& operation) {
    if (!Enabled()) {
        return std::forward<F>(operation)();
    }
    struct Timer {
        Counters& stats;
        std::chrono::steady_clock::time_point begin{std::chrono::steady_clock::now()};
        ~Timer() {
            stats.translations.fetch_add(1, std::memory_order_relaxed);
            stats.translation_ns.fetch_add(std::chrono::duration_cast<std::chrono::nanoseconds>(
                                               std::chrono::steady_clock::now() - begin)
                                               .count(),
                                           std::memory_order_relaxed);
        }
    } timer{counters[compute ? 1 : 0]};
    return std::forward<F>(operation)();
}

inline void Record(bool compute, s32 result, bool with_cache,
                   std::chrono::steady_clock::time_point begin) {
    auto& stats = counters[compute ? 1 : 0];
    stats.calls.fetch_add(1, std::memory_order_relaxed);
    stats.nanoseconds.fetch_add(std::chrono::duration_cast<std::chrono::nanoseconds>(
                                    std::chrono::steady_clock::now() - begin)
                                    .count(),
                                std::memory_order_relaxed);
    stats.with_app_cache.fetch_add(with_cache ? 1 : 0, std::memory_order_relaxed);
    if (result == 0) {
        stats.succeeded.fetch_add(1, std::memory_order_relaxed);
    } else if (stats.failed.fetch_add(1, std::memory_order_relaxed) < 16) {
        LOG_WARNING(Render_Vulkan, "Pipeline diagnostics: {} creation returned VkResult {}",
                    compute ? "compute" : "graphics", result);
    }
}

inline void Report(const char* phase) {
    if (!Enabled()) {
        return;
    }
    for (size_t i = 0; i < counters.size(); ++i) {
        const auto& stats = counters[i];
        LOG_INFO(Render_Vulkan,
                 "Pipeline diagnostics cumulative process totals ({}), {}: {} Vulkan calls, "
                 "{} succeeded, {} non-success, {:.3f} ms summed creation time, {} with "
                 "application cache (not a hit count; includes host and preparation pipelines)",
                 phase, i ? "compute" : "graphics", stats.calls.load(std::memory_order_relaxed),
                 stats.succeeded.load(std::memory_order_relaxed),
                 stats.failed.load(std::memory_order_relaxed),
                 static_cast<double>(stats.nanoseconds.load(std::memory_order_relaxed)) / 1e6,
                 stats.with_app_cache.load(std::memory_order_relaxed));
        LOG_INFO(Render_Vulkan,
                 "Pipeline diagnostics cumulative process totals ({}), {}: {} translation "
                 "attempts in {:.3f} ms (sum across threads, excludes SPIR-V emission)",
                 phase, i ? "compute" : "graphics",
                 stats.translations.load(std::memory_order_relaxed),
                 static_cast<double>(stats.translation_ns.load(std::memory_order_relaxed)) / 1e6);
    }
}

} // namespace Vulkan::PipelineBuildDiagnostics
