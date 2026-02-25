from google.cloud import storage
from google.api_core.exceptions import Conflict, NotFound
from globals.utils.logger import logger
from typing import Optional, List
from globals.config.config import GCS_SERVICE_ACCOUNT, PROJECT_ID, BUCKET_NAME
from datetime import timedelta, datetime, timezone
from io import BytesIO
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
import tempfile
import zipfile
from zoneinfo import ZoneInfo


class GCSManager:
    def __init__(self):
        """
        Initialize GCSManager with service account credentials and project ID.
        """
        self.timezone = ZoneInfo("Asia/Beirut")
        self.project_id = PROJECT_ID
        self.client = self._get_client()
        self.set_lifecycle_policy(bucket_name=BUCKET_NAME)
        logger.info(
            f"GCSManager for project {self.project_id} initialized successfully."
        )

    def set_lifecycle_policy(self, bucket_name: str):
        bucket = self.client.get_bucket(bucket_name)

        rules = {
            "rule": [
                {
                    "action": {"type": "Delete"},
                    "condition": {"age": 1, "matchesPrefix": ["zip/"]},
                },
                {
                    "action": {"type": "Delete"},
                    "condition": {"age": 365, "matchesPrefix": ["readings/"]},
                },
                {
                    "action": {"type": "SetStorageClass", "storageClass": "ARCHIVE"},
                    "condition": {"age": 365, "matchesPrefix": ["bills/"]},
                },
            ]
        }

        bucket.lifecycle_rules = rules["rule"]
        bucket.patch()
        logger.info(f"Lifecycle rules set for bucket {bucket_name}")

    def _get_client(self) -> storage.Client:
        """
        Returns the authenticated GCS client.
        """
        try:
            client = storage.Client.from_service_account_info(GCS_SERVICE_ACCOUNT)
            logger.info("GCS client created successfully.")
            return client
        except Exception as e:
            logger.error(f"Error creating GCS client: {e}")
            raise

    def create_bucket(self, bucket_name: str, location: str) -> storage.Bucket:
        """
        Creates a new bucket in the specified location.
        """
        try:
            bucket = self.client.bucket(bucket_name)
            new_bucket = self.client.create_bucket(bucket, location=location)
            logger.info(f"Bucket {bucket_name} created in {location}.")
            return new_bucket

        except Conflict:
            logger.info(f"Bucket {bucket_name} already exists.")
            return self.client.get_bucket(bucket_name)

        except Exception as e:
            logger.error(f"Error creating bucket {bucket_name}: {e}")
            raise

    def upload_buffer(
        self,
        bucket_name: str,
        buffer: BytesIO,
        destination_blob_name: str,
        content_type: str = "image/png",
    ) -> str:
        """
        Uploads an in-memory file (like a QR code image buffer) to GCS.
        """
        try:
            bucket = self.client.bucket(bucket_name)
            blob = bucket.blob(destination_blob_name)
            buffer.seek(0)
            blob.upload_from_file(buffer, content_type=content_type)
            logger.info(f"Buffer uploaded to {destination_blob_name}.")
            return destination_blob_name

        except Exception as e:
            logger.error(f"Error uploading buffer: {e}")
            raise

    def download_file(
        self, bucket_name: str, blob_name: str, destination_file_path: str
    ):
        """
        Downloads a blob from GCS to a local path.
        """
        try:
            bucket = self.client.bucket(bucket_name)
            blob = bucket.blob(blob_name)
            blob.download_to_filename(destination_file_path)
            logger.info(f"Blob {blob_name} downloaded to {destination_file_path}.")

        except NotFound:
            logger.error(f"Blob {blob_name} not found in bucket {bucket_name}.")
            raise

    def list_files(self, bucket_name: str, prefix: Optional[str] = None) -> List[str]:
        """
        Lists all blobs in the bucket (optionally under a prefix/folder).
        """
        try:
            bucket = self.client.bucket(bucket_name)
            blobs = bucket.list_blobs(prefix=prefix)
            return [blob.name for blob in blobs]

        except Exception as e:
            logger.error(f"Error listing files in bucket {bucket_name}: {e}")
            raise

    def file_exists(self, bucket_name: str, blob_name: str) -> bool:
        """
        Checks if a file exists in the bucket.
        """
        try:
            bucket = self.client.bucket(bucket_name)
            blob = bucket.blob(blob_name)
            exists = blob.exists()
            if exists:
                logger.info(f"Blob {blob_name} exists in bucket {bucket_name}.")
            else:
                logger.info(f"Blob {blob_name} does not exist in bucket {bucket_name}.")
            return exists

        except NotFound:
            logger.info(f"Blob {blob_name} does not exist in bucket {bucket_name}.")
            return False

    def generate_signed_url(
        self,
        bucket_name: str,
        blob_name: str,
        expiration_minutes: int = 15,
        download: bool = True,
    ):
        try:
            bucket = self.client.bucket(bucket_name)
            blob = bucket.blob(blob_name)

            url = blob.generate_signed_url(
                version="v4",
                expiration=timedelta(minutes=expiration_minutes),
                method="GET",
                response_disposition=(
                    f'attachment; filename="{blob_name}"' if download else None
                ),
            )
            logger.info(
                f"Generated signed URL for blob {blob_name} in bucket {bucket_name}."
            )
            return url

        except Exception as e:
            logger.error(
                f"Error generating signed URL for blob {blob_name} in bucket {bucket_name}: {e}"
            )
            raise

    def delete_file(self, bucket_name: str, blob_name: str):
        """
        Deletes a file from the specified bucket.
        """
        try:
            bucket = self.client.bucket(bucket_name)
            blob = bucket.blob(blob_name)
            blob.delete()
            logger.info(f"Blob {blob_name} deleted from bucket {bucket_name}.")
            return True

        except NotFound:
            logger.error(f"Blob {blob_name} not found in bucket {bucket_name}.")
            raise

        except Exception as e:
            logger.error(
                f"Error deleting blob {blob_name} from bucket {bucket_name}: {e}"
            )
            raise

    def create_qr_zip_and_signed_url(
        self, bucket_name: str, qr_blob_names: List[str], expiration_minutes: int = 15
    ) -> str:
        try:
            zip_blob_name = f"zip/qrcodes_{datetime.now(self.timezone).strftime('%Y-%m-%d_%H-%M-%S')}.zip"

            # Step 1: Download all QR codes concurrently to a temp folder
            with tempfile.TemporaryDirectory() as tmpdir:

                def download(blob_name):
                    local_path = os.path.join(tmpdir, os.path.basename(blob_name))
                    self.download_file(bucket_name, blob_name, local_path)
                    return local_path

                with ThreadPoolExecutor(max_workers=10) as executor:
                    futures = [
                        executor.submit(download, name) for name in qr_blob_names
                    ]
                    for future in as_completed(futures):
                        future.result()  # Raise any download exceptions

                logger.info(
                    f"Downloaded {len(qr_blob_names)} QR codes to temporary directory {tmpdir}."
                )

                # Step 2: Zip the folder
                zip_path = os.path.join(tmpdir, os.path.basename(zip_blob_name))
                with zipfile.ZipFile(zip_path, "w") as zipf:
                    for file_name in os.listdir(tmpdir):
                        full_path = os.path.join(tmpdir, file_name)
                        if file_name != os.path.basename(
                            zip_blob_name
                        ) and os.path.isfile(full_path):
                            zipf.write(full_path, arcname=file_name)

                logger.info(f"Created zip file {zip_path} containing QR codes.")

                # Step 3: Upload zip to GCS
                with open(zip_path, "rb") as f:
                    buffer = BytesIO(f.read())
                    self.upload_buffer(
                        bucket_name,
                        buffer,
                        zip_blob_name,
                        content_type="application/zip",
                    )
                logger.info(
                    f"Uploaded zip file {zip_blob_name} to bucket {bucket_name}."
                )

                # Step 4: Generate signed URL for the zip file
                return self.generate_signed_url(
                    bucket_name, zip_blob_name, expiration_minutes
                )

        except Exception as e:
            logger.error(f"Error creating QR zip and signed URL: {e}")
            raise

    def delete_files(self, bucket_name: str, blob_names: List[str]):
        """
        Deletes multiple QR code files from GCS.
        """
        try:
            bucket = self.client.bucket(bucket_name)
            bucket.delete_blobs([bucket.blob(blob_name) for blob_name in blob_names])
            logger.info(
                f"Deleted {len(blob_names)} QR code files from bucket {bucket_name}."
            )
            return True

        except Exception as e:
            logger.error(f"Error deleting QR code files: {e}")
            raise
