import datetime
import firebase_admin
from firebase_admin import credentials, storage

class FirebaseManager:
    def __init__(self, bucket_name):

            # Path to your service account key file
        service_account_key_path = 'x-reacts-firebase-adminsdk-ofq0u-1f2c412804.json'

        # Initialize the Firebase app with the service account
        if not firebase_admin._apps:
            cred = credentials.Certificate(service_account_key_path)
            firebase_admin.initialize_app(cred, {
                'storageBucket': f'{bucket_name}.appspot.com'
            })

        # Get a reference to the storage bucket
        self.bucket = storage.bucket()

    def upload_file(self, source_file_name, destination_blob_name):
        # Create a blob in the bucket and upload the file to it
        blob = self.bucket.blob(destination_blob_name)
        blob.upload_from_filename(source_file_name)

        # Generate a signed URL for the blob
        url = blob.generate_signed_url(datetime.timedelta(seconds=300), method='GET')
        return url
    
def main():
    # Create an instance of FirebaseManager
    firebase_manager = FirebaseManager('x-reacts')

    # Upload a file to Firebase Storage
    file_url = firebase_manager.upload_file('audio.mp3', 'audio2.mp3')

    # Print the download URL
    print(file_url)

if __name__ == "__main__":
    main()
