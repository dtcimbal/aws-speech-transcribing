import urllib.parse

import boto3


def get_s3path(event):
    s3obj = event['Records'][0]['s3']
    return (
        s3obj['bucket']['name'],
        urllib.parse.unquote_plus(s3obj['object']['key'], encoding='utf-8')
    )


def get_region():
    """
    Returns current region
    :return: current region
    """
    return boto3.session.Session().region_name


def build_s3url(region: str = get_region(), bucket: str = None, key: str = ''):
    """
    Formats URL to download the file from S3 by provided bucket and the key
    :param region:
    :param bucket:
    :param key:
    :return:
    """
    return f"https://s3-{region}.amazonaws.com/{bucket}/{key}"
