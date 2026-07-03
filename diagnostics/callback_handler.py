"""Callback Handler - 回调处理器


提供 Agent 工具调用的回调追踪和调试输出。
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Optional


_TEXT_COLOR = {
    "blue": "\033[36;1m",
    "yellow": "\033[33;1m",
    "pink": "\033[38;5;200m",
    "green": "\033[32;1m",
    "red": "\033[31;1m",
    "reset": "\033[0m",
}


@dataclass
class ToolCallRecord:
    """工具调用记录"""
    tool_name: str
    tool_inputs: dict[str, Any]
    tool_outputs: Optional[Any] = None
    error: Optional[str] = None
    duration_ms: float = 0.0
    success: bool = True


class CallbackHandler:
    """Agent 回调处理器
    
        - 工具调用开始/结束/错误回调
    - Agent 循环追踪
    - 调试输出（带颜色）
    - 调用历史记录
    """
    
    def __init__(self, debug: bool = False, color: str = "green"):
        self.debug = debug
        self.color = color
        self.logger = logging.getLogger("hermes.callback")
        self.current_loop = 1
        self.history: list[ToolCallRecord] = []
    
    def _colored(self, text: str, color: str) -> str:
        """带颜色输出"""
        if not self.debug:
            return text
        return f"{_TEXT_COLOR.get(color, '')}{text}{_TEXT_COLOR['reset']}"
    
    def on_agent_start(self, thought: str = ""):
        """Agent 开始回调"""
        if self.debug:
            msg = f"\n[on_agent_start] Loop: {self.current_loop}"
            if thought:
                msg += f"\nThought: {thought}"
            print(self._colored(msg, self.color))
        
        self.logger.debug(f"Agent loop {self.current_loop} started")
    
    def on_agent_end(self, result: Any = None):
        """Agent 结束回调"""
        if self.debug:
            print(self._colored(f"\n[on_agent_end] Loop: {self.current_loop}", self.color))
        
        self.current_loop += 1
        self.logger.debug(f"Agent loop {self.current_loop - 1} ended")
    
    def on_tool_start(self, tool_name: str, tool_inputs: dict[str, Any]):
        """工具调用开始回调"""
        if self.debug:
            msg = f"\n[on_tool_start] Tool: {tool_name}\nInputs: {tool_inputs}"
            print(self._colored(msg, "blue"))
        
        self.logger.debug(f"Tool started: {tool_name}")
    
    def on_tool_end(self, tool_name: str, tool_inputs: dict[str, Any], 
                    tool_outputs: Any = None, duration_ms: float = 0.0):
        """工具调用结束回调"""
        record = ToolCallRecord(
            tool_name=tool_name,
            tool_inputs=tool_inputs,
            tool_outputs=tool_outputs,
            duration_ms=duration_ms,
        )
        self.history.append(record)
        
        if self.debug:
            output_str = str(tool_outputs)[:500] if tool_outputs else "None"
            msg = f"\n[on_tool_end] Tool: {tool_name}\nOutputs: {output_str}\nDuration: {duration_ms:.1f}ms"
            print(self._colored(msg, "green"))
        
        self.logger.debug(f"Tool ended: {tool_name} ({duration_ms:.1f}ms)")
    
    def on_tool_error(self, tool_name: str, error: Exception, 
                      tool_inputs: dict[str, Any] = None):
        """工具调用错误回调"""
        record = ToolCallRecord(
            tool_name=tool_name,
            tool_inputs=tool_inputs or {},
            error=str(error),
            success=False,
        )
        self.history.append(record)
        
        if self.debug:
            msg = f"\n[on_tool_error] Tool: {tool_name}\nError: {error}"
            print(self._colored(msg, "red"))
        
        self.logger.error(f"Tool error: {tool_name} - {error}")
    
    def on_thought(self, thought: str):
        """思考过程回调"""
        if self.debug:
            print(self._colored(f"\n[on_thought] {thought}", "yellow"))
    
    def on_observation(self, observation: str):
        """观察结果回调"""
        if self.debug:
            print(self._colored(f"\n[on_observation] {observation}", "pink"))
    
    def get_history(self, tool_name: str = None) -> list[ToolCallRecord]:
        """获取调用历史"""
        if tool_name:
            return [r for r in self.history if r.tool_name == tool_name]
        return self.history.copy()
    
    def get_stats(self) -> dict[str, Any]:
        """获取调用统计"""
        total = len(self.history)
        successful = sum(1 for r in self.history if r.success)
        failed = total - successful
        
        tool_counts = {}
        for record in self.history:
            tool_counts[record.tool_name] = tool_counts.get(record.tool_name, 0) + 1
        
        return {
            "total_calls": total,
            "successful": successful,
            "failed": failed,
            "success_rate": successful / total if total > 0 else 0,
            "tool_counts": tool_counts,
            "total_loops": self.current_loop - 1,
        }
    
    def reset(self):
        """重置状态"""
        self.history.clear()
        self.current_loop = 1


# 使用示例
if __name__ == "__main__":
    handler = CallbackHandler(debug=True)
    
    # 模拟 Agent 循环
    handler.on_agent_start("I need to search for information")
    handler.on_tool_start("web_search", {"query": "test"})
    handler.on_tool_end("web_search", {"query": "test"}, {"results": ["item1"]}, 150.0)
    handler.on_observation("Found 1 result")
    handler.on_agent_end()
    
    # 统计
    import json
    print(json.dumps(handler.get_stats(), indent=2))
