"""
传播路径分析模块

核心功能:
1. 构建传播图 (基于转发关系和时间序列)
2. 发现传播路径 (BFS/最短路径/影响力路径)
3. 识别关键节点 (PageRank/中心性分析)
4. 传播模式分类 (星型/链式/病毒式/社区)
"""

import json
from collections import defaultdict, deque
from datetime import datetime, timedelta
from django.db.models import Q, Count, Avg, Max
from django.utils import timezone
import networkx as nx
from apps.posts.models import SocialPost
from apps.analysis.models import PropagationPath


class PropagationAnalyzer:
    """传播分析器"""

    # 传播模式定义
    PATTERNS = {
        'star': '星型传播',  # 单中心多点辐射
        'chain': '链式传播',  # 节点形成长链
        'viral': '病毒式传播',  # 指数级增长
        'community': '社区传播',  # 多子群独立传播
        'unknown': '未知',
    }

    @classmethod
    def build_propagation_graph(cls, posts, max_nodes=500):
        """
        构建传播图

        基于转发关系和时间序列推断传播路径

        Args:
            posts: SocialPost查询集或列表
            max_nodes: 最大节点数（限制计算复杂度）

        Returns:
            nx.DiGraph: 有向图对象
        """
        G = nx.DiGraph()

        # 转换为列表（如果是查询集）
        if not isinstance(posts, list):
            posts = list(posts[:max_nodes])

        # 按发布时间排序
        posts_sorted = sorted(posts, key=lambda p: p.publish_time or timezone.now())

        # 添加节点
        for post in posts_sorted:
            node_id = post.author  # 简化：使用作者作为节点
            G.add_node(
                node_id,
                post_id=post.id,
                timestamp=post.publish_time,
                sentiment=post.sentiment,
                likes=post.likes,
                comments=post.comments,
                shares=post.shares,
            )

        # 添加边（基于时间窗口和内容相似度推断转发关系）
        # 简化策略：如果用户A发帖后，用户B在24小时内发布了相似内容的帖子，则认为存在传播
        time_window = timedelta(hours=24)

        for i, post_a in enumerate(posts_sorted):
            for post_b in posts_sorted[i + 1:]:
                # 检查时间窗口
                if post_b.publish_time and post_a.publish_time:
                    time_diff = post_b.publish_time - post_a.publish_time
                    if time_diff > time_window:
                        break  # 超出时间窗口

                    # 检查内容相似度（简化：检查是否有共同关键词）
                    if cls._has_content_similarity(post_a, post_b):
                        # 权重基于时间差（越早权重越高）
                        weight = max(0, 1 - time_diff.total_seconds() / (24 * 3600))
                        G.add_edge(post_a.author, post_b.author, weight=weight)

        return G

    @classmethod
    def _has_content_similarity(cls, post_a, post_b, threshold=0.3):
        """
        检查两篇帖子内容是否相似

        简化实现：基于关键词重叠度
        """
        keywords_a = set(post_a.keywords or [])
        keywords_b = set(post_b.keywords or [])

        if not keywords_a or not keywords_b:
            return False

        # 计算Jaccard相似度
        intersection = len(keywords_a & keywords_b)
        union = len(keywords_a | keywords_b)

        if union == 0:
            return False

        similarity = intersection / union
        return similarity >= threshold

    @classmethod
    def find_propagation_paths(cls, graph, source, max_depth=5, max_paths=10):
        """
        发现传播路径

        Args:
            graph: NetworkX图对象
            source: 源节点ID
            max_depth: 最大深度
            max_paths: 最大路径数

        Returns:
            list: 传播路径列表
        """
        if source not in graph:
            return []

        paths = []

        # BFS找所有路径
        queue = deque([(source, [source])])

        while queue and len(paths) < max_paths:
            node, path = queue.popleft()

            if len(path) > max_depth:
                continue

            # 获取邻居
            for neighbor in graph.successors(node):
                if neighbor not in path:  # 避免循环
                    new_path = path + [neighbor]
                    paths.append(new_path)
                    queue.append((neighbor, new_path))

        # 格式化路径
        formatted_paths = []
        for path in paths:
            path_data = {
                'nodes': path,
                'length': len(path) - 1,
                'nodes_data': [
                    {
                        'author': node,
                        **graph.nodes[node]
                    }
                    for node in path if node in graph.nodes
                ]
            }
            formatted_paths.append(path_data)

        return formatted_paths[:max_paths]

    @classmethod
    def identify_key_nodes(cls, graph, top_k=10):
        """
        识别关键传播节点

        使用多种中心性指标综合评估

        Args:
            graph: NetworkX图对象
            top_k: 返回前K个节点

        Returns:
            list: 关键节点列表，按影响力排序
        """
        if graph.number_of_nodes() == 0:
            return []

        key_nodes = []

        # 1. PageRank (最重要的指标)
        try:
            pagerank = nx.pagerank(graph, weight='weight')
        except:
            pagerank = {node: 0 for node in graph.nodes()}

        # 2. 介数中心性
        try:
            betweenness = nx.betweenness_centrality(graph, weight='weight')
        except:
            betweenness = {node: 0 for node in graph.nodes()}

        # 3. 接近中心性
        try:
            closeness = nx.closeness_centrality(graph)
        except:
            closeness = {node: 0 for node in graph.nodes()}

        # 4. 出度（传播广度）
        out_degree = dict(graph.out_degree())

        # 5. 入度（被引用次数）
        in_degree = dict(graph.in_degree())

        # 综合评分
        for node in graph.nodes():
            # 归一化各指标
            pr_score = pagerank.get(node, 0)
            bc_score = betweenness.get(node, 0)
            cc_score = closeness.get(node, 0)

            # 加权综合得分
            composite_score = (
                pr_score * 0.4 +      # PageRank权重最高
                bc_score * 0.3 +       # 介数中心性
                cc_score * 0.2 +       # 接近中心性
                out_degree.get(node, 0) * 0.05 +  # 传播广度
                in_degree.get(node, 0) * 0.05     # 被引用次数
            )

            key_nodes.append({
                'author': node,
                'pagerank': round(pr_score, 4),
                'betweenness': round(bc_score, 4),
                'closeness': round(cc_score, 4),
                'out_degree': out_degree.get(node, 0),
                'in_degree': in_degree.get(node, 0),
                'composite_score': round(composite_score, 4),
                'node_data': graph.nodes.get(node, {}),
            })

        # 按综合得分排序
        key_nodes.sort(key=lambda x: x['composite_score'], reverse=True)

        return key_nodes[:top_k]

    @classmethod
    def classify_propagation_pattern(cls, graph):
        """
        传播模式分类

        Args:
            graph: NetworkX图对象

        Returns:
            dict: 传播模式信息
        """
        if graph.number_of_nodes() == 0:
            return {'pattern': 'unknown', 'confidence': 0, 'features': {}}

        # 计算图特征
        features = cls._calculate_graph_features(graph)

        # 基于特征判断模式
        pattern = cls._classify_pattern_by_features(features)

        return {
            'pattern': pattern,
            'label': cls.PATTERNS.get(pattern, '未知'),
            'confidence': round(features.get('confidence', 0.5), 2),
            'features': features,
        }

    @classmethod
    def _calculate_graph_features(cls, graph):
        """计算图的结构特征"""
        features = {}

        # 1. 节点数和边数
        features['node_count'] = graph.number_of_nodes()
        features['edge_count'] = graph.number_of_edges()

        if features['node_count'] == 0:
            return features

        # 2. 平均度
        degrees = [d for n, d in graph.degree()]
        features['avg_degree'] = round(sum(degrees) / len(degrees), 2) if degrees else 0

        # 3. 密度
        features['density'] = round(nx.density(graph), 4)

        # 4. 直径（最短路径最长值）
        try:
            features['diameter'] = nx.diameter(graph)
        except:
            features['diameter'] = 0

        # 5. 平均路径长度
        try:
            features['avg_path_length'] = round(nx.average_shortest_path_length(graph), 2)
        except:
            features['avg_path_length'] = 0

        # 6. 聚类系数
        try:
            features['clustering_coefficient'] = round(nx.average_clustering(graph), 4)
        except:
            features['clustering_coefficient'] = 0

        # 7. 强连通分量数
        try:
            features['scc_count'] = nx.number_strongly_connected_components(graph)
        except:
            features['scc_count'] = 0

        # 8. 度分布方差（衡量是否均匀）
        if degrees:
            mean_deg = sum(degrees) / len(degrees)
            variance = sum((d - mean_deg) ** 2 for d in degrees) / len(degrees)
            features['degree_variance'] = round(variance, 2)
        else:
            features['degree_variance'] = 0

        return features

    @classmethod
    def _classify_pattern_by_features(cls, features):
        """基于特征分类传播模式"""
        # 规则分类器

        # 星型传播：高密度、低直径、高度方差（少数节点度很高）
        if (features.get('density', 0) > 0.3 and
            features.get('diameter', 0) <= 3 and
            features.get('degree_variance', 0) > features.get('avg_degree', 0) ** 2):
            return 'star'

        # 链式传播：低密度、高直径、低聚类系数
        if (features.get('density', 0) < 0.2 and
            features.get('diameter', 0) > 5 and
            features.get('clustering_coefficient', 0) < 0.3):
            return 'chain'

        # 病毒式传播：指数增长特征（边数远大于节点数）
        edge_count = features.get('edge_count', 0)
        node_count = features.get('node_count', 1)
        if edge_count > node_count * 1.5 and features.get('density', 0) > 0.4:
            return 'viral'

        # 社区传播：多个强连通分量、高聚类系数
        if features.get('scc_count', 0) > 2 and features.get('clustering_coefficient', 0) > 0.5:
            return 'community'

        return 'unknown'

    @classmethod
    def analyze_propagation(cls, post_id):
        """
        完整分析单个帖子的传播情况

        Args:
            post_id: 帖子ID

        Returns:
            PropagationPath: 传播路径对象
        """
        try:
            post = SocialPost.objects.get(id=post_id)
        except SocialPost.DoesNotExist:
            return None

        # 获取相关帖子（同话题、时间窗口内）
        time_window = timedelta(hours=48)
        related_posts = SocialPost.objects.filter(
            topic=post.topic,
            publish_time__gte=post.publish_time,
            publish_time__lte=post.publish_time + time_window
        )

        # 构建传播图
        graph = cls.build_propagation_graph(related_posts)

        if graph.number_of_nodes() == 0:
            return None

        # 分析传播路径
        paths = cls.find_propagation_paths(graph, post.author)

        # 识别关键节点
        key_nodes = cls.identify_key_nodes(graph, top_k=10)

        # 分类传播模式
        pattern_info = cls.classify_propagation_pattern(graph)

        # 计算传播深度和广度
        depth = cls._calculate_depth(graph, post.author)
        breadth = graph.number_of_nodes()

        # 计算传播速度
        speed = cls._calculate_speed(related_posts)

        # 保存到数据库
        propagation_path = PropagationPath.objects.create(
            post=post,
            path_data={
                'nodes': list(graph.nodes()),
                'edges': list(graph.edges(data=True)),
            },
            depth=depth,
            breadth=breadth,
            speed=speed,
            pattern=pattern_info['pattern'],
            key_nodes=key_nodes[:10],  # 存储Top 10
            total_nodes=graph.number_of_nodes(),
            total_edges=graph.number_of_edges(),
        )

        return propagation_path

    @classmethod
    def _calculate_depth(cls, graph, source):
        """计算传播深度（BFS最大深度）"""
        if source not in graph:
            return 0

        visited = {source}
        queue = deque([(source, 0)])
        max_depth = 0

        while queue:
            node, depth = queue.popleft()
            max_depth = max(max_depth, depth)

            for neighbor in graph.successors(node):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, depth + 1))

        return max_depth

    @classmethod
    def _calculate_speed(cls, posts):
        """计算传播速度（每小时新增节点数）"""
        if not posts.exists():
            return 0

        first_post = posts.order_by('publish_time').first()
        last_post = posts.order_by('-publish_time').first()

        if not first_post.publish_time or not last_post.publish_time:
            return 0

        time_diff = (last_post.publish_time - first_post.publish_time).total_seconds() / 3600  # 小时

        if time_diff == 0:
            return 0

        return round(posts.count() / time_diff, 2)

    @classmethod
    def get_propagation_stats(cls, topic_id):
        """
        获取话题的传播统计概览

        Args:
            topic_id: 话题ID

        Returns:
            dict: 传播统计数据
        """
        # 获取最近的传播分析记录
        paths = PropagationPath.objects.filter(
            post__topic_id=topic_id
        ).order_by('-created_at')[:100]

        if not paths:
            return {
                'total_analyzed': 0,
                'avg_depth': 0,
                'avg_breadth': 0,
                'avg_speed': 0,
                'pattern_distribution': {},
            }

        # 计算统计值
        total = paths.count()
        avg_depth = sum(p.depth for p in paths) / total
        avg_breadth = sum(p.breadth for p in paths) / total
        avg_speed = sum(p.speed for p in paths) / total

        # 模式分布
        pattern_dist = defaultdict(int)
        for p in paths:
            pattern_dist[p.pattern] += 1

        return {
            'total_analyzed': total,
            'avg_depth': round(avg_depth, 2),
            'avg_breadth': round(avg_breadth, 2),
            'avg_speed': round(avg_speed, 2),
            'pattern_distribution': {
                pattern: {'count': count, 'label': cls.PATTERNS.get(pattern, '未知')}
                for pattern, count in pattern_dist.items()
            },
        }


# 便捷函数
def analyze_post_propagation(post_id):
    """分析帖子传播的便捷函数"""
    return PropagationAnalyzer.analyze_propagation(post_id)


def get_topic_propagation_stats(topic_id):
    """获取话题传播统计的便捷函数"""
    return PropagationAnalyzer.get_propagation_stats(topic_id)
