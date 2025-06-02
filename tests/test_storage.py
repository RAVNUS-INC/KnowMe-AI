import unittest
from src.storage.minio_client import MinioClient  # Adjust the import based on your actual MinIO client implementation

class TestMinioClient(unittest.TestCase):
    
    def setUp(self):
        self.client = MinioClient()  # Initialize your MinIO client here

    def test_upload_file(self):
        # Test the upload functionality
        result = self.client.upload_file('test_file.txt', 'bucket_name')
        self.assertTrue(result)

    def test_download_file(self):
        # Test the download functionality
        result = self.client.download_file('bucket_name', 'test_file.txt')
        self.assertIsNotNone(result)

    def test_delete_file(self):
        # Test the delete functionality
        result = self.client.delete_file('bucket_name', 'test_file.txt')
        self.assertTrue(result)

    def tearDown(self):
        # Clean up any resources if necessary
        pass

if __name__ == '__main__':
    unittest.main()