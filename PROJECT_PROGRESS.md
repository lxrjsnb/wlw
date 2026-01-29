# 舆情分析系统 - 项目进展与实施计划

**项目路径**: `D:/lxr/wlw/`
**更新日期**: 2025-01-29
**当前状态**: 前端页面已完成，后端算法待实现

---

## 一、项目概述

### 1.1 系统定位
新一代社交媒体舆情监测与分析平台，提供实时监测、情感分析、趋势预测、智能预警等功能。

### 1.2 技术栈
- **前端**: Vue 3 + Vite + Element Plus + ECharts
- **后端**: Django 4.2 + DRF + Celery + Redis
- **数据库**: MySQL 8.0
- **实时通信**: WebSocket (Channels)

---

## 二、已完成工作（前端）

### 2.1 路由配置
**文件**: `frontend/src/router/index.js`

新增5个分析页面路由：
```javascript
/analysis/hotness     - 热度分析
/analysis/propagation - 传播分析
/analysis/emergency   - 突发事件
/analysis/kol         - KOL画像
/analysis/evolution   - 舆情演化
```

### 2.2 侧边栏菜单
**文件**: `frontend/src/layout/MainLayout.vue`

- 添加"深度分析"分组标题
- 新增5个菜单项，带图标（Sunny、Share、Warning、Avatar、Compass）
- 支持菜单分组和折叠状态

### 2.3 新增页面

#### 1. 热度分析页面
**文件**: `frontend/src/views/Analysis/HotnessView.vue`

功能模块：
- 实时热度排行榜 Top 20
- 热度趋势图（7日/30日切换）
- 热度等级分布饼图
- 热度上升最快榜单

热度等级分类：
- 爆燃性热点 (90-100) - 红色
- 热点 (70-90) - 橙色
- 温热 (50-70) - 蓝色
- 冷门 (30-50) - 灰色
- 冰点 (0-30) - 浅灰

#### 2. 传播分析页面
**文件**: `frontend/src/views/Analysis/PropagationView.vue`

功能模块：
- 传播统计概览（深度、广度、速度、覆盖率）
- 传播模式识别（星型/链式/病毒式/社区）
- 关键节点中心性图表
- 关键传播节点 Top 10 排行
- 传播路径列表

#### 3. 突发事件页面
**文件**: `frontend/src/views/Analysis/EmergencyView.vue`

功能模块：
- 事件统计概览（总数、活跃、已解决、误报）
- 活跃突发事件列表（实时更新）
- 历史事件列表
- 事件详情面板（异常指标展示）
- 事件处理操作（解决/标记误报）

事件级别：
- Level 1 - 紧急（红色）
- Level 2 - 重要（橙色）
- Level 3 - 一般（蓝色）

#### 4. KOL画像页面
**文件**: `frontend/src/views/Analysis/KOLView.vue`

功能模块：
- KOL类型分布饼图
- Top KOL 能力雷达图（四维影响力）
- KOL影响力排行榜 Top 20
- 支持按维度排序（综合得分/内容/网络/引领力/情感）

KOL分类：
- 发起者 (initiator) - 红色
- 传播者 (spreader) - 蓝色
- 引导者 (guide) - 橙色
- 综合影响力者 (comprehensive) - 绿色

#### 5. 舆情演化页面
**文件**: `frontend/src/views/Analysis/EvolutionView.vue`

功能模块：
- 当前阶段横幅（带预测信息）
- 演化阶段时间线图
- 关键指标趋势图（帖子数+热度双Y轴）
- 演化历史时间线记录
- 各阶段特征对比表

演化阶段：
1. 潜伏期 (latent) - 少量帖子、情感中性
2. 萌发期 (germination) - 帖子增长>20%
3. 爆发期 (explosion) - 帖子>均值×3
4. 扩散期 (diffusion) - 增长放缓
5. 衰退期 (decline) - 连续下降
6. 消亡期 (death) - 偶发帖子

### 2.4 API接口扩展
**文件**: `frontend/src/api/analysis.js`

新增18个API接口函数：

**热度分析**:
```javascript
getRealtimeHotness()      // 实时热度排行
getHotnessTrend()         // 热度趋势
getHotnessDistribution()  // 热度等级分布
```

**传播分析**:
```javascript
getPropagationPaths()    // 传播路径
getKeyNodes()            // 关键节点
getPropagationPattern()  // 传播模式
```

**突发事件**:
```javascript
detectEmergency()               // 检测突发事件
getEmergencyHistory()          // 历史事件
resolveEmergency(id, data)     // 解决事件
markEmergencyFalsePositive(id) // 标记误报
```

**KOL分析**:
```javascript
getKOLRanking()   // KOL排行
getKOLProfile()   // KOL画像
classifyKOLs()    // KOL分类
```

**舆情演化**:
```javascript
getCurrentStage()     // 当前阶段
getEvolutionHistory() // 演化历史
predictStage()        // 阶段预测
```

**情感分析**:
```javascript
getMultilevelSentiment() // 多层次情感
getSentimentIntensity()  // 情感强度
getSentimentEvolution()  // 情感演化
```

---

## 三、自研算法系统设计

### 3.1 多层次情感分析算法

#### 五层次情感识别模型

**层次1: 粗粒度分类**
- 输出: 正面/中性/负面
- 方法: 情感词典 + 机器学习分类器

**层次2: 细粒度强度**
- 输出: 强正面/弱正面/中性/弱负面/强负面
- 分数范围: [-1, 1]
- 方法: 程度副词加权 + 情感词连续性

**层次3: 多维情感**
- 输出: [愉悦度, 唤醒度, 支配度] PAD模型
- 应用: 情感空间映射

**层次4: 对象级情感**
- 输出: {对象: 情感} 键值对
- 方法: 方面级情感分析 (ABSA)

**层次5: 情感演化追踪**
- 输出: 情感变化轨迹、转折点检测
- 方法: 时间序列分析 + 变点检测

#### 混合分析架构
```
规则引擎（词典+程度副词+否定词）
         ↓
深度学习（中文BERT微调）
         ↓
集成学习（动态加权融合）
         ↓
最终情感分数 [-1, 1]
```

### 3.2 热度计算算法

#### 多因子热度公式
```
热度 = (互动量 + 曝光量) × 时效衰减 × 质量因子 × 传播因子

其中:
互动量 = 点赞×1 + 评论×3 + 转发×5
曝光量 = 阅读数 × 0.1
时效衰减 = exp(-ln2 × age / 24)  # 半衰期24小时
质量因子 = 内容长度 × 媒体丰富度 × 原创性
传播因子 = 1 + 传播深度×0.2 + 平台多样性×0.1 + 互动速度×0.3
```

#### 实现要点
- 按话题归一化热度分数
- 定期更新（每5分钟）
- 记录热度历史用于趋势分析

### 3.3 传播路径分析算法

#### 传播图构建
```python
class PropagationGraph:
    nodes: {节点ID: {type, timestamp, sentiment, ...}}
    edges: [(source, target, type, timestamp, weight)]
```

#### 核心算法
1. **最短传播路径**: BFS算法
2. **影响力传播路径**: Dijkstra变种（权重为影响力衰减）
3. **关键节点识别**: PageRank / 介数中心性
4. **传播模式识别**: 图聚类分析

#### 传播模式分类
- 星型传播: 单中心多点辐射
- 链式传播: 节点形成长链
- 病毒式传播: 指数级增长
- 社区传播: 多子群独立传播后汇合

### 3.4 突发事件检测算法

#### 三种检测方法

**方法1: STL分解 + 3σ异常检测**
```python
from statsmodels.tsa.seasonal import STL

stl = STL(time_series, period=24)  # 24小时周期
result = stl.fit()
residual = result.resid
anomalies = np.where(np.abs(residual) > 3 * residual.std())[0]
```

**方法2: PELT变点检测**
```python
import ruptures as rpt

algo = rpt.Pelt(model="rbf").fit(time_series)
change_points = algo.predict(pen=10)
```

**方法3: LSTM预测异常**
- 训练LSTM模型预测未来值
- 检测实际值与预测值的偏差
- 超过阈值即为异常

#### 突发定义
- 数量突发: 帖子数 > 历史均值×3σ
- 情感突发: 负面比例1小时上升>20%
- 速度突发: 热度增长速度 > 历史最快×2

### 3.5 KOL识别算法

#### 四维影响力评分

**维度1: 内容影响力 (40%)**
```python
内容影响力 = (平均点赞数×1 + 平均评论数×3 + 平均转发数×5) / 帖子数
爆款率 = 热度>90的帖子数 / 总帖子数
```

**维度2: 网络影响力 (30%)**
```python
PageRank分数 = 算法计算
介数中心性 = 算法计算
接近中心性 = 算法计算
粉丝数权重 = log(粉丝数 + 1)
```

**维度3: 话题引领力 (20%)**
```python
时间领先性 = 首发时间与话题热度峰值的时差
引用次数 = 其他帖子引用该用户帖子的次数
发起率 = 发起话题数 / 参与话题数
```

**维度4: 情感影响力 (10%)**
```python
情感传染率 = 跟帖情感与原帖情感一致的比例
情感引导力 = 后续讨论的情感倾向与该用户的相关性
```

#### KOL综合评分
```python
KOL得分 = 内容影响力×0.4
        + 网络影响力×0.3
        + 话题引领力×0.2
        + 情感影响力×0.1
```

### 3.6 舆情演化阶段识别

#### 六阶段生命周期模型

| 阶段 | 特征 | 识别条件 | 预计持续时间 |
|------|------|---------|-------------|
| 潜伏期 | 帖子少、情感中性 | 帖子 < 均值×1.2 | 不定 |
| 萌发期 | 开始增长 | 增长率 > 20% | 6-24h |
| 爆发期 | 指数增长 | 帖子 > 均值×3 | 12-48h |
| 扩散期 | 增长放缓 | 0 < 增长率 < 20% | 24-72h |
| 衰退期 | 开始下降 | 连续3h下降 | 24-96h |
| 消亡期 | 基本沉寂 | 帖子 < 峰值×0.1 | 不定 |

#### 阶段转换检测
```python
class OpinionEvolutionClassifier:
    def classify_stage(self, topic_id, metrics):
        # 基于当前指标判断阶段
        # 记录状态转换历史
        # 预测下一阶段和持续时间
```

---

## 四、下一步工作计划

### 4.1 后端实现（优先级排序）

#### 阶段1: 数据库模型扩展
**文件**: `backend/apps/analysis/models.py`

需要新增4个模型：
```python
class PropagationPath(models.Model):
    post = models.ForeignKey('posts.SocialPost')
    path_data = models.JSONField()
    depth = models.IntegerField()
    breadth = models.IntegerField()
    pattern = models.CharField(max_length=50)

class KOLProfile(models.Model):
    author = models.CharField(max_length=100)
    topic = models.ForeignKey('topics.Topic')
    kol_score = models.FloatField()
    kol_type = models.CharField(max_length=50)
    content_influence = models.FloatField()
    network_influence = models.FloatField()
    topic_leadership = models.FloatField()
    sentiment_influence = models.FloatField()

class EmergencyEvent(models.Model):
    topic = models.ForeignKey('topics.Topic')
    detected_at = models.DateTimeField(auto_now_add=True)
    event_type = models.CharField(max_length=50)
    severity = models.CharField(max_length=50)
    metrics = models.JSONField()
    status = models.CharField(max_length=50)
    alert_triggered = models.BooleanField(default=False)

class OpinionEvolution(models.Model):
    topic = models.ForeignKey('topics.Topic')
    stage = models.CharField(max_length=50)
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True)
    duration_hours = models.FloatField(null=True)
    peak_hotness = models.FloatField()
    transition_metrics = models.JSONField()
```

#### 阶段2: 核心算法模块

创建6个新文件：

1. **`backend/apps/analysis/sentiment_analyzer.py`**
   - `analyze_sentiment_multilevel(text)` - 五层次情感分析
   - `calculate_sentiment_intensity(text)` - 情感强度计算
   - `extract_sentiment_targets(text)` - 对象级情感提取
   - `track_sentiment_evolution(user_id, topic_id)` - 情感演化追踪

2. **`backend/apps/analysis/hotness_calculator.py`**
   - `calculate_hotness(post, current_time)` - 热度计算
   - `normalize_hotness_by_topic(posts, topic_id)` - 按话题归一化
   - `classify_hotness_level(score)` - 等级分类
   - `update_all_hotness()` - 批量更新所有帖子热度

3. **`backend/apps/analysis/propagation_analyzer.py`**
   - `build_propagation_graph(posts)` - 构建传播图
   - `find_propagation_paths(graph, source, max_depth)` - 发现传播路径
   - `identify_key_nodes(graph, top_k)` - 识别关键节点
   - `classify_propagation_pattern(graph)` - 传播模式分类

4. **`backend/apps/analysis/emergency_detector.py`**
   - `detect_anomaly_stl(time_series)` - STL异常检测
   - `detect_change_points(time_series)` - 变点检测
   - `detect_emergency_event(metrics)` - 综合突发检测
   - `trigger_emergency_alert(event)` - 触发预警

5. **`backend/apps/analysis/kol_detector.py`**
   - `calculate_content_influence(author)` - 内容影响力
   - `calculate_network_influence(author)` - 网络影响力
   - `calculate_topic_leadership(author, topic)` - 话题引领力
   - `calculate_sentiment_influence(author)` - 情感影响力
   - `calculate_kol_score(author, topic)` - KOL综合得分
   - `classify_kol_type(author, metrics)` - KOL类型分类

6. **`backend/apps/analysis/evolution_tracker.py`**
   - `classify_evolution_stage(topic_id, metrics)` - 阶段分类
   - `update_baseline(topic_id, metrics)` - 更新基线数据
   - `track_stage_transitions(topic_id)` - 跟踪阶段转换
   - `predict_next_stage(topic_id)` - 预测下一阶段

#### 阶段3: API端点实现
**文件**: `backend/apps/analysis/views.py`

新增6个ViewSet：
```python
class HotnessViewSet(viewsets.GenericViewSet):
    @action(detail=False, methods=['get'])
    def realtime(self, request):
        """实时热度排行"""

    @action(detail=False, methods=['get'])
    def trend(self, request):
        """热度趋势"""

    @action(detail=False, methods=['get'])
    def distribution(self, request):
        """等级分布"""

class PropagationViewSet(viewsets.GenericViewSet):
    @action(detail=False, methods=['get'])
    def paths(self, request):
        """传播路径"""

    @action(detail=False, methods=['get'])
    def key_nodes(self, request):
        """关键节点"""

    @action(detail=False, methods=['get'])
    def pattern(self, request):
        """传播模式"""

class EmergencyViewSet(viewsets.GenericViewSet):
    @action(detail=False, methods=['get'])
    def detect(self, request):
        """检测突发事件"""

    @action(detail=False, methods=['get'])
    def history(self, request):
        """历史事件"""

    @action(detail=False, methods=['post'])
    def resolve(self, request):
        """解决事件"""

class KOLViewSet(viewsets.GenericViewSet):
    @action(detail=False, methods=['get'])
    def ranking(self, request):
        """KOL排行"""

    @action(detail=False, methods=['get'])
    def profile(self, request):
        """KOL画像"""

    @action(detail=False, methods=['get'])
    def classify(self, request):
        """KOL分类"""

class EvolutionViewSet(viewsets.GenericViewSet):
    @action(detail=False, methods=['get'])
    def current_stage(self, request):
        """当前阶段"""

    @action(detail=False, methods=['get'])
    def history(self, request):
        """演化历史"""

    @action(detail=False, methods=['get'])
    def predict(self, request):
        """阶段预测"""

class SentimentAnalysisViewSet(viewsets.GenericViewSet):
    @action(detail=False, methods=['get'])
    def multilevel(self, request):
        """多层次情感分析"""

    @action(detail=False, methods=['get'])
    def intensity(self, request):
        """情感强度"""

    @action(detail=False, methods=['get'])
    def evolution(self, request):
        """情感演化"""
```

#### 阶段4: 定时任务
**文件**: `backend/apps/analysis/tasks.py`

新增5个定时任务：
```python
from celery import shared_task

@shared_task
def update_hotness_scores():
    """每5分钟更新热度分数"""
    pass

@shared_task
def detect_emergency_events():
    """每分钟检测突发事件"""
    pass

@shared_task
def update_kol_rankings():
    """每小时更新KOL排行"""
    pass

@shared_task
def analyze_evolution_stage():
    """每15分钟更新演化阶段"""
    pass

@shared_task
def build_propagation_graphs():
    """每小时构建传播图"""
    pass
```

#### 阶段5: 依赖包
**文件**: `backend/requirements.txt`

新增依赖：
```txt
# 深度学习
torch>=2.0.0
transformers>=4.30.0

# NLP
jieba>=0.42.1
snownlp>=0.12.3

# 时间序列分析
statsmodels>=0.14.0
ruptures>=1.1.0

# 图分析
networkx>=3.1

# 机器学习
scikit-learn>=1.3.0
```

### 4.2 实施顺序建议

1. **第一周**: 数据库模型 + 基础算法
   - 完成4个新模型的迁移
   - 实现热度计算算法（最基础）
   - 实现多层次情感分析（最重要）

2. **第二周**: API端点 + 前端联调
   - 实现6个ViewSet
   - 前端接入真实API
   - 基础功能测试

3. **第三周**: 高级算法
   - 传播路径分析
   - KOL识别算法
   - 突发事件检测

4. **第四周**: 智能预测
   - 舆情演化追踪
   - 定时任务配置
   - 系统优化和测试

---

## 五、关键文件清单

### 5.1 前端文件

**新建文件**:
```
frontend/src/views/Analysis/
├── HotnessView.vue        # 热度分析
├── PropagationView.vue    # 传播分析
├── EmergencyView.vue      # 突发事件
├── KOLView.vue           # KOL画像
└── EvolutionView.vue     # 舆情演化
```

**修改文件**:
```
frontend/src/router/index.js        # 新增5个路由
frontend/src/layout/MainLayout.vue  # 更新侧边栏菜单
frontend/src/api/analysis.js        # 新增18个API函数
```

### 5.2 后端文件（待创建）

**新建文件**:
```
backend/apps/analysis/
├── sentiment_analyzer.py    # 多层次情感分析
├── hotness_calculator.py    # 热度计算
├── propagation_analyzer.py  # 传播路径分析
├── emergency_detector.py    # 突发事件检测
├── kol_detector.py         # KOL识别
└── evolution_tracker.py    # 舆情演化追踪
```

**修改文件**:
```
backend/apps/analysis/models.py   # 新增4个模型
backend/apps/analysis/views.py    # 新增6个ViewSet
backend/apps/analysis/tasks.py    # 新增5个定时任务
backend/requirements.txt           # 新增算法依赖
backend/iot_system/settings.py     # 可能需要添加算法相关配置
```

---

## 六、验证方案

### 6.1 前端验证
```bash
# 启动前端
cd D:/lxr/wlw/frontend
npm run dev

# 访问系统
http://localhost:5173

# 验证步骤
1. 登录系统
2. 点击侧边栏"深度分析"分组下的5个新菜单
3. 验证页面能正常跳转和展示
4. 检查模拟数据显示正常
```

### 6.2 后端验证
```bash
# 1. 数据库迁移
cd D:/lxr/wlw/backend
python manage.py makemigrations analysis
python manage.py migrate

# 2. 启动Django服务
python manage.py runserver

# 3. 启动Celery worker
celery -A iot_system worker -l info

# 4. 测试API
curl http://localhost:8000/api/v1/analysis/hotness/realtime/?topic=1
curl http://localhost:8000/api/v1/analysis/emergency/detect/
```

### 6.3 集成验证

**测试场景1: 热度分析**
1. 创建测试话题
2. 生成100条测试帖子（不同互动数据）
3. 触发热度计算任务
4. 验证热度排行页面数据正确性

**测试场景2: 突发事件检测**
1. 模拟帖子数量突然增加
2. 触发突发事件检测任务
3. 验证事件被正确识别和记录
4. 前端突发事件页面正确显示

**测试场景3: KOL识别**
1. 创建测试用户数据
2. 模拟不同影响力用户的发帖行为
3. 触发KOL计算任务
4. 验证KOL排行和分类结果

---

## 七、技术难点与解决方案

### 7.1 难点1: 情感分析准确率
**问题**: 简单词典匹配准确率不足
**解决方案**:
- 使用预训练BERT模型微调
- 构建领域情感词典
- 规则+模型混合架构

### 7.2 难点2: 传播路径数据获取
**问题**: 社交媒体API限制，难以获取完整转发链
**解决方案**:
- 基于转发关系推断传播路径
- 使用时间序列近似传播路径
- 关键节点用PageRank识别

### 7.3 难点3: 实时性能
**问题**: 大数据量下计算耗时长
**解决方案**:
- 使用Celery异步任务
- Redis缓存计算结果
- 定时批量计算而非实时

### 7.4 难点4: 突发检测误报率
**问题**: 正常波动可能被识别为突发
**解决方案**:
- 多指标融合检测
- 添加冷却时间机制
- 支持误报标记和反馈学习

---

## 八、项目架构图

```
┌─────────────────────────────────────────────────────────┐
│                         前端层                          │
│  Vue 3 + Element Plus + ECharts                        │
│                                                          │
│  舆情总览 │ 话题管理 │ 帖子列表 │ 实时监控               │
│  ────────────────────────────────────────────            │
│  深度分析组: 情感│趋势│热度│传播│突发│KOL│演化      │
│  ────────────────────────────────────────────            │
│  预警中心 │ 预警规则 │ 数据报表 │ 用户管理 │ 系统设置   │
└─────────────────────────────────────────────────────────┘
                          ↕ HTTP/WebSocket
┌─────────────────────────────────────────────────────────┐
│                         API层                           │
│                    Django REST Framework                 │
│                                                          │
│  认证API │ 话题API │ 帖子API │ 分析API │ 预警API        │
└─────────────────────────────────────────────────────────┘
                          ↕
┌─────────────────────────────────────────────────────────┐
│                       业务逻辑层                         │
│                                                          │
│  情感分析模块 │ 热度计算模块 │ 传播分析模块               │
│  突发检测模块 │ KOL识别模块 │ 演化追踪模块               │
└─────────────────────────────────────────────────────────┘
                          ↕
┌─────────────────────────────────────────────────────────┐
│                       数据层                            │
│                                                          │
│  MySQL (关系数据) │ Redis (缓存/队列)                   │
│  Celery (异步任务) │ WebSocket (实时推送)                │
└─────────────────────────────────────────────────────────┘
```

---

## 九、下一步行动计划

### 立即执行（下个会话）
1. 创建数据库模型扩展文件
2. 实现热度计算算法模块
3. 实现多层次情感分析模块
4. 配置URL路由
5. 运行数据库迁移

### 后续任务
1. 实现6个ViewSet
2. 实现传播分析、KOL识别、突发事件检测模块
3. 配置Celery定时任务
4. 前端接入真实API
5. 系统测试和优化

---

## 十、重要提醒

### 10.1 注意事项
1. **前后端接口命名保持一致**: 前端API调用要与后端URL完全匹配
2. **数据格式规范**: 使用统一的日期格式（ISO 8601）
3. **错误处理**: 所有API都要有try-catch和适当的错误响应
4. **权限控制**: 新增的API也要检查用户权限
5. **性能优化**: 大数据量计算使用异步任务

### 10.2 待确认事项
1. ~~是否使用真实的深度学习模型？~~ 可能需要GPU资源
2. 是否需要实现完整的传播路径追踪？ 数据获取难度较大
3. 突发事件的阈值参数是否需要可配置？
4. KOL识别的各维度权重是否需要根据话题调整？

### 10.3 当前问题
1. 前端页面使用模拟数据，需要接入真实API
2. 后端算法模块尚未实现
3. 定时任务尚未配置
4. 数据库新增模型尚未迁移

---

**文档维护**: 请在每次重大更新后及时更新此文档
**最后更新**: 2025-01-29
**版本**: v1.0
