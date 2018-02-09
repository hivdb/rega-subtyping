from s3lib import S3Helper

import argparse
import logging
import os

class LogArchiver:
    log_path = None
    folder_name = None
    log_filter = '-'
    LOGGER_PATH = "/var/log/jobarchive/logarchive.log"

    def __init__(self):
        args = LogArchiver.parse_args()

        self.log_path = args.log_path
        folder_name = args.s3_folder
        if folder_name is None:
            folder_name = self.log_path
        self.folder_name = folder_name
        if args.filter:
            self.log_filter = args.filter
        logging.basicConfig(format='%(asctime)s-%(levelname)s-%(message)s', filename=self.LOGGER_PATH, level=logging.INFO)
        logging.warning("Log reaper initialized")  

    @staticmethod
    def parse_args():
        parser = argparse.ArgumentParser(description='Archive logs to S3')
        parser.add_argument('log_path', metavar='[log path]', help='Path to the logs directory')
        parser.add_argument('s3_folder', metavar='[s3 folder]', help = 'S3 Folder to save in')
        parser.add_argument('--filter', metavar='[string]', required=False, help='Optional filter for files to archive.  Will only archive files that have [string] in their file name.  No wildcards/regex.')

        return parser.parse_args()

    #finds the log files that we're going to archive.  by default, we look for files with a dash in
    #the name.  otherwise we filter for files given by the filter
    def get_logs(self):
        if not self.log_path:
            return None
        files = os.listdir(self.log_path)
        logs = 0
        rotated_logs = 0
        log_paths = {}
        #look for rotated logs and send those over
        for log in files:
            logs += 1
            if log.find(self.log_filter) is not -1:
                rotated_logs += 1
                log_paths[log] = "{0}/{1}".format(self.log_path, log)
        logging.info("processed {0} logs, {1} are ready for archive".format(logs, rotated_logs))
        return log_paths

    def archive_logs(self, log_paths):
        summary = {"processed": 0, "archived": 0, "failed": 0}
        if not log_paths:
            return summary

        bucket_name = 'dbpartners'
        for file_name, log_path in log_paths.iteritems():
            summary["processed"] += 1
            key_name = "{0}/{1}".format(self.folder_name, file_name)
            bytes_written = S3Helper.save_to_s3(bucket_name, key_name, filename=log_path)
            logging.info("Saved log to {0}".format(key_name))
            if bytes_written <= 0:
                logging.info("failed to save log to s3")
                summary["failed"] += 1
            else:
                summary["archived"] += 1
        return summary

    def archive(self):
        if self.log_path is None:
            logging.critical("no log path was provided!")
            return False
        if self.folder_name is None:
            logging.critical("no s3 folder was provided!")
            return False

        files_to_archive = self.get_logs()
        summary = self.archive_logs(files_to_archive)
        logging.info("Summary")
        logging.info("-------")
        logging.info("Processed: {0}".format(summary["processed"]))
        logging.info("Archived: {0}".format(summary["archived"]))
        logging.info("Failed: {0}".format(summary["failed"]))
        logging.warning("done")
