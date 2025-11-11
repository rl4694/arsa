import pytest
from unittest.mock import patch, MagicMock
import data.db_connect as dbc


@pytest.fixture(autouse=True)
def _reset_client():
    """Reset the global client before and after each test."""
    original_client = dbc.client
    dbc.client = None
    yield
    dbc.client = original_client


class TestConnectDB:
    """Test the connect_db function."""
    
    @patch('data.db_connect.pm.MongoClient')
    @patch.dict('os.environ', {'CLOUD_MONGO': '0'}, clear=False)
    def test_connect_local(self, mock_client):
        """Test connecting to MongoDB locally."""
        mock_mongo = MagicMock()
        mock_client.return_value = mock_mongo
        
        result = dbc.connect_db()
        
        # Should call MongoClient without arguments for local connection
        mock_client.assert_called_once_with()
        assert result == mock_mongo
        assert dbc.client == mock_mongo
    
    @patch('data.db_connect.pm.MongoClient')
    @patch.dict('os.environ', {'CLOUD_MONGO': '1', 'MONGO_PASSWD': 'test_password'}, clear=False)
    def test_connect_cloud_with_password(self, mock_client):
        """Test connecting to MongoDB in the cloud with a password."""
        mock_mongo = MagicMock()
        mock_client.return_value = mock_mongo
        
        result = dbc.connect_db()
        
        # Should call MongoClient with connection string
        assert mock_client.call_count == 1
        call_args = mock_client.call_args[0][0]
        assert 'mongodb+srv://' in call_args
        assert 'test_password' in call_args
        assert result == mock_mongo
        assert dbc.client == mock_mongo
    
    @patch.dict('os.environ', {'CLOUD_MONGO': '1'}, clear=True)
    def test_connect_cloud_without_password(self):
        """Test that connecting to cloud without password raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            dbc.connect_db()
        
        assert 'You must set your password' in str(exc_info.value)
    
    @patch('data.db_connect.pm.MongoClient')
    @patch.dict('os.environ', {'CLOUD_MONGO': '0'}, clear=False)
    def test_reuse_existing_client(self, mock_client):
        """Test that connect_db reuses existing client instead of creating a new one."""
        mock_mongo = MagicMock()
        mock_client.return_value = mock_mongo
        
        # First call should create the client
        result1 = dbc.connect_db()
        assert mock_client.call_count == 1
        
        # Second call should reuse the existing client
        result2 = dbc.connect_db()
        assert mock_client.call_count == 1  # Still 1, not called again
        assert result1 == result2
        assert result2 == mock_mongo


class TestNeedsDbDecorator:
    """Test the @needs_db decorator."""
    
    @patch('data.db_connect.pm.MongoClient')
    @patch.dict('os.environ', {'CLOUD_MONGO': '0'}, clear=False)
    def test_decorator_establishes_connection(self, mock_client):
        """Test that @needs_db decorator establishes connection before function call."""
        mock_mongo = MagicMock()
        mock_client.return_value = mock_mongo
        
        # Call a function that uses @needs_db decorator
        @dbc.needs_db
        def test_function():
            return "success"
        
        result = test_function()
        
        # Decorator should have called connect_db, which calls MongoClient
        assert mock_client.call_count == 1
        assert result == "success"
        assert dbc.client == mock_mongo
    
    @patch('data.db_connect.pm.MongoClient')
    @patch.dict('os.environ', {'CLOUD_MONGO': '0'}, clear=False)
    def test_decorator_reuses_existing_connection(self, mock_client):
        """Test that @needs_db decorator reuses existing connection."""
        mock_mongo = MagicMock()
        mock_client.return_value = mock_mongo
        
        # Establish connection first
        dbc.connect_db()
        assert mock_client.call_count == 1
        
        # Call decorated function
        @dbc.needs_db
        def test_function():
            return "success"
        
        result = test_function()
        
        # Should not create a new connection
        assert mock_client.call_count == 1  # Still 1
        assert result == "success"


class TestConvertMongoId:
    """Test the convert_mongo_id function."""
    
    def test_converts_mongo_id(self):
        """Test that _id is converted to string."""
        from bson import ObjectId
        doc = {dbc.MONGO_ID: ObjectId('507f1f77bcf86cd799439011')}
        dbc.convert_mongo_id(doc)
        assert isinstance(doc[dbc.MONGO_ID], str)
        assert doc[dbc.MONGO_ID] == '507f1f77bcf86cd799439011'
    
    def test_no_mongo_id(self):
        """Test that function works when no _id is present."""
        doc = {'name': 'test'}
        dbc.convert_mongo_id(doc)
        assert doc == {'name': 'test'}


@pytest.mark.skip(reason="CRUD operations require active MongoDB connection")
class TestDatabaseCRUDOperations:
    """Tests for create, read, update, delete operations (requires live DB)."""
    
    def test_create_document(self):
        """Test creating a document in the database."""
        # Skipped: requires live MongoDB instance
        test_doc = {'name': 'test', 'value': 123}
        result = dbc.create('test_collection', test_doc)
        assert result.inserted_id is not None
    
    def test_read_documents(self):
        """Test reading documents from the database."""
        # Skipped: requires live MongoDB instance
        docs = dbc.read('test_collection')
        assert isinstance(docs, list)

