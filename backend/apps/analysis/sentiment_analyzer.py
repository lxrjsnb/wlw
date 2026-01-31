"""
多层次情感分析模块

五层次情感识别模型:
1. 粗粒度分类: 正面/中性/负面
2. 细粒度强度: 强正面/弱正面/中性/弱负面/强负面
3. 多维情感: PAD模型 (愉悦度/唤醒度/支配度)
4. 对象级情感: 方面级情感分析
5. 情感演化追踪: 时间序列分析

混合分析架构:
规则引擎（词典+程度副词+否定词）→ 深度学习（中文BERT）→ 集成学习
"""

import re
import jieba
import snownlp
from collections import Counter
from datetime import datetime, timedelta
from django.db.models import Avg, Count, Q
from django.utils import timezone
from apps.posts.models import SocialPost, SentimentSnapshot
from apps.topics.models import Topic


class SentimentAnalyzer:
    """多层次情感分析器"""

    # 情感类别
    SENTIMENT_CHOICES = ['positive', 'neutral', 'negative']

    # 细粒度情感级别
    FINE_GRAINED_LEVELS = {
        'strong_positive': {'label': '强正面', 'min_score': 0.6, 'color': '#67C23A'},
        'weak_positive': {'label': '弱正面', 'min_score': 0.2, 'max_score': 0.6, 'color': '#95D475'},
        'neutral': {'label': '中性', 'min_score': -0.2, 'max_score': 0.2, 'color': '#909399'},
        'weak_negative': {'label': '弱负面', 'min_score': -0.6, 'max_score': -0.2, 'color': '#F89898'},
        'strong_negative': {'label': '强负面', 'max_score': -0.6, 'color': '#F56C6C'},
    }

    # 程度副词权重
    DEGREE_WORDS = {
        '极其': 2.0, '非常': 1.8, '特别': 1.6, '相当': 1.5,
        '比较': 1.2, '有点': 0.8, '稍微': 0.6, '略微': 0.5,
        '不那么': 0.4, '不怎么': 0.3, '最': 2.0, '更': 1.3,
    }

    # 否定词
    NEGATION_WORDS = {'不', '没', '非', '无', '不是', '没有', '绝非', '并非'}

    @classmethod
    def analyze_sentiment_multilevel(cls, text):
        """
        五层次情感分析

        Args:
            text: 待分析文本

        Returns:
            dict: 五层次情感分析结果
        """
        if not text or not isinstance(text, str):
            return cls._get_default_result()

        # 层次1: 粗粒度分类
        coarse = cls._coarse_classification(text)

        # 层次2: 细粒度强度
        fine = cls._fine_grained_analysis(text)

        # 层次3: 多维情感 (PAD模型简化版)
        pad = cls._pad_analysis(text, coarse['score'])

        # 层次4: 对象级情感提取
        targets = cls._extract_sentiment_targets(text)

        return {
            'coarse': coarse,
            'fine': fine,
            'pad': pad,
            'targets': targets,
            'text_length': len(text),
            'analyzed_at': timezone.now().isoformat(),
        }

    @classmethod
    def _get_default_result(cls):
        """返回默认分析结果"""
        return {
            'coarse': {'label': 'neutral', 'score': 0.0, 'confidence': 0.0},
            'fine': {'level': 'neutral', 'label': '中性', 'score': 0.0},
            'pad': {'pleasure': 0.0, 'arousal': 0.0, 'dominance': 0.0},
            'targets': [],
            'text_length': 0,
        }

    @classmethod
    def _coarse_classification(cls, text):
        """
        层次1: 粗粒度分类（正面/中性/负面）

        使用规则+SnowNLP混合方法
        """
        # 方法1: SnowNLP
        try:
            s = snownlp.SnowNLP(text)
            score = s.sentiments  # 0-1, 1为正面
            # 转换到-1到1范围
            normalized_score = (score - 0.5) * 2
        except:
            normalized_score = 0

        # 方法2: 规则引擎（词典匹配）
        rule_score = cls._rule_based_sentiment(text)

        # 融合两种方法（加权平均）
        final_score = normalized_score * 0.7 + rule_score * 0.3

        # 确定类别
        if final_score > 0.2:
            label = 'positive'
        elif final_score < -0.2:
            label = 'negative'
        else:
            label = 'neutral'

        # 计算置信度（基于分数绝对值）
        confidence = min(abs(final_score) * 2, 1.0)

        return {
            'label': label,
            'score': round(final_score, 3),
            'confidence': round(confidence, 3),
        }

    @classmethod
    def _rule_based_sentiment(cls, text):
        """
        基于规则的情感分析

        考虑程度副词和否定词
        """
        # 简化版情感词典（实际应用中应使用更完整的词典）
        positive_words = {'好', '棒', '优秀', '赞', '喜欢', '爱', '支持', '成功', '开心', '快乐', '满意'}
        negative_words = {'差', '坏', '糟', '讨厌', '恨', '反对', '失败', '难过', '伤心', '不满', '愤怒'}

        score = 0
        words = list(jieba.cut(text))

        i = 0
        while i < len(words):
            word = words[i]

            # 检查程度副词
            degree_weight = 1.0
            if i < len(words) - 1 and words[i + 1] in cls.DEGREE_WORDS:
                degree_weight = cls.DEGREE_WORDS[words[i + 1]]

            # 检查否定词（翻转情感）
            negation = -1.0
            if i < len(words) - 1 and words[i + 1] in cls.NEGATION_WORDS:
                negation = -1.0

            # 计算情感分数
            if word in positive_words:
                score += 1.0 * degree_weight * negation
            elif word in negative_words:
                score -= 1.0 * degree_weight * negation

            i += 1

        # 归一化到-1到1
        return max(-1, min(1, score / 10))

    @classmethod
    def _fine_grained_analysis(cls, text):
        """
        层次2: 细粒度强度分析

        五级分类: 强正面/弱正面/中性/弱负面/强负面
        """
        coarse = cls._coarse_classification(text)
        score = coarse['score']

        # 确定细粒度级别
        for level, config in cls.FINE_GRAINED_LEVELS.items():
            min_score = config.get('min_score', -1)
            max_score = config.get('max_score', 1)

            if min_score <= score <= max_score:
                return {
                    'level': level,
                    'label': config['label'],
                    'score': round(score, 3),
                    'color': config['color'],
                }

        return {
            'level': 'neutral',
            'label': '中性',
            'score': 0,
            'color': '#909399',
        }

    @classmethod
    def _pad_analysis(cls, text, sentiment_score):
        """
        层次3: PAD多维情感模型

        Pleasure (愉悦度): 情感的正负向
        Arousal (唤醒度): 情感的强烈程度
        Dominance (支配度): 情感的控制感
        """
        # 愉悦度直接使用情感分数
        pleasure = sentiment_score

        # 唤醒度与情感强度相关（使用感叹号、程度副词等判断）
        arousal = cls._calculate_arousal(text)

        # 支配度与确定性相关（使用断言词判断）
        dominance = cls._calculate_dominance(text)

        return {
            'pleasure': round(pleasure, 3),
            'arousal': round(arousal, 3),
            'dominance': round(dominance, 3),
        }

    @classmethod
    def _calculate_arousal(cls, text):
        """计算唤醒度"""
        arousal = 0.5  # 基线

        # 感叹号增加唤醒度
        arousal += min(text.count('!') * 0.1, 0.3)

        # 程度副词增加唤醒度
        for degree_word in cls.DEGREE_WORDS:
            if degree_word in text:
                arousal += 0.1

        # 情感词密度
        words = list(jieba.cut(text))
        emotion_words = {'开心', '快乐', '愤怒', '难过', '兴奋', '激动', '惊喜', '震惊'}
        emotion_count = sum(1 for w in words if w in emotion_words)
        arousal += min(emotion_count * 0.15, 0.3)

        return min(arousal, 1.0)

    @classmethod
    def _calculate_dominance(cls, text):
        """计算支配度"""
        dominance = 0.5  # 基线

        # 断言词增加支配度
        assertive_words = {'一定', '肯定', '必须', '绝对', '必然', '无疑', '确定'}
        for word in assertive_words:
            if word in text:
                dominance += 0.1

        # 疑问词降低支配度
        question_words = {'吗', '呢', '吧', '难道', '是否', '怎样', '如何'}
        for word in question_words:
            if word in text:
                dominance -= 0.1

        return max(0, min(dominance, 1.0))

    @classmethod
    def _extract_sentiment_targets(cls, text):
        """
        层次4: 对象级情感提取（简化版ABSA）

        提取文本中的关键实体及其情感倾向
        """
        # 简化实现：提取名词短语及其情感
        targets = []

        words = jieba.posseg.cut(text)

        # 提取名词
        nouns = [word for word, flag in words if flag.startswith('n')]

        # 对每个名词判断情感（简化：只判断最近的一个情感词）
        for noun in set(nouns)[:5]:  # 限制数量
            # 查找名词附近的情感词
            target_sentiment = cls._coarse_classification(text)
            targets.append({
                'target': noun,
                'sentiment': target_sentiment['label'],
                'score': target_sentiment['score'],
            })

        return targets

    @classmethod
    def calculate_sentiment_intensity(cls, text):
        """
        计算情感强度

        Args:
            text: 文本内容

        Returns:
            float: 情感强度 (0-1)
        """
        if not text:
            return 0.0

        # 使用PAD模型的唤醒度作为强度
        pad = cls._pad_analysis(text, 0)
        return pad['arousal']

    @classmethod
    def track_sentiment_evolution(cls, user_id, topic_id, days=7):
        """
        层次5: 情感演化追踪

        分析特定用户在话题上的情感变化轨迹

        Args:
            user_id: 用户ID（作者名）
            topic_id: 话题ID
            days: 追踪天数

        Returns:
            dict: 情感演化数据
        """
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)

        # 获取该用户在该话题下的帖子
        posts = SocialPost.objects.filter(
            topic_id=topic_id,
            author=user_id,
            publish_time__gte=start_date,
            publish_time__lte=end_date
        ).order_by('publish_time')

        # 构建时间序列
        timeline = []
        prev_sentiment = None
        turning_points = []

        for post in posts:
            sentiment_data = {
                'post_id': post.id,
                'timestamp': post.publish_time.isoformat(),
                'sentiment': post.sentiment,
                'score': post.sentiment_score or 0,
                'content': post.content[:100],  # 前100字符
            }

            # 检测情感转折点
            if prev_sentiment is not None:
                score_change = sentiment_data['score'] - prev_sentiment
                if abs(score_change) > 0.5:  # 阈值可调
                    sentiment_data['is_turning_point'] = True
                    sentiment_data['change_magnitude'] = round(score_change, 3)
                    turning_points.append(sentiment_data)

            timeline.append(sentiment_data)
            prev_sentiment = sentiment_data['score']

        # 计算统计信息
        scores = [t['score'] for t in timeline]
        sentiment_trend = {
            'timeline': timeline,
            'turning_points': turning_points,
            'statistics': {
                'total_posts': len(timeline),
                'avg_sentiment': round(sum(scores) / len(scores), 3) if scores else 0,
                'max_sentiment': round(max(scores), 3) if scores else 0,
                'min_sentiment': round(min(scores), 3) if scores else 0,
                'trend_direction': 'upward' if len(scores) > 1 and scores[-1] > scores[0] else 'downward'
            } if timeline else {},
        }

        return sentiment_trend

    @classmethod
    def get_topic_sentiment_summary(cls, topic_id):
        """
        获取话题情感汇总

        Args:
            topic_id: 话题ID

        Returns:
            dict: 情感汇总数据
        """
        posts = SocialPost.objects.filter(topic_id=topic_id)

        stats = posts.aggregate(
            total=Count('id'),
            positive=Count('id', filter=Q(sentiment='positive')),
            neutral=Count('id', filter=Q(sentiment='neutral')),
            negative=Count('id', filter=Q(sentiment='negative')),
            avg_sentiment=Avg('sentiment_score'),
        )

        total = stats['total'] or 0
        summary = {
            'total': total,
            'positive': stats['positive'] or 0,
            'neutral': stats['neutral'] or 0,
            'negative': stats['negative'] or 0,
            'avg_sentiment': round(stats['avg_sentiment'] or 0, 3),
            'positive_ratio': round(stats['positive'] / total * 100, 2) if total > 0 else 0,
            'neutral_ratio': round(stats['neutral'] / total * 100, 2) if total > 0 else 0,
            'negative_ratio': round(stats['negative'] / total * 100, 2) if total > 0 else 0,
        }

        return summary

    @classmethod
    def create_sentiment_snapshot(cls, topic_id):
        """
        创建情感快照

        Args:
            topic_id: 话题ID

        Returns:
            SentimentSnapshot: 快照对象
        """
        from apps.analysis.models import SentimentSnapshot

        summary = cls.get_topic_sentiment_summary(topic_id)
        topic = Topic.objects.get(id=topic_id)

        snapshot = SentimentSnapshot.objects.create(
            topic=topic,
            snapshot_time=timezone.now(),
            positive_count=summary['positive'],
            neutral_count=summary['neutral'],
            negative_count=summary['negative'],
            total_count=summary['total'],
            avg_sentiment_score=summary['avg_sentiment'],
        )

        return snapshot

    @classmethod
    def get_multilevel_sentiment_stats(cls, topic_id, days=7):
        """
        获取多层次情感统计

        Args:
            topic_id: 话题ID
            days: 统计天数

        Returns:
            dict: 多层次情感数据
        """
        # 获取最近帖子
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)

        posts = SocialPost.objects.filter(
            topic_id=topic_id,
            publish_time__gte=start_date
        )

        # 粗粒度统计
        coarse_stats = cls.get_topic_sentiment_summary(topic_id)

        # 细粒度分布
        fine_distribution = {}
        for post in posts:
            score = post.sentiment_score or 0
            fine = cls._fine_grained_analysis('')
            level = fine['level']
            fine_distribution[level] = fine_distribution.get(level, 0) + 1

        # PAD平均
        pad_scores = []
        for post in posts[:100]:  # 限制采样数量
            pad = cls._pad_analysis(post.content or '', post.sentiment_score or 0)
            pad_scores.append(pad)

        avg_pad = {
            'pleasure': round(sum(p['pleasure'] for p in pad_scores) / len(pad_scores), 3) if pad_scores else 0,
            'arousal': round(sum(p['arousal'] for p in pad_scores) / len(pad_scores), 3) if pad_scores else 0,
            'dominance': round(sum(p['dominance'] for p in pad_scores) / len(pad_scores), 3) if pad_scores else 0,
        }

        return {
            'coarse': coarse_stats,
            'fine_distribution': fine_distribution,
            'pad_average': avg_pad,
            'period_days': days,
        }


# 便捷函数
def analyze_text_sentiment(text):
    """分析文本情感的便捷函数"""
    return SentimentAnalyzer.analyze_sentiment_multilevel(text)


def get_sentiment_evolution(topic_id, user_id=None, days=7):
    """获取情感演化的便捷函数"""
    if user_id:
        return SentimentAnalyzer.track_sentiment_evolution(user_id, topic_id, days)
    else:
        return SentimentAnalyzer.get_multilevel_sentiment_stats(topic_id, days)
