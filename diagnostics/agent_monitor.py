"""Agent Monitor - Agent 监控仪表板


提供 Agent 运行时指标收集、统计和可视化数据。
"""

import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class MetricPoint:
    """指标数据点"""
    timestamp: float
    value: float
    labels: dict[str, str] = field(default_factory=dict)


@dataclass
class MetricSummary:
    """指标摘要"""
    name: str
    count: int
    sum: float
    min: float
    max: float
    avg: float
    p50: float = 0.0
    p95: float = 0.0
    p99: float = 0.0


@dataclass
class AgentMetrics:
    """Agent 运行指标"""
    # 调用统计
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    
    # 延迟统计
    latency_ms_sum: float = 0.0
    latency_ms_min: float = float('inf')
    latency_ms_max: float = 0.0
    
    # Token 统计
    tokens_input: int = 0
    tokens_output: int = 0
    
    # 工具调用统计
    tool_calls: int = 0
    tool_failures: int = 0
    
    # 时间戳
    first_call_time: Optional[float] = None
    last_call_time: Optional[float] = None
    
    @property
    def success_rate(self) -> float:
        if self.total_calls == 0:
            return 0.0
        return self.successful_calls / self.total_calls
    
    @property
    def avg_latency_ms(self) -> float:
        if self.total_calls == 0:
            return 0.0
        return self.latency_ms_sum / self.total_calls
    
    @property
    def total_tokens(self) -> int:
        return self.tokens_input + self.tokens_output


class AgentMonitor:
    """Agent 监控器
    
        - 调用统计（总数、成功、失败）
    - 延迟追踪（min, max, avg, p50, p95, p99）
    - Token 使用统计
    - 工具调用监控
    - 时间序列数据
    """
    
    def __init__(self):
        self.metrics = AgentMetrics()
        self._latencies: list[float] = []
        self._time_series: dict[str, list[MetricPoint]] = defaultdict(list)
        self._tool_stats: dict[str, dict[str, int]] = defaultdict(lambda: {"calls": 0, "failures": 0})
    
    def record_call(self, success: bool, latency_ms: float, 
                    tokens_input: int = 0, tokens_output: int = 0):
        """记录一次 Agent 调用"""
        self.metrics.total_calls += 1
        if success:
            self.metrics.successful_calls += 1
        else:
            self.metrics.failed_calls += 1
        
        # 延迟统计
        self.metrics.latency_ms_sum += latency_ms
        self.metrics.latency_ms_min = min(self.metrics.latency_ms_min, latency_ms)
        self.metrics.latency_ms_max = max(self.metrics.latency_ms_max, latency_ms)
        self._latencies.append(latency_ms)
        
        # Token 统计
        self.metrics.tokens_input += tokens_input
        self.metrics.tokens_output += tokens_output
        
        # 时间戳
        now = time.time()
        if not self.metrics.first_call_time:
            self.metrics.first_call_time = now
        self.metrics.last_call_time = now
        
        # 时间序列
        self._time_series["latency"].append(MetricPoint(timestamp=now, value=latency_ms))
        self._time_series["tokens_input"].append(MetricPoint(timestamp=now, value=tokens_input))
        self._time_series["tokens_output"].append(MetricPoint(timestamp=now, value=tokens_output))
    
    def record_tool_call(self, tool_name: str, success: bool, latency_ms: float = 0):
        """记录工具调用"""
        self.metrics.tool_calls += 1
        if not success:
            self.metrics.tool_failures += 1
        
        self._tool_stats[tool_name]["calls"] += 1
        if not success:
            self._tool_stats[tool_name]["failures"] += 1
        
        # 时间序列
        now = time.time()
        self._time_series[f"tool_{tool_name}"].append(
            MetricPoint(timestamp=now, value=latency_ms, labels={"success": str(success)})
        )
    
    def get_latency_summary(self) -> MetricSummary:
        """获取延迟统计摘要"""
        if not self._latencies:
            return MetricSummary(name="latency_ms", count=0, sum=0, min=0, max=0, avg=0)
        
        sorted_latencies = sorted(self._latencies)
        count = len(sorted_latencies)
        
        return MetricSummary(
            name="latency_ms",
            count=count,
            sum=sum(sorted_latencies),
            min=sorted_latencies[0],
            max=sorted_latencies[-1],
            avg=sum(sorted_latencies) / count,
            p50=sorted_latencies[int(count * 0.5)],
            p95=sorted_latencies[int(count * 0.95)] if count >= 20 else sorted_latencies[-1],
            p99=sorted_latencies[int(count * 0.99)] if count >= 100 else sorted_latencies[-1],
        )
    
    def get_tool_stats(self) -> dict[str, dict[str, Any]]:
        """获取工具调用统计"""
        stats = {}
        for tool_name, data in self._tool_stats.items():
            stats[tool_name] = {
                "calls": data["calls"],
                "failures": data["failures"],
                "success_rate": (data["calls"] - data["failures"]) / data["calls"] if data["calls"] > 0 else 0,
            }
        return stats
    
    def get_time_series(self, metric_name: str, 
                        start_time: float = None, 
                        end_time: float = None) -> list[MetricPoint]:
        """获取时间序列数据"""
        points = self._time_series.get(metric_name, [])
        
        if start_time:
            points = [p for p in points if p.timestamp >= start_time]
        if end_time:
            points = [p for p in points if p.timestamp <= end_time]
        
        return points
    
    def get_dashboard_data(self) -> dict[str, Any]:
        """获取仪表板数据（用于可视化）"""
        latency_summary = self.get_latency_summary()
        
        return {
            "overview": {
                "total_calls": self.metrics.total_calls,
                "success_rate": self.metrics.success_rate,
                "avg_latency_ms": self.metrics.avg_latency_ms,
                "total_tokens": self.metrics.total_tokens,
            },
            "latency": {
                "min": latency_summary.min,
                "max": latency_summary.max,
                "avg": latency_summary.avg,
                "p50": latency_summary.p50,
                "p95": latency_summary.p95,
                "p99": latency_summary.p99,
            },
            "tokens": {
                "input": self.metrics.tokens_input,
                "output": self.metrics.tokens_output,
                "total": self.metrics.total_tokens,
            },
            "tools": self.get_tool_stats(),
            "time_series": {
                name: [{"timestamp": p.timestamp, "value": p.value} for p in points[-100:]]
                for name, points in self._time_series.items()
            },
        }
    
    def reset(self):
        """重置所有指标"""
        self.metrics = AgentMetrics()
        self._latencies.clear()
        self._time_series.clear()
        self._tool_stats.clear()


# 使用示例
if __name__ == "__main__":
    monitor = AgentMonitor()
    
    # 模拟一些调用
    import random
    for i in range(100):
        monitor.record_call(
            success=random.random() > 0.1,
            latency_ms=random.uniform(10, 500),
            tokens_input=random.randint(100, 1000),
            tokens_output=random.randint(50, 500),
        )
    
    # 模拟工具调用
    monitor.record_tool_call("web_search", success=True, latency_ms=150)
    monitor.record_tool_call("web_search", success=True, latency_ms=200)
    monitor.record_tool_call("terminal", success=False, latency_ms=5000)
    
    # 获取仪表板数据
    import json
    dashboard = monitor.get_dashboard_data()
    print(json.dumps(dashboard, indent=2))
