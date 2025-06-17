import threading
import time
import collections
import logging
import statistics

class SpikeDetector:
    def __init__(self, window_minutes, min_events, std_times):
        self.window_minutes = window_minutes
        self.min_events = min_events
        self.std_times = std_times
        # 改为全局总数统计，不区分 site_uuid/attack_type
        self.counts = collections.deque(maxlen=window_minutes)  # 每分钟攻击数
        self.lock = threading.Lock()
        self.last_minute = None
        self.alerted = set()  # 避免重复告警 (minute)

    def add_event(self, site_uuid, attack_type, event_time):
        minute = int(event_time // 60)
        now = int(time.time() // 60)
        with self.lock:
            if self.last_minute is None or minute > self.last_minute:
                logging.debug(f"[SpikeDetector] 新的一分钟: {minute} (last_minute={self.last_minute}), 归档并新建计数桶")
                self.counts.append(0)
                self.last_minute = minute
            # 保证当前分钟有元素
            if not self.counts:
                logging.debug(f"[SpikeDetector] 初始化全局当前分钟计数桶")
                self.counts.append(0)
            self.counts[-1] += 1
            logging.debug(f"[SpikeDetector] minute={minute}, 当前分钟累计: {self.counts[-1]}")

    def check_spike(self):
        """返回 [(cur, mean, std)] 需要告警的项（全局总数）"""
        results = []
        with self.lock:
            counts = list(self.counts)
            logging.debug(f"[SpikeDetector] 检查全局 counts={counts}")
            if len(counts) < self.window_minutes:
                logging.debug(f"[SpikeDetector] 窗口未满: {len(counts)}/{self.window_minutes}")
                return results
            cur = counts[-1]
            prev = counts[:-1]
            if len(prev) < 2:
                logging.debug(f"[SpikeDetector] 历史数据不足以计算均值/标准差")
                return results
            mean = statistics.mean(prev)
            std = statistics.stdev(prev) if len(prev) > 1 else 0
            logging.debug(f"[SpikeDetector] 当前:{cur}, 均值:{mean:.2f}, std:{std:.2f}")
            minute = int(time.time() // 60)
            key = minute
            if cur > self.min_events and cur > mean + self.std_times * std:
                if key not in self.alerted:
                    logging.info(f"[SpikeDetector] 检测到激增: 当前:{cur}, 均值:{mean:.2f}, std:{std:.2f}")
                    results.append((cur, mean, std))
                    self.alerted.add(key)
        return results