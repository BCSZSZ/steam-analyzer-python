"""
BERTopic Analyzer - discovers topics in Steam reviews using BERTopic.

Uses state-of-the-art topic modeling with semantic embeddings for
better topic quality compared to traditional LDA. Supports both
English and Chinese with language-specific preprocessing.
"""

from bertopic import BERTopic
from sentence_transformers import SentenceTransformer
from umap import UMAP
from hdbscan import HDBSCAN
from sklearn.feature_extraction.text import CountVectorizer
import json
import re
import os
from datetime import datetime
from .base_analyzer import BaseAnalyzer
from .text_processor import TextProcessor


class BERTopicAnalyzer(BaseAnalyzer):
    """
    Analyzes Steam reviews using BERTopic for topic discovery.
    
    Discovers coherent topics automatically using:
    - Semantic embeddings (sentence-transformers)
    - Dimensionality reduction (UMAP)
    - Density-based clustering (HDBSCAN)
    - Topic representation (c-TF-IDF)
    """
    
    def __init__(self):
        """Initialize BERTopic analyzer with text processor."""
        super().__init__()
        self.text_processor = TextProcessor()
        self.topic_model = None
        self.embeddings = None
        self.stopwords_file = 'data/stopwords.json'
        self.custom_stopwords = self._load_stopwords()
    
    def analyze(self, json_data, language='english', min_topic_size=10, 
                ngram_range=(1, 2), top_n_words=10, sentiment_filter=None):
        """
        Perform BERTopic analysis on reviews.
        
        Args:
            json_data: Raw review data from Steam API
            language: 'english' or 'schinese'
            min_topic_size: Minimum reviews per topic (smaller = more topics)
            ngram_range: N-gram range for topic words (e.g., (1, 2) for unigrams + bigrams)
            top_n_words: Number of representative words per topic
            sentiment_filter: 'positive', 'negative', or None (both)
        
        Returns:
            dict: Analysis results with topics and metadata
        """
        print(f"\n=== BERTopic Analysis ===")
        print(f"Language: {language}")
        print(f"Min Topic Size: {min_topic_size}")
        print(f"N-gram Range: {ngram_range}")
        print(f"Sentiment Filter: {sentiment_filter or 'All'}")
        
        # Extract reviews
        reviews = json_data.get('reviews', [])
        if not reviews:
            return {'error': 'No reviews found in data'}
        
        # Filter by language
        filtered_reviews = [
            r for r in reviews 
            if r.get('language') == language
        ]
        
        if not filtered_reviews:
            return {'error': f'No reviews found for language: {language}'}
        
        # Filter by sentiment if specified
        if sentiment_filter:
            voted_up = (sentiment_filter == 'positive')
            filtered_reviews = [
                r for r in filtered_reviews 
                if r.get('voted_up') == voted_up
            ]
            
            if not filtered_reviews:
                return {'error': f'No {sentiment_filter} reviews found'}
        
        print(f"Total reviews after filtering: {len(filtered_reviews)}")
        
        # Extract review texts
        documents = [r.get('review', '') for r in filtered_reviews]
        documents = [doc for doc in documents if doc.strip()]  # Remove empty
        
        if len(documents) < min_topic_size:
            return {
                'error': f'Insufficient reviews ({len(documents)}) for topic modeling. Need at least {min_topic_size}.'
            }
        
        print(f"Processing {len(documents)} reviews...")
        
        # Auto-add English game name to stopwords
        self._add_game_to_stopwords(json_data)
        
        # Preprocess documents with enhanced cleaning and tokenization
        processed_docs = self._preprocess_documents(documents, language)
        
        # Configure BERTopic model
        topic_model = self._create_topic_model(
            language=language,
            min_topic_size=min_topic_size,
            ngram_range=ngram_range,
            top_n_words=top_n_words
        )
        
        # Fit model and get topics
        print("Fitting BERTopic model...")
        topics, probs = topic_model.fit_transform(processed_docs)
        
        # Store for later use
        self.topic_model = topic_model
        
        # Get topic info
        topic_info = topic_model.get_topic_info()
        
        # Build results
        # Convert topics and probs to list if they aren't already
        topics_list = topics.tolist() if hasattr(topics, 'tolist') else list(topics)
        probs_list = probs.tolist() if probs is not None and hasattr(probs, 'tolist') else (list(probs) if probs is not None else None)
        
        results = {
            'metadata': {
                'total_reviews': len(filtered_reviews),
                'total_documents': len(documents),
                'language': language,
                'sentiment_filter': sentiment_filter,
                'min_topic_size': min_topic_size,
                'ngram_range': ngram_range,
                'top_n_words': top_n_words,
                'num_topics': len(topic_info) - 1,  # Exclude -1 (outliers)
                'analysis_date': datetime.now().isoformat()
            },
            'topics': self._extract_topic_details(topic_model, topic_info),
            'document_topics': topics_list,
            'topic_probabilities': probs_list,
            'outlier_count': sum(1 for t in topics_list if t == -1)
        }
        
        print(f"✓ Analysis complete! Found {results['metadata']['num_topics']} topics")
        print(f"  Outliers: {results['outlier_count']} reviews")
        
        return results
    
    def _preprocess_documents(self, documents, language):
        """
        Enhanced preprocessing for BERTopic with language-specific cleaning.
        
        Steps:
        1. Clean text (remove URLs, special chars)
        2. Remove English words (for Chinese) or game terms (for English)
        3. Tokenize with language-specific processor
        4. Remove stopwords
        5. Join tokens for embedding model
        
        Args:
            documents: List of review texts
            language: 'english' or 'schinese'
        
        Returns:
            List of preprocessed documents
        """
        processed = []
        
        for doc in documents:
            # Step 1: Basic cleaning
            doc = self.text_processor.clean_text(doc)
            
            if len(doc) < 10:
                continue
            
            # Step 2: Language-specific cleaning
            if language == 'schinese':
                # Remove ALL English words and URLs for Chinese analysis
                doc = re.sub(r'[a-zA-Z]+', '', doc)
                doc = re.sub(r'https?://\S+', '', doc)
                doc = re.sub(r'[0-9]+', '', doc)  # Remove standalone numbers
            
            # Step 3: Tokenize with stopword removal
            tokens = self.text_processor.tokenize(doc, language, remove_stopwords=True)
            
            if len(tokens) < 3:  # Skip if too few meaningful tokens
                continue
            
            # Step 4: Join tokens (space-separated for embedding model)
            processed_doc = ' '.join(tokens)
            
            if processed_doc.strip():
                processed.append(processed_doc)
        
        return processed
    
    def _create_topic_model(self, language, min_topic_size, ngram_range, top_n_words):
        """
        Create and configure BERTopic model.
        
        Args:
            language: 'english' or 'schinese'
            min_topic_size: Minimum cluster size
            ngram_range: N-gram range for topic representation
            top_n_words: Number of words per topic
        
        Returns:
            Configured BERTopic model
        """
        # Select language-specific embedding model
        print(f"Loading embedding model for {language}...")
        if language == 'schinese':
            # Chinese-specific model optimized for semantic understanding
            # Alternative: 'DMetaSoul/sbert-chinese-qmc-domain-v1' or 'uer/sbert-base-chinese-nli'
            embedding_model = SentenceTransformer('shibing624/text2vec-base-chinese')
            print("✓ Loaded Chinese-specific model: shibing624/text2vec-base-chinese")
        else:
            # English-specific model (faster and more accurate than multilingual)
            embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            print("✓ Loaded English-specific model: all-MiniLM-L6-v2")
        
        # Configure UMAP for dimensionality reduction
        umap_model = UMAP(
            n_neighbors=15,
            n_components=5,
            min_dist=0.0,
            metric='cosine',
            random_state=42
        )
        
        # Configure HDBSCAN for clustering
        hdbscan_model = HDBSCAN(
            min_cluster_size=min_topic_size,
            min_samples=3,
            metric='euclidean',
            cluster_selection_method='eom',
            prediction_data=True
        )
        
        # Configure CountVectorizer for topic representation
        # Combine built-in stopwords with custom stopwords
        stopwords = self.text_processor.get_stopwords(language)
        custom_stopwords = self._get_combined_stopwords(language)
        
        if stopwords:
            combined_stopwords = list(stopwords) + list(custom_stopwords)
        else:
            combined_stopwords = list(custom_stopwords)
        
        vectorizer_model = CountVectorizer(
            ngram_range=ngram_range,
            stop_words=combined_stopwords if combined_stopwords else None,
            min_df=10,     # Increased from 2: word must appear in 10+ documents
            max_df=0.3,    # NEW: ignore words in >30% of documents (too common)
        )
        
        # Create BERTopic model
        topic_model = BERTopic(
            embedding_model=embedding_model,
            umap_model=umap_model,
            hdbscan_model=hdbscan_model,
            vectorizer_model=vectorizer_model,
            top_n_words=top_n_words,
            language=language if language == 'english' else 'multilingual',
            calculate_probabilities=True,
            verbose=True
        )
        
        return topic_model
    
    def _extract_topic_details(self, topic_model, topic_info):
        """
        Extract detailed information for each topic.
        
        Args:
            topic_model: Fitted BERTopic model
            topic_info: DataFrame with topic information
        
        Returns:
            List of topic dictionaries
        """
        topics = []
        
        for _, row in topic_info.iterrows():
            topic_id = row['Topic']
            
            # Skip outlier topic (-1)
            if topic_id == -1:
                continue
            
            # Get topic words and scores
            topic_words = topic_model.get_topic(topic_id)
            
            topic_dict = {
                'topic_id': int(topic_id),
                'count': int(row['Count']),
                'name': row['Name'],
                'words': [
                    {
                        'word': word,
                        'score': float(score)
                    }
                    for word, score in topic_words
                ],
                'representative_docs': topic_model.get_representative_docs(topic_id)[:3]  # Top 3 examples
            }
            
            topics.append(topic_dict)
        
        return topics
    
    def save_analysis(self, results, appid, game_name, language):
        """
        Save BERTopic analysis results to JSON.
        
        Args:
            results: Analysis results dictionary
            appid: Steam App ID
            game_name: Game title
            language: Language code
        
        Returns:
            str: Path to saved file
        """
        sentiment = results['metadata'].get('sentiment_filter', 'all')
        date_str = datetime.now().strftime('%Y-%m-%d')
        
        filename = f"{appid}_{game_name}_{language}_{sentiment}_bertopic_{date_str}.json"
        
        return self.save_output(results, 'insights', filename)
    
    def get_topic_model(self):
        """
        Get the fitted BERTopic model for visualization.
        
        Returns:
            BERTopic model or None if not fitted
        """
        return self.topic_model
    
    def visualize_topics(self):
        """
        Generate interactive topic visualization using Plotly.
        
        Returns:
            Plotly figure object or None
        """
        if self.topic_model is None:
            return None
        
        try:
            # Generate intertopic distance map
            fig = self.topic_model.visualize_topics()
            return fig
        except Exception as e:
            print(f"Error generating visualization: {e}")
            return None
    
    def visualize_hierarchy(self):
        """
        Generate hierarchical topic clustering visualization.
        
        Returns:
            Plotly figure object or None
        """
        if self.topic_model is None:
            return None
        
        try:
            fig = self.topic_model.visualize_hierarchy()
            return fig
        except Exception as e:
            print(f"Error generating hierarchy: {e}")
            return None
    
    def visualize_barchart(self, top_n_topics=10):
        """
        Generate bar chart of top topics.
        
        Args:
            top_n_topics: Number of topics to display
        
        Returns:
            Plotly figure object or None
        """
        if self.topic_model is None:
            return None
        
        try:
            fig = self.topic_model.visualize_barchart(top_n_topics=top_n_topics)
            return fig
        except Exception as e:
            print(f"Error generating barchart: {e}")
            return None
    
    # ===== Stopwords Management =====
    
    def _load_stopwords(self):
        """
        Load custom stopwords from JSON file.
        
        Returns:
            dict: Stopwords dictionary
        """
        if not os.path.exists(self.stopwords_file):
            # Create default file if doesn't exist
            default_stopwords = {
                "universal": [
                    "dlc", "jrpg", "rpg", "fps", "moba", "mmo",
                    "spoiler", "review", "game", "gameplay",
                    "游戏", "评分", "好评", "差评",
                    "10", "9", "8", "sp", "ed", "op",
                    "https", "http", "www", "com",
                    "best", "indie", "year"
                ],
                "game_specific": {}
            }
            os.makedirs(os.path.dirname(self.stopwords_file), exist_ok=True)
            with open(self.stopwords_file, 'w', encoding='utf-8') as f:
                json.dump(default_stopwords, f, indent=2, ensure_ascii=False)
            return default_stopwords
        
        try:
            with open(self.stopwords_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading stopwords: {e}")
            return {"universal": [], "game_specific": {}}
    
    def _save_stopwords(self):
        """Save stopwords to JSON file."""
        try:
            with open(self.stopwords_file, 'w', encoding='utf-8') as f:
                json.dump(self.custom_stopwords, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving stopwords: {e}")
    
    def _add_game_to_stopwords(self, json_data):
        """
        Auto-add English game name from metadata to stopwords.
        
        Args:
            json_data: Review data with metadata
        """
        metadata = json_data.get('metadata', {})
        game_name = metadata.get('game_name', '')
        appid = metadata.get('appid', '')
        
        if not game_name or not appid:
            return
        
        # Create game key
        clean_name = game_name.lower().replace(' ', '_').replace("'", '')
        game_key = f"{appid}_{clean_name}"
        
        # Check if already exists
        if game_key in self.custom_stopwords.get('game_specific', {}):
            return
        
        # Tokenize English game name
        tokens = re.findall(r'\w+', game_name.lower())
        tokens = [t for t in tokens if len(t) > 2]  # Filter short tokens
        
        if tokens:
            # Add to game_specific
            if 'game_specific' not in self.custom_stopwords:
                self.custom_stopwords['game_specific'] = {}
            
            self.custom_stopwords['game_specific'][game_key] = tokens
            self._save_stopwords()
            print(f"✓ Auto-added game stopwords: {tokens}")
    
    def _get_combined_stopwords(self, language):
        """
        Get combined stopwords (universal + all game-specific).
        
        Args:
            language: 'english' or 'schinese'
        
        Returns:
            set: Combined stopwords
        """
        stopwords = set(self.custom_stopwords.get('universal', []))
        
        # Add all game-specific stopwords
        for game_terms in self.custom_stopwords.get('game_specific', {}).values():
            stopwords.update(game_terms)
        
        return stopwords
    
    def get_stopwords_dict(self):
        """Get current stopwords dictionary for UI editing."""
        return self.custom_stopwords
    
    def update_stopwords_dict(self, new_stopwords):
        """
        Update stopwords dictionary from UI.
        
        Args:
            new_stopwords: New stopwords dictionary
        """
        self.custom_stopwords = new_stopwords
        self._save_stopwords()
