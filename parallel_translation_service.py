"""Service for handling parallel translation processing."""
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Optional, Tuple
from queue import Queue
import threading
from .translation_service import TranslationService
from utils.text_chunker import TextChunker

logger = logging.getLogger(__name__)

class ParallelTranslationService:
    def __init__(
        self,
        max_workers: int = 3,
        chunk_size: int = 1000,
        batch_size: int = 10
    ):
        self.max_workers = max_workers
        self.chunk_size = chunk_size
        self.batch_size = batch_size
        self.translation_service = TranslationService()
        self.text_chunker = TextChunker(max_chunk_size=chunk_size)
        self.results_queue: Queue = Queue()
        self.translation_lock = threading.Lock()

    def translate_content(self, content_map: Dict[str, str]) -> Dict[str, str]:
        """
        Translate multiple content pieces in parallel.
        
        Args:
            content_map: Dictionary of {content_id: content}
            
        Returns:
            Dict[str, str]: Dictionary of {content_id: translated_content}
        """
        chunks_map: Dict[str, List[Tuple[int, str]]] = {}
        
        # Split all content into chunks first
        for content_id, content in content_map.items():
            chunks = self.text_chunker.split_into_chunks(content)
            chunks_map[content_id] = list(enumerate(chunks))
            
        # Create translation tasks
        translation_tasks = []
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            for content_id, chunks in chunks_map.items():
                for chunk_batch in self._create_batches(chunks):
                    task = executor.submit(
                        self._translate_batch,
                        content_id,
                        chunk_batch
                    )
                    translation_tasks.append(task)
            
            # Process completed translations
            for future in as_completed(translation_tasks):
                try:
                    result = future.result()
                    if result:
                        self.results_queue.put(result)
                except Exception as e:
                    logger.error(f"Translation task failed: {str(e)}")
        
        # Combine results
        return self._combine_results(chunks_map)

    def _create_batches(
        self,
        chunks: List[Tuple[int, str]]
    ) -> List[List[Tuple[int, str]]]:
        """Create batches of chunks for translation."""
        return [
            chunks[i:i + self.batch_size]
            for i in range(0, len(chunks), self.batch_size)
        ]

    def _translate_batch(
        self,
        content_id: str,
        chunk_batch: List[Tuple[int, str]]
    ) -> Optional[Tuple[str, List[Tuple[int, str]]]]:
        """Translate a batch of chunks."""
        try:
            translated_chunks = []
            for idx, chunk in chunk_batch:
                with self.translation_lock:  # Ensure thread-safe API access
                    translated_text = self.translation_service._translate_text(chunk)
                    if translated_text:
                        translated_chunks.append((idx, translated_text))
            
            return content_id, translated_chunks
            
        except Exception as e:
            logger.error(f"Batch translation failed: {str(e)}")
            return None

    def _combine_results(
        self,
        chunks_map: Dict[str, List[Tuple[int, str]]]
    ) -> Dict[str, str]:
        """Combine translated chunks back into complete content."""
        results: Dict[str, Dict[int, str]] = {
            content_id: {} for content_id in chunks_map
        }
        
        # Process all results from the queue
        while not self.results_queue.empty():
            content_id, translated_chunks = self.results_queue.get()
            for idx, text in translated_chunks:
                results[content_id][idx] = text
        
        # Combine chunks in correct order
        combined_results = {}
        for content_id, chunks in results.items():
            if not chunks:
                continue
                
            ordered_chunks = [
                chunks.get(i, '')
                for i in range(len(chunks_map[content_id]))
            ]
            combined_results[content_id] = '\n'.join(
                chunk for chunk in ordered_chunks if chunk
            )
        
        return combined_results
