import boto
from boto.s3.key import Key
from boto.s3.connection import S3Connection

class S3Helper:
    ACCESS_KEY = "AKIAJ6X4OONYIHFVNVOQ"
    SECRET_KEY = "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"

    conn = None
    buckets = {}
    keys = {}


    @staticmethod
    def get_s3_conn():
        if S3Helper.conn is None:
            S3Helper.conn = S3Connection(S3Helper.ACCESS_KEY, S3Helper.SECRET_KEY)
        return S3Helper.conn

    @staticmethod
    def get_bucket(bucket_name):
        conn = S3Helper.get_s3_conn()
        if bucket_name not in S3Helper.buckets:
            S3Helper.buckets[bucket_name] = conn.get_bucket(bucket_name)
        return S3Helper.buckets[bucket_name]

    @staticmethod
    def get_key(bucket_name, key_name):
        bk = bucket_name + key_name
        if bk not in S3Helper.keys:
            S3Helper.keys[bk] = Key(S3Helper.get_bucket(bucket_name))
        return S3Helper.keys[bk]

    #saves data to the given key in the given bucket
    #if a file name is provided, uses key.set_contents_from_filename
    @staticmethod
    def save_to_s3(bucket_name, key_name, filename=None):
        key = S3Helper.get_key(bucket_name, key_name)
        key.key = key_name
        
        bytes_written = -1        
        if filename is not None:
            bytes_written = key.set_contents_from_filename(filename)
        return bytes_written
