"""
Word Cloud Generator - creates visual word clouds from analysis results.

Generates word clouds from N-gram and TF-IDF analysis results with
customizable colors and sizes based on frequencies or scores.
"""

from wordcloud import WordCloud
import matplotlib.pyplot as plt
from PIL import Image
import io
import os
import platform


class WordCloudGenerator:
    """
    Generates word cloud visualizations from text analysis results.
    
    Supports:
    - N-gram frequency word clouds
    - TF-IDF distinctive term word clouds
    - Custom color schemes
    - Adjustable sizes and parameters
    """
    
    def __init__(self):
        """Initialize word cloud generator with default settings."""
        self.default_width = 1200
        self.default_height = 600
        self.default_background = 'white'
        self.chinese_font = self._get_chinese_font()
    
    def generate_from_ngrams(self, ngram_results, max_words=100, colormap='viridis', language='english'):
        """
        Generate word cloud from N-gram analysis results.
        
        Args:
            ngram_results: List of dicts with 'ngram' and 'count' keys
            max_words: Maximum number of words to display
            colormap: Matplotlib colormap name (e.g., 'viridis', 'plasma', 'Blues')
            language: 'english' or 'schinese' for font selection
        
        Returns:
            PIL.Image: Word cloud image, or None if insufficient data
        """
        if not ngram_results:
            return None
        
        # Convert n-grams to frequency dictionary
        frequencies = {}
        for item in ngram_results[:max_words]:
            ngram = item.get('ngram', '')
            count = item.get('count', 0)
            if ngram and count > 0:
                frequencies[ngram] = count
        
        if not frequencies:
            return None
        
        # Use Chinese font if language is Chinese
        font_path = self.chinese_font if language == 'schinese' else None
        
        # Generate word cloud
        # relative_scaling: 0.3 = less difference between biggest/smallest words
        # prefer_horizontal: 1.0 = all words horizontal, 0.5 = 50/50 mix
        wordcloud = WordCloud(
            width=self.default_width,
            height=self.default_height,
            background_color=self.default_background,
            colormap=colormap,
            max_words=max_words,
            relative_scaling=0.3,  # Reduced from 0.5 to decrease size variance
            min_font_size=12,      # Increased from 10 to make small words more readable
            max_font_size=80,      # Cap maximum size to reduce extremes
            prefer_horizontal=1.0, # All words horizontal (no vertical text)
            font_path=font_path
        ).generate_from_frequencies(frequencies)
        
        return self._wordcloud_to_image(wordcloud)
    
    def generate_from_tfidf(self, tfidf_terms, max_words=50, colormap='Greens', sentiment='positive', language='english'):
        """
        Generate word cloud from TF-IDF distinctive terms.
        
        Args:
            tfidf_terms: List of dicts with 'term' and 'score' keys
            max_words: Maximum number of words to display
            colormap: Matplotlib colormap name
                     - 'Greens' for positive terms
                     - 'Reds' for negative terms
            sentiment: 'positive' or 'negative' (for labeling)
            language: 'english' or 'schinese' for font selection
        
        Returns:
            PIL.Image: Word cloud image, or None if insufficient data
        """
        if not tfidf_terms:
            return None
        
        # Convert terms to frequency dictionary (using scores as weights)
        frequencies = {}
        for item in tfidf_terms[:max_words]:
            term = item.get('term', '')
            score = item.get('score', 0.0)
            if term and score > 0:
                # Scale scores to reasonable range for word cloud
                frequencies[term] = score * 1000
        
        if not frequencies:
            return None
        
        # Use Chinese font if language is Chinese
        font_path = self.chinese_font if language == 'schinese' else None
        
        # Generate word cloud
        # relative_scaling: 0.3 = less difference between biggest/smallest words
        # prefer_horizontal: 1.0 = all words horizontal
        wordcloud = WordCloud(
            width=self.default_width // 2,  # Half width for side-by-side display
            height=self.default_height,
            background_color=self.default_background,
            colormap=colormap,
            max_words=max_words,
            relative_scaling=0.3,  # Reduced from 0.5 to decrease size variance
            min_font_size=12,      # Increased from 10 to make small words more readable
            max_font_size=80,      # Cap maximum size to reduce extremes
            prefer_horizontal=1.0, # All words horizontal (no vertical text)
            font_path=font_path
        ).generate_from_frequencies(frequencies)
        
        return self._wordcloud_to_image(wordcloud)
    
    def generate_dual_tfidf(self, positive_terms, negative_terms, max_words=50, language='english'):
        """
        Generate side-by-side word clouds for positive and negative terms.
        
        Args:
            positive_terms: List of positive distinctive terms
            negative_terms: List of negative distinctive terms
            max_words: Maximum words per cloud
            language: 'english' or 'schinese' for font selection
        
        Returns:
            tuple: (positive_image, negative_image) as PIL Images
        """
        positive_cloud = self.generate_from_tfidf(
            positive_terms, 
            max_words=max_words, 
            colormap='Greens',
            sentiment='positive',
            language=language
        )
        
        negative_cloud = self.generate_from_tfidf(
            negative_terms, 
            max_words=max_words, 
            colormap='Reds',
            sentiment='negative',
            language=language
        )
        
        return positive_cloud, negative_cloud
    
    def _wordcloud_to_image(self, wordcloud):
        """
        Convert WordCloud object to PIL Image.
        
        Args:
            wordcloud: WordCloud object
        
        Returns:
            PIL.Image: Image object
        """
        # Convert to numpy array then to PIL Image
        img_array = wordcloud.to_array()
        return Image.fromarray(img_array)
    
    def save_image(self, image, filepath):
        """
        Save word cloud image to file.
        
        Args:
            image: PIL Image object
            filepath: Path to save file (should end in .png)
        
        Returns:
            bool: True if saved successfully
        """
        try:
            if image:
                image.save(filepath, 'PNG')
                return True
        except Exception as e:
            print(f"Error saving image: {e}")
        return False
    
    def _get_chinese_font(self):
        """
        Detect and return path to Chinese font.
        
        Returns:
            str: Path to Chinese font, or None if not found
        """
        system = platform.system()
        
        # Common Chinese font paths by OS
        font_paths = []
        
        if system == 'Windows':
            font_paths = [
                'C:/Windows/Fonts/simhei.ttf',  # SimHei
                'C:/Windows/Fonts/msyh.ttc',    # Microsoft YaHei
                'C:/Windows/Fonts/simsun.ttc',  # SimSun
                'C:/Windows/Fonts/simkai.ttf',  # KaiTi
            ]
        elif system == 'Darwin':  # macOS
            font_paths = [
                '/System/Library/Fonts/PingFang.ttc',
                '/Library/Fonts/Arial Unicode.ttf',
            ]
        else:  # Linux
            font_paths = [
                '/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf',
                '/usr/share/fonts/truetype/wqy/wqy-microhei.ttc',
                '/usr/share/fonts/truetype/arphic/uming.ttc',
            ]
        
        # Find first available font
        for font_path in font_paths:
            if os.path.exists(font_path):
                return font_path
        
        # If no font found, return None (will use default)
        print("Warning: No Chinese font found, Chinese characters may not display correctly")
        return None
    
    def create_empty_placeholder(self, text="No data available"):
        """
        Create a placeholder image when no data is available.
        
        Args:
            text: Message to display
        
        Returns:
            PIL.Image: Placeholder image
        """
        # Create a simple placeholder
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.text(0.5, 0.5, text, 
                ha='center', va='center',
                fontsize=16, color='gray')
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
        
        # Convert to PIL Image
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight', dpi=100)
        buf.seek(0)
        plt.close(fig)
        
        return Image.open(buf)
