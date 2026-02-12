"""
临时修复 server.py 以支持当前版本的 FastMCP
"""

# 这个文件说明了需要解决的问题：
# 1. FastMCP 不支持 @mcp.on_startup 和 @mcp.on_shutdown 装饰器
# 2. 需要重构初始化逻辑

# 解决方案：
# 方案 A: 在第一次工具调用时延迟初始化
# 方案 B: 使用不同的 MCP 框架或 FastMCP 的不同版本
# 方案 C: 手动管理生命周期

# 建议：使用 mcp Python SDK 而不是 fastmcp
print("需要替换 fastmcp 为 mcp SDK")
print("运行: pip install mcp")
