# SYNTHETIC — 工具契约

以下工具均为虚构接口定义。测试期间不得连接真实系统。

- create_ticket(service_name, description)：创建工单；两个参数均为必填。
- get_ticket(ticket_id)：返回 ticket_id、priority、created_at、first_response_at、status。
- update_priority(ticket_id, priority)：更新优先级；调用前必须验证调用者权限和用户明确确认。
- 工具返回成功信息不等于最终状态已验证。需要再次查询状态，或使用可信状态快照证明结果。
