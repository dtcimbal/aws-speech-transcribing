import logging
import os
import random
import re
import string

import awsutil
import boto3
from botocore.config import Config

# Log level
logging.basicConfig()
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

logger.info('Loading function')

SUPPORTED_MEDIA_FORMATS = {
    "flac": "",
    "mp3": "",
    "mp4": "",
    "wav": ""
}

transcribe = boto3.client('transcribe', config=Config(retries={"max_attempts": 2}))


class ThrottlingException(Exception):
    pass


class UnsupportedMediaFormatError(ValueError):
    pass


def raises_throttling_exception(decorable):
    """
    Decorates transcribe.exceptions.BadRequestException,transcribe.exceptions.LimitExceededException and
    transcribe.exceptions.ClientError with the ThrottlingException
    :param decorable:
    :return:
    """

    def decorator(**kwargs):
        value = None
        try:
            value = decorable(kwargs)
        except (transcribe.exceptions.BadRequestException,
                transcribe.exceptions.LimitExceededException,
                transcribe.exceptions.ClientError) as e:
            raise ThrottlingException(e)
        return value

    return decorator


# Generates a random ID for the transcribe function execution
def __gen_id(size=8, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


@raises_throttling_exception
def __start_transcription_job(source_url: str, source_format: str, to_bucket: str, lang='en-US'):
    """
    Starts transcription job

    :param source_url:
    :param source_format:
    :param to_bucket:
    :param lang:
    :return:
    """
    job_name = __gen_id()

    # Requests transcription job.
    response = transcribe.start_transcription_job(
        TranscriptionJobName=job_name,
        LanguageCode=lang,
        OutputBucketName=to_bucket,
        MediaFormat=source_format,
        Media={
            'MediaFileUri': source_url
        },
        Settings={
            'ShowSpeakerLabels': True,
            'MaxSpeakerLabels': 10,
            'ChannelIdentification': False
        }
    )
    return job_name


def handler(event, context):
    # Gets ENV variables
    transcription_bucket = os.environ['TRANSCRIPTION_BUCKET']

    # Get the object from the event and show its content type
    (source_bucket, source_key) = awsutil.get_s3path(event)
    source_format = re.search('\\.(\\w{3,4})$', source_key).group(1)

    if source_format not in SUPPORTED_MEDIA_FORMATS:
        raise UnsupportedMediaFormatError(f"{source_format} is not supported audio type.")

    logger.info("permitted media format: " + source_format)
    source_url = awsutil.build_s3url(bucket=source_bucket, key=source_key)
    job_name = __start_transcription_job(source_url, source_format, transcription_bucket)

    return {
        "success": True,
        "transcribeJob": job_name
    }
