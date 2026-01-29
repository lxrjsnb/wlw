"""
情感分析服务
"""
import re
import random
from typing import Dict, List, Optional
import jieba
from jieba import analyse


class SentimentAnalyzer:
    """情感分析服务"""

    # 情感词典
    POSITIVE_WORDS = [
        '好', '棒', '优秀', '优秀', '赞', '支持', '喜欢', '爱', '开心', '快乐',
        '满意', '值得', '推荐', '期待', '精彩', '完美', '给力', '强', '牛',
        '厉害', '厉害', '感动', '感谢', '幸福', '美丽', '漂亮', '棒极了', '太棒了',
        '真好', '非常好', '不错', '可以', '行', '对', '是', '同意', '认同',
        '有道理', '说得好', '说得对', '有建设性', '有意义', '有价值', '正面',
        '积极', '向上', '阳光', '热情', '友好', '和善', '亲切', '温暖', '舒适'
    ]

    NEGATIVE_WORDS = [
        '差', '烂', '垃圾', '恶心', '讨厌', '恨', '愤怒', '生气', '不爽', '失望',
        '难过', '伤心', '痛苦', '糟糕', '坏', '弱', '低劣', '劣质', '次品', '假',
        '虚伪', '欺骗', '骗子', '坑', '坑爹', '坑人', '无聊', '没意思', '不好',
        '不行', '不可以', '不对', '不是', '反对', '不认同', '不赞成', '质疑',
        '怀疑', '担忧', '焦虑', '紧张', '恐惧', '害怕', '惊慌', '混乱', '麻烦',
        '困扰', '烦恼', '痛苦', '恶劣', '残酷', '冷漠', '无情', '讽刺', '嘲笑',
        '鄙视', '轻视', '忽视', '无视', '否定', '拒绝', '排斥', '抵制', '反对',
        '抗议', '谴责', '批评', '指责', '抨击', '攻击', '谩骂', '辱骂', '侮辱'
    ]

    def __init__(self):
        """初始化分词器"""
        # 设置jieba分词模式
        jieba.setLogLevel(jieba.logging.INFO)

    def analyze(self, text: str) -> Dict:
        """
        分析文本情感

        Args:
            text: 待分析的文本

        Returns:
            dict: {
                'sentiment': 'positive'/'neutral'/'negative',
                'score': float (情感分数 -1到1),
                'keywords': list (关键词列表)
            }
        """
        if not text or not isinstance(text, str):
            return {
                'sentiment': 'neutral',
                'score': 0.0,
                'keywords': []
            }

        # 提取关键词
        keywords = self.extract_keywords(text, topK=5)

        # 计算情感分数
        sentiment_score = self.calculate_sentiment_score(text)

        # 判断情感倾向
        if sentiment_score > 0.3:
            sentiment = 'positive'
        elif sentiment_score < -0.3:
            sentiment = 'negative'
        else:
            sentiment = 'neutral'

        # 归一化分数到-1到1之间
        normalized_score = max(-1.0, min(1.0, sentiment_score))

        return {
            'sentiment': sentiment,
            'sentiment_score': round(normalized_score, 3),
            'keywords': keywords
        }

    def calculate_sentiment_score(self, text: str) -> float:
        """计算情感分数"""
        score = 0.0
        text_lower = text.lower()

        # 正面词计数
        positive_count = sum(1 for word in self.POSITIVE_WORDS if word in text_lower)
        # 负面词计数
        negative_count = sum(1 for word in self.NEGATIVE_WORDS if word in text_lower)

        total = positive_count + negative_count
        if total == 0:
            return 0.0

        # 计算分数 (-1 到 1)
        score = (positive_count - negative_count) / max(total, 1)

        # 考虑标点符号的强调
        if '！' in text or '!' in text:
            score *= 1.2
        if '！！！' in text or '!!!' in text:
            score *= 1.5

        # 考虑重复词的强调
        for word in self.POSITIVE_WORDS:
            if word * 2 in text_lower:  # 如"好好好"
                score += 0.2
        for word in self.NEGATIVE_WORDS:
            if word * 2 in text_lower:
                score -= 0.2

        return score

    def extract_keywords(self, text: str, topK: int = 5) -> List[str]:
        """提取关键词"""
        try:
            # 使用TF-IDF算法提取关键词
            keywords = jieba.analyse.extract_tags(
                text,
                topK=topK,
                withWeight=False,
                allowPOS=('n', 'vn', 'v', 'a')  # 名词、动名词、动词、形容词
            )
            return keywords[:topK]
        except Exception as e:
            # 如果提取失败，使用简单分词
            words = jieba.cut(text)
            return [w for w in words if len(w) >= 2][:topK]

    def batch_analyze(self, texts: List[str]) -> List[Dict]:
        """批量分析文本情感"""
        return [self.analyze(text) for text in texts]


class SentimentKeywordExtractor:
    """情感关键词提取器"""

    def __init__(self):
        self.analyzer = SentimentAnalyzer()

    def extract_with_sentiment(self, text: str, topK: int = 10) -> List[Dict]:
        """
        提取带情感标签的关键词

        Returns:
            [
                {'word': '关键词', 'sentiment': 'positive', 'weight': 0.8},
                ...
            ]
        """
        keywords = self.analyzer.extract_keywords(text, topK=topK * 2)

        results = []
        for word in keywords[:topK]:
            # 判断单个词的情感
            word_score = self.analyzer.calculate_sentiment_score(word)
            if word_score > 0.1:
                sentiment = 'positive'
            elif word_score < -0.1:
                sentiment = 'negative'
            else:
                sentiment = 'neutral'

            results.append({
                'word': word,
                'sentiment': sentiment,
                'weight': abs(word_score)
            })

        return results
