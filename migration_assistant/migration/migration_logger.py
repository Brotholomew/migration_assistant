from datetime import datetime
from simple_websocket import Server
from flask import current_app
import os


class MigrationLogger:
    def __init__(self, ws: Server):
        self.date = MigrationLogger.get_date()
        self.ws = ws
        self.logfile = ""

    @staticmethod
    def get_date():
        return datetime.today().strftime('%Y-%m-%d::%H:%M:%S')

    def log(self, msg):
        _msg = f"[{MigrationLogger.get_date()}]: {msg}"
        self.logfile += _msg + "\n"
        self.ws.send(_msg)
        current_app.logger.info(msg)

    def err(self, msg):
        _msg = f"[{MigrationLogger.get_date()}][ERROR]: {msg}"
        self.logfile += _msg + "\n"
        self.ws.send(_msg)
        current_app.logger.error(msg)

    def end(self):
        with open(os.path.join(current_app.instance_path, f"{self.date}.log"), 'w') as f:
            f.write(f"{self.logfile}")