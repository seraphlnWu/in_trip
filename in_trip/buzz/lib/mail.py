# coding=utf-8

import smtplib

def mail(from_addr, to_addrs, subject, body, smtp_server="localhost"):
    server = smtplib.SMTP(smtp_server)
    msg = "From: %s\r\nTo: %s\r\nSubject: %s\r\n\r\n%s" % (from_addr, ', '.join(to_addrs), subject, body)
    server.sendmail(from_addr, to_addrs, msg)
    server.quit()


if __name__ == '__main__':
    mail('no-reply@buzzmaster.com.cn', ['wangjian@admaster.com.cn', ], 'test mail', 'this is a test mail, ignore it.')
