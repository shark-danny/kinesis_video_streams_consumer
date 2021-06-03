import boto3

class S3Client:
    '''
    This class acts as a client for s3
    '''
    def __init__(self):
        self._client=self.get_client()

    def get_client(self):
        return boto3.client('s3')

    def put_object(self,bucket_name,key,body):
        '''
        :param bucket_name: S3 bucket name
        :param key: Key for s3 object
        :param body: Content of the object
        :return:
        '''
        self._client.put_object(Bucket=bucket_name,
                                Key=key,
                                Body=body)
