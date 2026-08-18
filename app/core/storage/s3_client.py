import boto3
from decouple import config
from fastapi import HTTPException

B2_ENDPOINT_URL = config("B2_ENDPOINT_URL", default=None)
B2_ACCESS_KEY_ID = config("B2_ACCESS_KEY_ID", default=None)
B2_SECRET_ACCESS_KEY = config("B2_SECRET_ACCESS_KEY", default=None)
B2_BUCKET_NAME = config("B2_BUCKET_NAME", default=None)

class S3Client:
    def __init__(self):
        if not all([B2_ENDPOINT_URL, B2_ACCESS_KEY_ID, B2_SECRET_ACCESS_KEY, B2_BUCKET_NAME]):
            print("WARNING: B2 credentials are not fully set in .env")

        self.bucket_name = B2_BUCKET_NAME
        try:
            self.s3 = boto3.client(
                's3',
                endpoint_url=B2_ENDPOINT_URL,
                aws_access_key_id=B2_ACCESS_KEY_ID,
                aws_secret_access_key=B2_SECRET_ACCESS_KEY
            )
        except Exception as e:
            print(f"Failed to initialize S3 client: {e}")
            self.s3 = None

    def upload_file(self, file_obj, filename: str) -> bool:
        if not self.s3:
            raise HTTPException(status_code=500, detail="S3 client not initialized")
        try:
            self.s3.upload_fileobj(file_obj, self.bucket_name, filename)
            return True
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to upload to S3: {str(e)}")

    def get_file_stream(self, filename: str):
        if not self.s3:
            raise HTTPException(status_code=500, detail="S3 client not initialized")
        try:
            response = self.s3.get_object(Bucket=self.bucket_name, Key=filename)
            return response['Body']
        except Exception as e:
            raise HTTPException(status_code=404, detail=f"Failed to fetch file from S3: {str(e)}")

    def delete_file(self, filename: str) -> bool:
        if not self.s3:
            raise HTTPException(status_code=500, detail="S3 client not initialized")
        try:
            self.s3.delete_object(Bucket=self.bucket_name, Key=filename)
            return True
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to delete file from S3: {str(e)}")
