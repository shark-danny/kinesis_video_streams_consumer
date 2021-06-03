import boto3
import os

current_path=os.path.dirname(os.path.realpath(__file__))
prj_root=current_path+'/../../'

class KinesisVideoBase:
    '''
    This class acts as a base class for kinesis video stream consumers
    '''

    def __init__(self,kinesis_video_stream):
        '''
        :param kinesis_video_stream: Name of the kinesis video stream
        '''
        self._kinesis_video_stream=kinesis_video_stream
        self._kinesis_client=self.get_kinesis_client()
        self._media_endpoint_url=self.get_media_endpoint()
        self._media_client=self.get_media_client()

    def get_kinesis_client(self):
        return boto3.client('kinesisvideo')

    def get_media_endpoint(self):
        return self._kinesis_client.\
               get_data_endpoint(StreamName=self._kinesis_video_stream,
               APIName='GET_MEDIA')['DataEndpoint']

    def get_media_client(self):
        return boto3.client('kinesis-video-media',
                            endpoint_url=self._media_endpoint_url)


