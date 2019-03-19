import logging
import os
import re
import urllib.parse

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


class UnsupportedMediaFormat(ValueError):
    pass


def handler(event, context):
    # Gets ENV variables
    output_bucket = os.environ['TRANSCRIPTION_BUCKET']

    # Get the object from the event and show its content type
    s3obj = event['Records'][0]['s3']
    source_bucket = s3obj['bucket']['name']
    source_file = urllib.parse.unquote_plus(s3obj['object']['key'], encoding='utf-8')
    source_file_format = re.search('\\.(\\w{3,4})$', source_file).group(1)

    # Raises UnsupportedMediaFormat error if the format is unsupported by AWS Transcribe
    __check_media_format_supported(source_file_format)

    # Formats S3 url
    source_url = __build_s3url(bucket=source_bucket, key=source_file)

    # Formats the output key
    output_key = re.sub(r'\s', '.', source_file)

    # Starts transcription job
    __start_transcription_job(source_url, source_file_format, output_bucket, output_key)


def __build_s3url(region: str = region, bucket: str = None, key: str = ''):
    """
    Formats URL to download the file from S3 by provided bucket and the key
    :param region:
    :param bucket:
    :param key:
    :return:
    """
    return f"https://s3-{region}.amazonaws.com/{bucket}/{key}"


def __check_media_format_supported(media_format):
    """
    Ensures provided media_format is supported by Transcribe, throws UnsupportedMediaFormat otherwise

    :param media_format:
    :return:
    """
    if media_format not in SUPPORTED_MEDIA_FORMATS:
        raise UnsupportedMediaFormat(f"{media_format} is not supported audio type.")


def raises_throttling_exception(decorable):
    """
    Decorates transcribe exceptions with the ThrottlingException

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
def __start_transcription_job(source_url: str, source_format: str, to_bucket: str, to_key: str, lang='en-US') -> str:
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
