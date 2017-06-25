#!/usr/bin/python2
# coding=utf-8
import sys
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from smtplib import SMTP_SSL
from supervisor import childutils

from proxypool.config import SEND_MAIL


SMTP_SERVER = 'smtp server'
ACCOUNT = 'account'
PASSWORD = 'password'
LOG_PATH = '/tmp/email.txt'

msg = MIMEMultipart('alternative')
msg['Subject'] = 'ProxyPool process exit unexpectedly'
msg['From'] = 'address to send email'
msg['To'] = 'address to receive email'

template = """
<html>
  <head></head>
  <body>
    <p>[{dt}]<br>
       Process <b>{processname}</b> in group <b>{groupname}</b> exited
       unexpectedly (pid <em>{pid}</em>) from state <b>{from_state}.</b>
    </p>
  </body>
</html>
"""


def write_log(headers, payload):
    if not headers['eventname'].startswith('PROCESS_STATE_'):
        return
    f = open(LOG_PATH, 'a')
    f.write(str(headers) + '-' + str(datetime.now()) + '\n\n')
    pheaders, pdata = childutils.eventdata(payload + '\n')
    f.write(str(pheaders) + '-' + str(datetime.now()) + '\n\n')

    pheaders['dt'] = datetime.now()
    try:
        content = ('[{dt}]  Process {processname} in group {groupname} exited '
               'unexpectedly (pid {pid}) from state {from_state}\n').format(
            **pheaders)
        f.write(content)
        if SEND_MAIL:
            content = template.format(**pheaders)
            msg.set_payload(MIMEText(content, 'html'))
            smtp = SMTP_SSL(SMTP_SERVER)
            smtp.login(ACCOUNT, PASSWORD)
            smtp.sendmail(msg['From'], msg['To'], msg.as_string())
            smtp.quit()
    finally:
        f.flush()
        f.close()


def main():
    while 1:
        headers, payload = childutils.listener.wait(sys.stdin, sys.stdout)
        write_log(headers, payload)
        childutils.listener.ok(sys.stdout)


if __name__ == '__main__':
    main()
