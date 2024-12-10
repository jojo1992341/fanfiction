"""Utility for breaking down text into manageable chunks."""
import re
from typing import List
import logging

logger = logging.getLogger(__name__)

class TextChunker:
    def __init__(self, max_chunk_size: int = 1000):
        self.max_chunk_size = max_chunk_size
        
    def split_into_chunks(self, text: str) -> List[str]:
        """
        Split text into smaller chunks while preserving paragraph structure.
        
        Args:
            text: Text content to split
            
        Returns:
            List[str]: List of text chunks
        """
        if not text:
            return []
            
        # Split into paragraphs first
        paragraphs = self._split_into_paragraphs(text)
        
        chunks = []
        current_chunk = []
        current_size = 0
        
        for para in paragraphs:
            para_size = len(para)
            
            if para_size > self.max_chunk_size:
                # If we have accumulated content, add it as a chunk
                if current_chunk:
                    chunks.append('\n'.join(current_chunk))
                    current_chunk = []
                    current_size = 0
                
                # Split large paragraph into sentences
                para_chunks = self._split_paragraph(para)
                chunks.extend(para_chunks)
                
            elif current_size + para_size > self.max_chunk_size:
                # Current paragraph would exceed chunk size, start new chunk
                chunks.append('\n'.join(current_chunk))
                current_chunk = [para]
                current_size = para_size
                
            else:
                # Add paragraph to current chunk
                current_chunk.append(para)
                current_size += para_size
        
        # Add any remaining content
        if current_chunk:
            chunks.append('\n'.join(current_chunk))
            
        return chunks
        
    def _split_into_paragraphs(self, text: str) -> List[str]:
        """Split text into paragraphs."""
        # Split on double newlines or other paragraph markers
        paragraphs = re.split(r'\n\s*\n|\r\n\s*\r\n', text)
        return [p.strip() for p in paragraphs if p.strip()]
        
    def _split_paragraph(self, paragraph: str) -> List[str]:
        """Split a large paragraph into smaller chunks by sentences."""
        sentences = re.split(r'(?<=[.!?])\s+', paragraph)
        chunks = []
        current_chunk = []
        current_size = 0
        
        for sentence in sentences:
            sentence_size = len(sentence)
            
            if sentence_size > self.max_chunk_size:
                # Handle extremely long sentences
                if current_chunk:
                    chunks.append(' '.join(current_chunk))
                    current_chunk = []
                    current_size = 0
                
                # Split by phrase markers
                phrase_chunks = self._split_sentence(sentence)
                chunks.extend(phrase_chunks)
                
            elif current_size + sentence_size > self.max_chunk_size:
                chunks.append(' '.join(current_chunk))
                current_chunk = [sentence]
                current_size = sentence_size
                
            else:
                current_chunk.append(sentence)
                current_size += sentence_size
        
        if current_chunk:
            chunks.append(' '.join(current_chunk))
            
        return chunks
        
    def _split_sentence(self, sentence: str) -> List[str]:
        """Split a very long sentence into phrase chunks."""
        # Split on phrase markers like commas, semicolons, etc.
        phrases = re.split(r'(?<=[,;:])\s+', sentence)
        chunks = []
        current_chunk = []
        current_size = 0
        
        for phrase in phrases:
            phrase_size = len(phrase)
            
            if phrase_size > self.max_chunk_size:
                # If still too long, split arbitrarily
                if current_chunk:
                    chunks.append(' '.join(current_chunk))
                    current_chunk = []
                    current_size = 0
                
                # Split into fixed-size chunks as last resort
                while phrase:
                    chunks.append(phrase[:self.max_chunk_size])
                    phrase = phrase[self.max_chunk_size:]
                    
            elif current_size + phrase_size > self.max_chunk_size:
                chunks.append(' '.join(current_chunk))
                current_chunk = [phrase]
                current_size = phrase_size
                
            else:
                current_chunk.append(phrase)
                current_size += phrase_size
        
        if current_chunk:
            chunks.append(' '.join(current_chunk))
            
        return chunks
