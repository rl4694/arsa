import pytest
import os
from unittest.mock import patch, MagicMock
from bson.objectid import ObjectId
import data.db_connect as dbc
import pymongo as pm


@pytest.fixture(autouse=True)
def _reset_client():
    """Reset the global client before and after each test."""
    original_client = dbc.client
    dbc.client = None
    yield
    dbc.client = original_client


@pytest.fixture(scope='class')
def live_client():
    mongo_url = os.environ.get('MONGO_URL')

    if not mongo_url:
        pytest.skip("MONGO_URL environment variable not set.")
    try:
        client = pm.MongoClient(
            mongo_url,
            serverSelectionTimeoutMS=5000,
            **dbc.PA_SETTINGS
        )
        client.admin.command('ping')
        return client
    except Exception as e:
        pytest.skip(f"Could not connect to MongoDB. Error: {e}")


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
    @patch.dict('os.environ',
                {'CLOUD_MONGO: '1',
                 'MONGO_URL': 'mongodb+srv://mock_user:mock_pass@cluster.mongodb.net/test'},
                clear=False)
    
    def test_connect_cloud_with_url(self, mock_client):
        """Test connecting to MongoDB in the cloud with a password."""
        mock_mongo = MagicMock()
        mock_client.return_value = mock_mongo
        
        result = dbc.connect_db()
        
        # Should call MongoClient with connection string
        assert mock_client.call_count == 1
        call_args = mock_client.call_args[0][0]
        assert 'mongodb+srv://' in call_args
        assert 'mock_user' in call_args
        assert result == mock_mongo
    
    @patch.dict('os.environ', {'CLOUD_MONGO': '1'}, clear=True)
    def test_connect_cloud_without_url(self):
        if 'MONGO_URL' in os.environ:
            del os.environ['MONGO_URL']
        """Test that connecting to cloud without password raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            dbc.connect_db()
        
        assert 'You must set the MONGO_URL env variable' in str(exc_info.value)
    
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
        doc = {dbc.MONGO_ID: ObjectId('507f1f77bcf86cd799439011')}
        dbc.convert_mongo_id(doc)
        assert isinstance(doc[dbc.MONGO_ID], str)
        assert doc[dbc.MONGO_ID] == '507f1f77bcf86cd799439011'
    
    def test_no_mongo_id(self):
        """Test that function works when no _id is present."""
        doc = {'name': 'test'}
        dbc.convert_mongo_id(doc)
        assert doc == {'name': 'test'}


class TestDatabaseCRUDOperations:
    """Tests for create, read, update, delete operations (requires live DB)."""
    TEST_COLLECTION = 'test_integration_suite'
    TEST_DB = dbc.SE_DB

    @pytest.fixture(autouse=True)
    def setup_teardown_live_data(self, live_client):
        dbc.client = live_client
        
        """Clean slate before test"""
        dbc.client[self.TEST_DB][self.TEST_COLLECTION].delete_many({})
        
        yield

        """Clean slate after test"""
        dbc.client[self.TEST_DB][self.TEST_COLLECTION].delete_many({})

    def test_create_and_read_one(self):
        """Test creating a document in the database."""
        test_doc = {'name': 'integration_test', 'value': 999}

        result = dbc.create(self.TEST_COLLECTION, test_doc, db=self.TEST_DB)
        assert result.inserted_id is not None

        fetched_doc = dbc.read_one(self.TEST_COLLECTION,
                                   {'_id': result.inserted_id},
                                   db=self.TEST_DB)
        assert fetched_doc is not None
        assert fetched_doc['name'] == 'integration_test'
        assert isinstance(fetched_doc['_id'], str)
    
    def test_delete_document(self):
        """Test creating and then deleting a document"""
        doc = {'name': 'to_be_deleted'}
        result = dbc.create(self.TEST_COLLECTION, doc, db=self.TEST_DB)
        
        count = dbc.delete(self.TEST_COLLECTION, {'_id': result.inserted_id}, db=self.TEST_DB)
        assert count == 1
        
        missing_doc = dbc.read_one(self.TEST_COLLECTION,
                                   {'_id': result.inserted_id},
                                   db=self.TEST_DB)
        assert missing_doc is None

    def test_read_all_no_id(self):
        """Test reading list of documents with no_id=True (default)"""
        dbc.create(self.TEST_COLLECTION, {'item': 1}, db=self.TEST_DB)
        dbc.create(self.TEST_COLLECTION, {'item': 2}, db=self.TEST_DB)
        
        docs = dbc.read(self.TEST_COLLECTION, db=self.TEST_DB, no_id=True)
        
        assert isinstance(docs, list)
        assert len(docs) == 2
        assert '_id' not in docs[0]
        assert 'id' not in docs[1]
