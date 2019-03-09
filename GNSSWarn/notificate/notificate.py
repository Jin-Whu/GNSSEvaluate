#!usr/bin/env python
# coding:utf-8

import os
from email.header import Header
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart, MIMEBase
from email.utils import parseaddr, formataddr
from email import encoders
import smtplib
import datetime
import time


class Config(object):
    def __init__(self, addr, name):
        self.from_addr = None
        self.from_name = None
        self.email_user = None
        self.email_password = None
        self.email_server = None
        self.email_port = None
        self.addr = addr
        self.name = name


def readconfig():
    """Read configure file.

    Return:
        config, type:Config.
    """
    configpath = os.path.join(os.path.dirname(__file__), 'notificate.ini')
    if not os.path.isfile(configpath):
        print('Not find notificate.ini\n')
        return None
    config = Config(list(), list())
    with open(configpath) as f:
        for line in f:
            if line.startswith('to_email'):
                email = line.split('=')[1].strip()
                if email:
                    config.addr.append(email)
            if line.startswith('to_name'):
                name = line.split('=')[1].strip()
                if name:
                    config.name.append(name)
            if line.startswith('from_addr'):
                from_addr = line.split('=')[1].strip()
                if from_addr:
                    config.from_addr = from_addr
            if line.startswith('from_name'):
                from_name = line.split('=')[1].strip()
                if from_name:
                    config.from_name = from_name
            if line.startswith('email_user'):
                email_user = line.split('=')[1].strip()
                if email_user:
                    config.email_user = email_user
            if line.startswith('email_password'):
                email_password = line.split('=')[1].strip()
                if email_password:
                    config.email_password = email_password
            if line.startswith('email_server'):
                email_server = line.split('=')[1].strip()
                if email_server:
                    config.email_server = email_server
            if line.startswith('email_port'):
                email_port = line.split('=')[1].strip()
                if email_port:
                    config.email_port = int(email_port)
    if not config.addr or not config.name:
        print('Not find valid email or name information\n')
        return None
    return config


def _format_addr(s):
    name, addr = parseaddr(s)
    return formataddr((Header(name, 'utf-8').encode(), addr))


class Notify(object):
    def notificate(self, subject, message=None, files=None):
        """notificate.

        Args:
            subject:subject of email.
            message:message of email.
            files:file attacment.
        """
        # read to_addr  and to_name from notificate.ini
        config = readconfig()
        if not config:
            print('Not valid configure\n')
            return

        from_addr = config.from_addr
        from_name = config.from_name
        user = config.email_user
        password = config.email_password
        smtp_server = config.email_server
        smtp_port = config.email_port
        msg = MIMEMultipart()
        msg['From'] = _format_addr('%s <%s>' % (from_name, from_addr))
        msg['To'] = ', '.join([
            _format_addr('%s <%s>' % (to_name, to_addr))
            for to_addr, to_name in zip(config.addr, config.name)
        ])
        msg['Subject'] = Header(subject, 'utf-8').encode()
        if message:
            msg.attach(MIMEText('%s' % message, 'plain', 'utf-8'))
        if files:
            for filepath in files:
                with open(filepath, 'rb') as f:
                    part = MIMEBase('application', 'octet-stream')
                    part.add_header(
                        'Content-Disposition',
                        'attacment',
                        filename=os.path.basename(filepath))
                    part.set_payload(f.read())
                    encoders.encode_base64(part)
                    msg.attach(part)

        while True:
            try:
                server = smtplib.SMTP(smtp_server, smtp_port)
                server.starttls()
                server.login(user, password)
                server.sendmail(from_addr, config.addr, msg.as_string())
                server.quit()
                now = str(datetime.datetime.now().replace(second=0, microsecond=0))
                for to_addr in config.addr:
                    print('%s: Send email to %s successfully!\n' % (now, to_addr))
            except:
                raise
                time.sleep(300)
            else:
                break
