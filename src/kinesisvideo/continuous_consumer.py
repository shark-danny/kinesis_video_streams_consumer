import time
import imageio
from io import BytesIO
import os
from src.kinesisvideo.base import KinesisVideoBase
from src.s3.client import S3Client
from src.utils.matroska_parser import Ebml,MatroskaTags

current_path=os.path.dirname(os.path.realpath(__file__))
prj_root=current_path+'/../../'

class ContinousConsumer(KinesisVideoBase):
    '''
    This class coninuously consumes available fragments from kinesis video stream
    '''

    def __init__(self,kinesis_video_stream):
        '''
        :param kinesis_video_stream: Name of kinesis video stream
        '''
        super(ContinousConsumer,self).__init__(kinesis_video_stream)
        self._s3_client=S3Client()

    def consume(self):
        while True:
            fragment=self.get_fragment()
            print(fragment)


    def get_fragment(self):
        s3_key=self._kinesis_video_stream+'/'+time.strftime("%Y%m%d-%H%M%S")+'.webm'

        fragment=self._media_client.get_media(
            StreamName=self._kinesis_video_stream,
            StartSelector={
                'StartSelectorType':'EARLIEST'
            }
        )

        content=fragment['Payload'].read()

        matroska_parser=Ebml(content,MatroskaTags)

        # matroska_tags['Segment'][0]['Tags'][0]['Tag'][0]['SimpleTag']
        matroska_tags=matroska_parser.parse()


        # vid=imageio.get_reader(BytesIO(content),'ffmpeg')
        #
        # metadata=vid.get_meta_data()
        #
        # for num,image in enumerate(vid.iter_data()):
        #     print(image.mean())

        self._s3_client.put_object('kinesis-video-fragments',s3_key,content)

        return fragment


if __name__=='__main__':
    consumer=ContinousConsumer('video_stream')
    consumer.consume()