#coding=utf-8

from bottle import request, response, static_file, redirect
from admin.config.config import ROOT

#@render('home/index.html')
def index():
    return redirect('/project/index/1')

def static(path):
    return static_file(path, ROOT+ '/static')
