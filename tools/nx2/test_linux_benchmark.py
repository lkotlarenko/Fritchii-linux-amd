#!/usr/bin/env python3
import unittest

from linux_benchmark import frame_summary, thread_deltas


class ThreadDeltaTests(unittest.TestCase):
    def test_cpu_and_faults_follow_the_faulting_thread(self):
        before = {"threads": {"1": {"name": "GPU", "start_ticks": 5, "ticks": 10,
                                     "minor_faults": 20, "major_faults": 3}}}
        after = {"threads": {"1": {"name": "GPU", "start_ticks": 5, "ticks": 17,
                                    "minor_faults": 31, "major_faults": 6},
                             "2": {"name": "new", "start_ticks": 8, "ticks": 100,
                                    "minor_faults": 99, "major_faults": 80}}}
        self.assertEqual(thread_deltas([before, after]), {
            "1:GPU": {"ticks": 7, "minor_faults": 11, "major_faults": 3}})

    def test_reused_tid_does_not_produce_false_faults(self):
        before = {"threads": {"1": {"name": "GPU", "start_ticks": 5, "ticks": 10,
                                     "minor_faults": 20, "major_faults": 3}}}
        after = {"threads": {"1": {"name": "GPU", "start_ticks": 9, "ticks": 100,
                                    "minor_faults": 200, "major_faults": 30}}}
        self.assertEqual(thread_deltas([before, after]), {})


class FrameSummaryTests(unittest.TestCase):
    def snapshots(self, bins, elapsed, presents):
        before = {"scm_rev": "same", "presents": 7, "uptime_s": 10,
                  "frame_times": [0] * 4096, "frame_time_bucket_us": 250}
        after = dict(before, presents=7 + presents, uptime_s=10 + elapsed)
        after["frame_times"] = before["frame_times"].copy()
        for bucket, count in bins.items():
            after["frame_times"][bucket] = count
        return before, after

    def test_slow_baseline_does_not_saturate_at_old_64ms_limit(self):
        result = frame_summary(*self.snapshots({280: 100}, 7, 100))
        self.assertAlmostEqual(result["average_fps"], 100 / 7)
        self.assertEqual(result["p99"], {"lower_ms": 70, "upper_ms": 70.25})
        self.assertAlmostEqual(result["one_percent_low_fps_approx"], 1000 / 70.125)

    def test_tail_percentiles_and_slowest_one_percent_are_distinct(self):
        result = frame_summary(*self.snapshots({40: 950, 80: 40, 400: 10}, 12, 1000))
        self.assertEqual(result["p95"]["lower_ms"], 10)
        self.assertEqual(result["p99"]["lower_ms"], 20)
        self.assertEqual(result["worst"], {"lower_ms": 100, "upper_ms": 100.25})
        self.assertAlmostEqual(result["one_percent_low_fps_approx"], 1000 / 100.125)

    def test_overflow_is_censored_not_reported_as_exact_duration(self):
        result = frame_summary(*self.snapshots({4095: 100}, 150, 100))
        self.assertIsNone(result["p99"]["upper_ms"])
        self.assertIsNone(result["worst"]["upper_ms"])
        self.assertIsNone(result["one_percent_low_fps_approx"])
        self.assertEqual(result["overflow_intervals"], 100)

    def test_restart_rejected(self):
        before, after = self.snapshots({40: 100}, 1, 100)
        after["scm_rev"] = "different"
        with self.assertRaises(RuntimeError):
            frame_summary(before, after)

    def test_empty_window_has_no_percentiles(self):
        result = frame_summary(*self.snapshots({}, 1, 0))
        self.assertIsNone(result["p99"])
        self.assertIsNone(result["one_percent_low_fps_approx"])

    def test_session_and_histogram_changes_rejected(self):
        for key, value in (("host_pid", 42), ("program_id", "other"),
                           ("frame_time_bucket_us", 500), ("uptime_s", 1),
                           ("frame_times", [0] * 256), ("powered_on", False)):
            with self.subTest(key=key):
                before, after = self.snapshots({40: 10}, 1, 10)
                after[key] = value
                with self.assertRaises(RuntimeError):
                    frame_summary(before, after)


if __name__ == "__main__":
    unittest.main()
