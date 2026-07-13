项目简介
药店智能客服与管理系统是一个前后端分离的药店服务平台，包含面向管理员的业务后台与面向C端用户的智能导购助手。系统后端采用 Spring Boot 分层架构完成药品、购物车、订单等核心交易模块；同时基于 FastAPI + LangGraph 构建多轮对话智能体（Agent），通过自然语言理解用户症状，结合数据库检索推荐药品，实现从“人找药”到“药找人”的智能化升级。

项目特点：

完整的药店业务闭环：药品管理 → 购物车 → 下单 → 支付 → 发货 → 完成

AI 智能导购：基于 LangGraph 的多轮对话智能体，通过症状理解推荐药品

数据驱动运营：订单统计、交易概览、药品销售排行

安全认证：JWT 无状态认证 + 微信登录（预留）

技术栈
后端核心（管理端）
技术	版本	用途
Java	17	后端开发语言
Spring Boot	3.x	应用框架
MyBatis	3.x	ORM 框架
MySQL	8.0	业务数据库
Redis	7.x	会话缓存
JWT	0.9.x	用户认证
PageHelper	5.x	分页插件
AI 智能体（Agent）
技术	版本	用途
Python	3.11	开发语言
FastAPI	0.136.x	Web 框架
LangChain	1.3.x	LLM 框架
LangGraph	1.2.x	工作流编排
DeepSeek API	-	大语言模型
Redis	7.x	会话存储
工具链
项目管理：Maven、pip

代码管理：Git

API 测试：Postman / APIfox

数据库工具：Navicat / MySQL Workbench

📂 项目结构
text
<img width="676" height="751" alt="image" src="https://github.com/user-attachments/assets/62481a04-ba68-4890-93a4-b209db4796a4" />
<img width="842" height="659" alt="image" src="https://github.com/user-attachments/assets/9670048e-574d-4e09-8868-1ff4cf2f431b" />

🗄️ 数据库设计
核心表结构（共 11 张表）
表名	说明
user	用户表（微信登录）
drug	药品主表
drug_specification	药品规格表
drug_usage	药品用途表（树形结构）
drug_usage_relation	药品-用途关联表
drug_usage_synonym	用途同义词表
cart	购物车表
address_book	收货地址表
orders	订单主表
order_detail	订单明细表
order_log	订单操作日志表
ER 图核心关系
text
user (1) ──< cart (N)
user (1) ──< orders (N)
drug (1) ──< drug_specification (N)
drug (N) ──< drug_usage_relation >── (N) drug_usage
orders (1) ──< order_detail (N)
orders (1) ──< order_log (N)
🚀 快速开始
前置条件
Java 17+

Python 3.11+

MySQL 8.0+

Redis 7.x+

Maven 3.6+

pip

1. 克隆项目
bash
git clone https://github.com/your-username/pharmacy-agent.git
cd pharmacy-agent
2. 数据库初始化
sql
-- 创建数据库
CREATE DATABASE cloud_drugstore CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 导入表结构（执行 database/schema.sql）
USE cloud_drugstore;
SOURCE database/schema.sql;

-- 导入测试数据
SOURCE database/test_data.sql;
3. 管理端启动（Spring Boot）
bash
cd pharmacy-admin
mvn clean install
mvn spring-boot:run
4. AI 智能体启动（FastAPI）
bash
cd backend-agent

# 创建虚拟环境
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量（修改 configs/.env.dev）
cp configs/.env.example configs/.env.dev

# 启动服务
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
5. 验证服务
管理端健康检查：

bash
curl http://localhost:8080/admin/health
智能体健康检查：

bash
curl http://localhost:8000/api/v1/health
测试对话：

bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -H "X-User-Id: test_user_001" \
  -d '{"message":"我头痛"}'
📡 API 接口文档
管理端接口（部分）
路径	方法	说明
/admin/drug/page	GET	药品分页查询
/admin/drug	POST	新增药品
/admin/drug/{id}	PUT	编辑药品
/admin/drug/{id}/status	PUT	修改药品状态
/admin/order/page	GET	订单列表
/admin/order/{id}/ship	PUT	订单发货
/admin/order/{id}/cancel	PUT	管理员取消订单
/admin/statistics/overview	GET	统计总览
智能体接口
路径	方法	说明
/api/v1/chat	POST	对话接口
/api/v1/health	GET	健康检查
用户端接口（部分）
路径	方法	说明
/user/drug/page	GET	药品分页查询（用户端）
/user/drug/{id}	GET	药品详情
/user/cart/list	GET	购物车列表
/user/order/create	POST	下单
/user/order/{id}/pay	PUT	支付
🧠 智能体工作流
text
用户消息
   ↓
【意图识别节点】→ 判断 inquiry/chat/other
   ↓
【信息收集节点】→ 提取症状、年龄、过敏史、偏好
   ↓
【追问决策节点】→ 判断是否需要继续追问
   ├── 信息完整 → 进入药品检索
   └── 信息缺失 → 返回追问（等待用户回复）
   ↓
【药品检索节点】→ 同义词匹配 + 用途关联 + 排序
   ↓
【结果生成节点】→ LLM 生成推荐文案
   ↓
返回推荐结果
🔧 环境变量配置
智能体 .env.dev 示例
env
# 应用配置
APP_ENV=development
DEBUG=true

# MySQL 配置
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=cloud_drugstore

# Redis 配置
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_DB=0
REDIS_EXPIRE_SECONDS=604800

# DeepSeek API
OPENAI_API_KEY=sk-your-deepseek-key
OPENAI_BASE_URL=https://api.deepseek.com/v1
OPENAI_MODEL=deepseek-chat
项目亮点
LangGraph 四层工作流架构：Planner → Dispatcher → Worker → Synthesizer，实现任务分配与自检

智能体职能分化：通过精细化 Prompt 为各节点赋予独立职能，提高对关键信息的注意力捕获

订单状态机管理：精细化订单流转 + 超时自动取消 + 操作日志全记录

多级异常降级策略：LLM 调用失败、检索结果为空等场景自动降级，保障系统高可用

会话状态持久化：基于 Redis 的多轮对话存储，支持会话重置与过期自动清理

后续规划
库存管理模块

药品销量统计与趋势分析

用户画像与个性化推荐

WebSocket 实时消息推送（来单提醒）

向量检索升级（RAG）

