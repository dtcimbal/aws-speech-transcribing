import logging
import os
import re

import awsutil
import boto3
from botocore.config import Config

SUPPORTED_MEDIA_FORMATS = {"flac", "mp3", "mp4", "wav"}

# Logger setup
formatter = logging.Formatter('%(asctime)-15s %(message)s')

log = logging.getLogger()
log.setLevel(logging.DEBUG)

# Console log handler
console = logging.StreamHandler()
console.setLevel(logging.INFO)
console.setFormatter(formatter)
log.addHandler(console)

log.info('Loading the handler')

# AWS setup
region = boto3.session.Session().region_name
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


# Throttling exception wrapper is optional
@raises_throttling_exception
def __start_transcription_job(source_url: str, source_format: str, to_bucket: str, to_key: str, lang='en-US'):
    """
    Starts transcription job

    :param source_url:
    :param source_format:
    :param to_bucket:
    :param lang:
    :return:
    """

    # Requests transcription job.
    response = transcribe.start_transcription_job(
        TranscriptionJobName=to_key,
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

    return response['TranscriptionJob']['TranscriptionJobName']


def handler(event, context):
    # Gets ENV variables
    output_bucket = os.environ['TRANSCRIPTION_BUCKET']

    # Get the object from the event and show its content type
    (source_bucket, source_key) = awsutil.get_s3path(event)
    source_format = re.search('\\.(\\w{3,4})$', source_key).group(1)

    if source_format not in SUPPORTED_MEDIA_FORMATS:
        raise UnsupportedMediaFormatError(f"{source_format} is not supported audio type.")

    log.info("permitted media format: " + source_format)
    source_url = awsutil.build_s3url(bucket=source_bucket, key=source_key)

    # Formats the output key
    output_key = re.sub(r'\s', '.', source_key)

    # Starts transcription job
    __start_transcription_job(source_url, source_format, output_bucket, output_key)
