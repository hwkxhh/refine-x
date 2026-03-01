import os
import boto3
from botocore.exceptions import ClientError
from fastapi import UploadFile, HTTPException
from app.config import settings


class StorageService:
    def __init__(self):
        self.s3_client = boto3.client(
            "s3",
            endpoint_url=settings.S3_ENDPOINT,
            aws_access_key_id=settings.S3_ACCESS_KEY,
            aws_secret_access_key=settings.S3_SECRET_KEY,
            region_name="us-east-1",
        )
        self.bucket_name = settings.S3_BUCKET

    def validate_file(self, file: UploadFile) -> dict:
        allowed_extensions = [".csv", ".xlsx", ".xls"]
        file_ext = os.path.splitext(file.filename)[1].lower()

        if file_ext not in allowed_extensions:
            return {
                "valid": False,
                "error": f"File type '{file_ext}' not allowed. Only CSV and Excel files accepted.",
                "file_type": None,
                "file_size": 0,
            }

        file_type = "csv" if file_ext == ".csv" else "xlsx"

        file.file.seek(0, 2)
        file_size = file.file.tell()
        file.file.seek(0)

        max_size = 50 * 1024 * 1024  # 50MB
        if file_size > max_size:
            return {
                "valid": False,
                "error": f"File too large ({file_size / 1024 / 1024:.1f}MB). Maximum 50MB.",
                "file_type": None,
                "file_size": file_size,
            }

        return {"valid": True, "error": None, "file_type": file_type, "file_size": file_size}

    def upload_file(self, file: UploadFile, job_id: int) -> str:
        try:
            s3_key = f"uploads/{job_id}/{file.filename}"
            self.s3_client.upload_fileobj(file.file, self.bucket_name, s3_key)
            return f"s3://{self.bucket_name}/{s3_key}"
        except ClientError as e:
            raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")

    def download_file(self, file_path: str) -> bytes:
        try:
            path_parts = file_path.replace("s3://", "").split("/", 1)
            bucket = path_parts[0]
            key = path_parts[1]
            response = self.s3_client.get_object(Bucket=bucket, Key=key)
            return response["Body"].read()
        except ClientError as e:
            raise HTTPException(status_code=404, detail=f"File not found: {str(e)}")

    def delete_file(self, file_path: str) -> bool:
        try:
            path_parts = file_path.replace("s3://", "").split("/", 1)
            bucket = path_parts[0]
            key = path_parts[1]
            self.s3_client.delete_object(Bucket=bucket, Key=key)
            return True
        except ClientError:
            return False


storage_service = StorageService()
