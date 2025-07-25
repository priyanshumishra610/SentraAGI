"""
Phase 1 Tests for OMNIMIND

Tests for ingest → chunk → embed → vector store → KG → basic retrieval pipeline.
"""

import pytest
import tempfile
import os
from unittest.mock import Mock, patch

# Test data
SAMPLE_TEXT = """
OMNIMIND is an autonomous, self-simulating, self-evolving cognitive kernel. 
It retrieves trusted knowledge from vast sources, verifies information with multi-agent swarm debate, 
and simulates reality when facts are missing. The system maintains a living Knowledge Graph, 
Vector DB & Thought Snapshots, self-repairs failing pipelines using genetic algorithms, 
and anchors its answers with cryptographic proof trails.
"""

SAMPLE_URLS = [
    "https://example.com/article1",
    "https://example.com/article2"
]

SAMPLE_FILES = [
    "test_document1.txt",
    "test_document2.txt"
]


class TestBasicLoader:
    """Test the basic loader functionality."""
    
    def test_loader_initialization(self):
        """Test loader can be initialized."""
        from crawlers.basic_loader import BasicLoader
        loader = BasicLoader()
        assert loader is not None
        assert loader.timeout == 30
        assert loader.max_retries == 3
    
    def test_url_detection(self):
        """Test URL detection logic."""
        from crawlers.basic_loader import BasicLoader
        loader = BasicLoader()
        
        assert loader._is_url("https://example.com") == True
        assert loader._is_url("http://example.com") == True
        assert loader._is_url("not_a_url") == False
        assert loader._is_url("/local/path") == False
    
    def test_file_loading(self):
        """Test local file loading."""
        from crawlers.basic_loader import BasicLoader
        
        # Create temporary test file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(SAMPLE_TEXT)
            temp_file = f.name
        
        try:
            loader = BasicLoader()
            result = loader.load_file(temp_file)
            
            assert result["success"] == True
            assert result["content"] == SAMPLE_TEXT
            assert result["content_type"] == "text/plain"
            assert result["size_bytes"] > 0
        finally:
            os.unlink(temp_file)


class TestSmartChunker:
    """Test the smart chunker functionality."""
    
    def test_chunker_initialization(self):
        """Test chunker can be initialized."""
        from chunker.chunker import SmartChunker
        chunker = SmartChunker()
        assert chunker is not None
        assert chunker.chunk_size == 1000
        assert chunker.overlap == 200
    
    def test_text_chunking(self):
        """Test text chunking functionality."""
        from chunker.chunker import SmartChunker
        chunker = SmartChunker(chunk_size=200, overlap=50)
        
        chunks = chunker.chunk_text(SAMPLE_TEXT)
        
        assert len(chunks) > 0
        for chunk in chunks:
            assert "text" in chunk
            assert "chunk_id" in chunk
            assert "start" in chunk
            assert "end" in chunk
            assert len(chunk["text"]) <= 200
    
    def test_chunk_stats(self):
        """Test chunk statistics calculation."""
        from chunker.chunker import SmartChunker
        chunker = SmartChunker()
        
        chunks = chunker.chunk_text(SAMPLE_TEXT)
        stats = chunker.get_chunk_stats(chunks)
        
        assert "total_chunks" in stats
        assert "avg_size" in stats
        assert "total_text" in stats
        assert stats["total_chunks"] == len(chunks)


class TestMultiModelEmbedder:
    """Test the multi-model embedder functionality."""
    
    def test_embedder_initialization(self):
        """Test embedder can be initialized."""
        from embedder.embedder import MultiModelEmbedder
        embedder = MultiModelEmbedder()
        assert embedder is not None
        assert embedder.model_name == "text-embedding-ada-002"
    
    def test_text_embedding(self):
        """Test text embedding functionality."""
        from embedder.embedder import MultiModelEmbedder
        embedder = MultiModelEmbedder()
        
        embedding = embedder.embed_text("Test text for embedding")
        
        assert len(embedding) > 0
        assert all(isinstance(x, (int, float)) for x in embedding)
    
    def test_embedding_stats(self):
        """Test embedding statistics calculation."""
        from embedder.embedder import MultiModelEmbedder
        embedder = MultiModelEmbedder()
        
        embeddings = [
            embedder.embed_text("Text 1"),
            embedder.embed_text("Text 2"),
            embedder.embed_text("Text 3")
        ]
        
        stats = embedder.get_embedding_stats(embeddings)
        
        assert "total_embeddings" in stats
        assert "embedding_dim" in stats
        assert "model_used" in stats
        assert stats["total_embeddings"] == 3


class TestVectorDB:
    """Test the vector database functionality."""
    
    def test_vectordb_initialization(self):
        """Test vector database can be initialized."""
        from vectordb.vectordb import VectorDB
        vectordb = VectorDB()
        assert vectordb is not None
        assert vectordb.backend in ["faiss", "simple"]
    
    def test_collection_creation(self):
        """Test collection creation."""
        from vectordb.vectordb import VectorDB
        vectordb = VectorDB()
        
        success = vectordb.create_collection("test_collection")
        assert success == True
        
        stats = vectordb.get_collection_stats("test_collection")
        assert "error" not in stats
    
    def test_vector_storage_and_search(self):
        """Test vector storage and search functionality."""
        from vectordb.vectordb import VectorDB
        from embedder.embedder import MultiModelEmbedder
        
        vectordb = VectorDB()
        embedder = MultiModelEmbedder()
        
        # Create test vectors
        test_texts = ["First document", "Second document", "Third document"]
        test_vectors = []
        
        for i, text in enumerate(test_texts):
            embedding = embedder.embed_text(text)
            test_vectors.append({
                "text": text,
                "embedding": embedding,
                "document_id": f"doc_{i}",
                "chunk_id": f"chunk_{i}"
            })
        
        # Store vectors
        success = vectordb.add_vectors("test_collection", test_vectors)
        assert success == True
        
        # Search vectors
        query_embedding = embedder.embed_text("First document")
        results = vectordb.search("test_collection", query_embedding, top_k=2)
        
        assert len(results) > 0
        assert "similarity" in results[0]
        assert "rank" in results[0]


class TestKnowledgeGraph:
    """Test the knowledge graph functionality."""
    
    def test_kg_initialization(self):
        """Test knowledge graph can be initialized."""
        from kg.kg_manager import KnowledgeGraphManager
        kg = KnowledgeGraphManager(use_neo4j=False)
        assert kg is not None
        assert kg.use_neo4j == False
    
    def test_entity_creation(self):
        """Test entity creation."""
        from kg.kg_manager import KnowledgeGraphManager
        kg = KnowledgeGraphManager(use_neo4j=False)
        
        success = kg.add_entity(
            entity_id="test_entity",
            entity_type="document",
            properties={"title": "Test Document", "source": "test"}
        )
        assert success == True
    
    def test_relationship_creation(self):
        """Test relationship creation."""
        from kg.kg_manager import KnowledgeGraphManager
        kg = KnowledgeGraphManager(use_neo4j=False)
        
        # Add entities first
        kg.add_entity("entity1", "document", {"title": "Doc 1"})
        kg.add_entity("entity2", "chunk", {"text": "Chunk 1"})
        
        # Add relationship
        success = kg.add_relationship(
            source_id="entity1",
            target_id="entity2",
            relationship_type="contains"
        )
        assert success == True
    
    def test_graph_stats(self):
        """Test graph statistics."""
        from kg.kg_manager import KnowledgeGraphManager
        kg = KnowledgeGraphManager(use_neo4j=False)
        
        # Add some test data
        kg.add_entity("entity1", "document", {"title": "Doc 1"})
        kg.add_entity("entity2", "chunk", {"text": "Chunk 1"})
        kg.add_relationship("entity1", "entity2", "contains")
        
        stats = kg.get_graph_stats()
        
        assert "total_entities" in stats
        assert "total_relationships" in stats
        assert "entity_types" in stats
        assert "relationship_types" in stats
        assert stats["total_entities"] == 2
        assert stats["total_relationships"] == 1


class TestPipeline:
    """Test the complete pipeline functionality."""
    
    def test_pipeline_initialization(self):
        """Test pipeline can be initialized."""
        from pipelines.pipeline import OMNIMINDPipeline
        pipeline = OMNIMINDPipeline()
        assert pipeline is not None
        assert len(pipeline.steps) == 4
    
    def test_pipeline_execution(self):
        """Test pipeline execution with mock data."""
        from pipelines.pipeline import OMNIMINDPipeline
        
        # Create temporary test file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(SAMPLE_TEXT)
            temp_file = f.name
        
        try:
            pipeline = OMNIMINDPipeline()
            result = pipeline.run([temp_file])
            
            assert "pipeline_success" in result
            assert "steps_executed" in result
            assert "execution_history" in result
        finally:
            os.unlink(temp_file)


class TestAPIEndpoints:
    """Test API endpoints."""
    
    def test_health_check(self):
        """Test basic health check endpoint."""
        from fastapi.testclient import TestClient
        from api.routes.health import router as health_router
        
        client = TestClient(health_router)
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "timestamp" in data
        assert data["status"] == "ok"
    
    @patch("vectordb.vectordb.VectorDB")
    @patch("embedder.embedder.MultiModelEmbedder")
    def test_vector_search(self, mock_embedder_class, mock_vectordb_class):
        """Test vector search endpoint with mocked dependencies."""
        from fastapi.testclient import TestClient
        from api.routes.search import router as search_router
        
        # Mock embedder
        mock_embedder = Mock()
        mock_embedder.embed_text.return_value = [0.1, 0.2, 0.3]  # Mock embedding vector
        mock_embedder_class.return_value = mock_embedder
        
        # Mock vectordb
        mock_vectordb = Mock()
        mock_vectordb.search.return_value = [
            {"id": "1", "text": "Test result 1", "similarity": 0.9},
            {"id": "2", "text": "Test result 2", "similarity": 0.8}
        ]
        mock_vectordb_class.return_value = mock_vectordb
        
        client = TestClient(search_router)
        response = client.post(
            "/search",
            json={
                "query": "test query",
                "collection": "test_collection",
                "top_k": 2
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert len(data["results"]) == 2
        assert data["results"][0]["score"] == 0.9
        assert data["results"][0]["text"] == "Test result 1"
        
        # Verify mocks were called correctly
        mock_embedder.embed_text.assert_called_once_with("test query")
        mock_vectordb.search.assert_called_once_with(
            "test_collection",
            [0.1, 0.2, 0.3],
            top_k=2
        )
    
    @patch("kg.kg_manager.KnowledgeGraphManager")
    def test_kg_query(self, mock_kg_class):
        """Test knowledge graph query endpoint with mocked dependencies."""
        from fastapi.testclient import TestClient
        from api.routes.knowledge import router as kg_router
        
        # Mock KG manager
        mock_kg = Mock()
        mock_kg.query.return_value = {
            "entities": [
                {
                    "id": "e1",
                    "type": "concept",
                    "name": "Test Entity",
                    "properties": {"key": "value"}
                }
            ],
            "relationships": [
                {
                    "source": "e1",
                    "target": "e2",
                    "type": "related_to",
                    "properties": {"weight": 0.8}
                }
            ]
        }
        mock_kg_class.return_value = mock_kg
        
        client = TestClient(kg_router)
        response = client.post(
            "/kg/query",
            json={
                "query": "test query",
                "limit": 10
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "entities" in data
        assert "relationships" in data
        assert len(data["entities"]) == 1
        assert len(data["relationships"]) == 1
        
        # Verify entity data
        entity = data["entities"][0]
        assert entity["id"] == "e1"
        assert entity["type"] == "concept"
        assert entity["name"] == "Test Entity"
        assert entity["properties"] == {"key": "value"}
        
        # Verify relationship data
        relationship = data["relationships"][0]
        assert relationship["source"] == "e1"
        assert relationship["target"] == "e2"
        assert relationship["type"] == "related_to"
        assert relationship["properties"] == {"weight": 0.8}
        
        # Verify mock was called correctly
        mock_kg.query.assert_called_once_with(
            query="test query",
            limit=10
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 