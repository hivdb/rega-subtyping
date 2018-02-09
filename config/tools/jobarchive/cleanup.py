from s3lib import S3Helper

import boto
from boto.s3.key import Key
from boto.s3.connection import S3Connection
import logging
import os
import shutil
import tarfile
import tempfile
import time

class RegaReaper:
    JOB_PATH = "/opt/rega/jobs"
    JOB_TYPES = ["HIV", "HTLV", "NoV"]
    JOB_AGE = 60 * 60 * 24 * 30 #one month in seconds
    S3_FOLDER = "jobs"

    LOG_PATH = "/var/log/jobarchive/jobarchive.log"

    def __init__(self):
        logging.basicConfig(format='%(asctime)s-%(levelname)s-%(message)s', filename=self.LOG_PATH, level=logging.INFO)
        logging.warning("Job reaper initialized")

    #gets a list of all job directories that are too old
    def get_jobs(self):
        paths = []
        for job_type in self.JOB_TYPES:
            paths.append("{0}/{1}".format(self.JOB_PATH, job_type))
        now = time.time()
        archive_paths = {}
        jobs = 0
        old_jobs = 0
        for path in paths:
            job_dirs = os.listdir(path)
            for job_dir in job_dirs:
                jobs += 1
                full_path = "{0}/{1}".format(path, job_dir)
                info = os.stat(full_path)
                if now - info.st_mtime > self.JOB_AGE:
                    old_jobs += 1
                    archive_paths[job_dir] = full_path
                    logging.info("job is too old, adding job to queue: {0}".format(full_path))
        logging.info("processed {0} jobs, {1} are old".format(jobs, old_jobs))
        return archive_paths

    def archive_jobs(self, job_paths):
        summary = {"processed": 0, "archived": 0, "deleted": 0, "failed": 0}
        if not job_paths:
            logging.info("nothing to archive")
            return summary

        bucket_name = 'rega'
        for dir_name, job_path in job_paths.iteritems():
            summary["processed"] += 1
            temp_file = tempfile.NamedTemporaryFile(delete=False, prefix='', suffix='.tgz')
            tar = tarfile.open(fileobj=temp_file, mode='w:gz')
            logging.info("Created temp file: {0}".format(tar.name))
            tar.add(job_path)
            tar.close()
            temp_file.close()
            logging.info("Packed job {0}".format(job_path))
            key_name = "jobs/{0}.tgz".format(dir_name)
            bytes_written = S3Helper.save_to_s3(bucket_name, key_name, filename=tar.name)
            logging.info("Saved job to {0}".format(key_name))
            if bytes_written <= 0:
                logging.info("failed to archive job")
                summary["failed"] += 1
            else:
                summary["archived"] += 1
                if self.delete_job(job_path):
                    summary["deleted"] += 1
                else:
                    summary["failed"] += 1
        return summary

    def delete_job(self, job_path):
        try:
            shutil.rmtree(job_path)
            logging.info("Deleted {0}".format(job_path))
        except:
            logging.critical("Failed to delete job: {0}".format(job_path))
            return False
        return True

    def reap(self):
        jobs_to_archive = self.get_jobs()
        summary = self.archive_jobs(jobs_to_archive)
        logging.info("Summary")
        logging.info("-------")
        logging.info("Processed: {0}".format(summary["processed"]))
        logging.info("Archived: {0}".format(summary["archived"]))
        logging.info("Deleted: {0}".format(summary["deleted"]))
        logging.info("Failed: {0}".format(summary["failed"]))
        logging.warning("done")
