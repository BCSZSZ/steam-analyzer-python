"""
Text Processing Utilities for Review Analysis.

Provides text cleaning, tokenization, and preprocessing for both English and Chinese text.
Handles language-specific processing with jieba for Chinese and NLTK for English.
"""

import re
import string
import jieba
from typing import List, Tuple
from collections import Counter


class TextProcessor:
    """
    Handles text preprocessing and tokenization for review analysis.
    
    Supports:
    - English: NLTK-based tokenization with stopword removal
    - Chinese: Jieba segmentation with custom stopword list
    """
    
    # Common English stopwords for review analysis
    ENGLISH_STOPWORDS = {
        'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', "you're",
        "you've", "you'll", "you'd", 'your', 'yours', 'yourself', 'yourselves', 'he',
        'him', 'his', 'himself', 'she', "she's", 'her', 'hers', 'herself', 'it', "it's",
        'its', 'itself', 'they', 'them', 'their', 'theirs', 'themselves', 'what', 'which',
        'who', 'whom', 'this', 'that', "that'll", 'these', 'those', 'am', 'is', 'are',
        'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'having', 'do',
        'does', 'did', 'doing', 'a', 'an', 'the', 'and', 'but', 'if', 'or', 'because',
        'as', 'until', 'while', 'of', 'at', 'by', 'for', 'with', 'about', 'against',
        'between', 'into', 'through', 'during', 'before', 'after', 'above', 'below',
        'to', 'from', 'up', 'down', 'in', 'out', 'on', 'off', 'over', 'under', 'again',
        'further', 'then', 'once', 'here', 'there', 'when', 'where', 'why', 'how', 'all',
        'both', 'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor',
        'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very', 's', 't', 'can',
        'will', 'just', 'don', "don't", 'should', "should've", 'now', 'd', 'll', 'm',
        'o', 're', 've', 'y', 'ain', 'aren', "aren't", 'couldn', "couldn't", 'didn',
        "didn't", 'doesn', "doesn't", 'hadn', "hadn't", 'hasn', "hasn't", 'haven',
        "haven't", 'isn', "isn't", 'ma', 'mightn', "mightn't", 'mustn', "mustn't",
        'needn', "needn't", 'shan', "shan't", 'shouldn', "shouldn't", 'wasn', "wasn't",
        'weren', "weren't", 'won', "won't", 'wouldn', "wouldn't"
    }
    
    # Common Chinese stopwords for review analysis
    CHINESE_STOPWORDS = {
        '的', '了', '和', '是', '在', '我', '有', '个', '不', '这', '你', '他', '她',
        '们', '也', '就', '都', '而', '及', '与', '着', '或', '一', '上', '下', '来',
        '去', '得', '到', '过', '能', '会', '可', '要', '说', '看', '让', '还', '用',
        '把', '被', '给', '没', '很', '比', '对', '于', '为', '从', '向', '以', '因',
        '由', '跟', '随', '等', '之', '但', '却', '又', '只', '当', '如', '若', '则',
        '将', '且', '并', '即', '便', '吧', '呢', '吗', '啊', '哦', '嗯', '哈', '呀',
        '哎', '哪', '什么', '怎么', '为什么', '多少', '几个', '这个', '那个', '这些',
        '那些', '这样', '那样', '怎样', '如何', '可以', '应该', '必须', '需要', '想要'
    }
    
    def __init__(self):
        """Initialize the text processor."""
        # Preload jieba for better performance
        jieba.initialize()
    
    def clean_text(self, text: str) -> str:
        """
        Clean text by removing URLs, special characters, and extra whitespace.
        
        Args:
            text: Raw text string
            
        Returns:
            Cleaned text string
        """
        if not text:
            return ""
        
        # Remove URLs
        text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
        
        # Remove Steam BBCode tags like [b], [/b], [i], [/i], etc.
        text = re.sub(r'\[/?[a-zA-Z]+\]', '', text)
        
        # Remove excessive punctuation (keep single punctuation)
        text = re.sub(r'([!?.,:;])\1+', r'\1', text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def tokenize_english(self, text: str, remove_stopwords: bool = True) -> List[str]:
        """
        Tokenize English text into words.
        
        Args:
            text: Cleaned English text
            remove_stopwords: Whether to remove common stopwords
            
        Returns:
            List of tokens (lowercase words)
        """
        # Convert to lowercase
        text = text.lower()
        
        # Remove punctuation and split into words
        # Keep apostrophes for contractions like "don't", "it's"
        text = re.sub(r'[^\w\s\']', ' ', text)
        tokens = text.split()
        
        # Remove tokens that are just numbers
        tokens = [t for t in tokens if not t.isdigit()]
        
        # Remove very short tokens (single characters except 'a' and 'i')
        tokens = [t for t in tokens if len(t) > 1 or t in ['a', 'i']]
        
        # Remove stopwords if requested
        if remove_stopwords:
            tokens = [t for t in tokens if t not in self.ENGLISH_STOPWORDS]
        
        return tokens
    
    def tokenize_chinese(self, text: str, remove_stopwords: bool = True) -> List[str]:
        """
        Tokenize Chinese text using jieba segmentation.
        
        Args:
            text: Cleaned Chinese text
            remove_stopwords: Whether to remove common stopwords
            
        Returns:
            List of tokens (Chinese words/phrases)
        """
        # Use jieba for Chinese word segmentation
        tokens = list(jieba.cut(text))
        
        # Remove whitespace and punctuation tokens
        tokens = [t.strip() for t in tokens if t.strip()]
        
        # Remove pure punctuation tokens
        tokens = [t for t in tokens if not all(c in string.punctuation + '！？。，、；：""''（）【】《》…—' for c in t)]
        
        # Remove single character tokens (often not meaningful in Chinese)
        tokens = [t for t in tokens if len(t) > 1]
        
        # Remove pure number tokens (like playtime hours)
        tokens = [t for t in tokens if not t.isdigit()]
        
        # Remove stopwords if requested
        if remove_stopwords:
            tokens = [t for t in tokens if t not in self.CHINESE_STOPWORDS]
        
        return tokens
    
    def tokenize(self, text: str, language: str, remove_stopwords: bool = True) -> List[str]:
        """
        Tokenize text based on language.
        
        Args:
            text: Text to tokenize
            language: 'english' or 'schinese' (Simplified Chinese)
            remove_stopwords: Whether to remove stopwords
            
        Returns:
            List of tokens
        """
        cleaned = self.clean_text(text)
        
        if language == 'english':
            return self.tokenize_english(cleaned, remove_stopwords)
        elif language == 'schinese':
            return self.tokenize_chinese(cleaned, remove_stopwords)
        else:
            # Fallback to simple whitespace tokenization
            return cleaned.lower().split()
    
    def generate_ngrams(self, tokens: List[str], n: int = 2, remove_repetitive: bool = True) -> List[Tuple[str, ...]]:
        """
        Generate n-grams from token list.
        
        Args:
            tokens: List of tokens
            n: Size of n-grams (1=unigrams, 2=bigrams, 3=trigrams)
            remove_repetitive: If True, filter out n-grams where all tokens are identical
                              (e.g., ('难评', '难评'), ('peak', 'peak'))
            
        Returns:
            List of n-gram tuples
        """
        if n < 1:
            raise ValueError("n must be at least 1")
        
        if len(tokens) < n:
            return []
        
        ngrams = []
        for i in range(len(tokens) - n + 1):
            ngram = tuple(tokens[i:i+n])
            
            # Filter out repetitive n-grams for n >= 2
            if remove_repetitive and n >= 2:
                # Check if all tokens in the n-gram are identical
                if len(set(ngram)) == 1:
                    # Skip this n-gram (e.g., ('难评', '难评') or ('peak', 'peak', 'peak'))
                    continue
            
            ngrams.append(ngram)
        
        return ngrams
    
    def count_ngrams(self, ngrams: List[Tuple[str, ...]], min_frequency: int = 1) -> List[Tuple[Tuple[str, ...], int]]:
        """
        Count n-gram frequencies and filter by minimum frequency.
        
        Args:
            ngrams: List of n-gram tuples
            min_frequency: Minimum frequency threshold
            
        Returns:
            List of (ngram, count) tuples sorted by count descending
        """
        counter = Counter(ngrams)
        
        # Filter by minimum frequency
        filtered = [(ngram, count) for ngram, count in counter.items() if count >= min_frequency]
        
        # Sort by count descending
        filtered.sort(key=lambda x: x[1], reverse=True)
        
        return filtered


def format_ngram(ngram: Tuple[str, ...]) -> str:
    """
    Format an n-gram tuple as a readable string.
    
    Args:
        ngram: Tuple of tokens
        
    Returns:
        Formatted string (space-separated for English, no space for Chinese)
    """
    # Check if it's Chinese by looking at the first character
    if ngram and any('\u4e00' <= c <= '\u9fff' for c in ngram[0]):
        # Chinese: no spaces between words
        return ''.join(ngram)
    else:
        # English: space-separated
        return ' '.join(ngram)
