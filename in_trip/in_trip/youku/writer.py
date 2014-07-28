# coding=utf8

import os
import datetime
import xlwt
import csv


class WriterError(Exception):
    pass


class WriterWrap(object):
    """ 输出数据文件 文件导出需要设置:
            文档的编码 encode; 文档类型 filetype; 输出路径 path;
            文档名称(不含扩展名) filename;
        writeObj = WriterWrap(path=path, filename="公共主页信息")
    """
    def __init__(self, **args):
        self.txtobj = TxtWriter(**args)
        self.xlsobj = XlsWriter(**args)

    def append(self, line):
        self.txtobj.append(line)
        self.xlsobj.append(line)

    def close(self):
        self.txtobj.close()
        self.xlsobj.close()


class Writer(object):
    def __init__(self):
        #TODO 初始化参数移至配置文件
        self.encode = 'gbk'
        self.filetype = None
        self.path = 'default_dir'
        self.filename = 'default'

    def setPath(self, path=None):
        """输出路径，默认当前时间, 注，导出路径为相对 CURRENT_PATH/output/ 的路径"""
        if not path:
            path = str(datetime.datetime.now())
            path = path.replace(" ", "").replace(":", "")
            self.path = "output/%s" % str(path)
        else:
            self.path = path

        if not os.path.exists(self.path):
            os.makedirs(self.path)

    def setFileName(self, file_name):
        """设置导出文件的文件名称, 如 default"""
         #TODO 解码编码封装 to utils
        if not isinstance(file_name, unicode):
            file_name = file_name.decode('utf-8', 'ignore')
        file_name = file_name.encode(self.encode, "ignore")

        index = 1
        fname = file_name
        # 获取不存在的文件名
        while 1:
            file_path = "%s/%s.%s" % (self.path, fname, self.filetype)
            if not os.path.exists(file_path):
                break
            index += 1
            fname = "%s_%d" % (file_name, index)

        self.filename = file_path

    def append(self):
        raise NotImplementedError('Should implement this method in subclass.')

    def close(self):
        raise NotImplementedError('Should implement this method in subclass.')


class TxtWriter(Writer):
    def __init__(self, **args):
        Writer.__init__(self)
        self.filetype = 'txt'
        self.setPath(args.get('path', None))
        self.setFileName(args.get('filename', None))

        self.txtfile = open(self.filename, "w")

    def append(self, line=[]):
        """ 写入一行 """
        tmp_line = []
        for item in line:
            if not isinstance(item, basestring):
                item = str(item)

            item = unicode(item.encode("cp936", "ignore"), "cp936")
            item = item.encode(self.encode, 'ignore')
            tmp_line.append(item)

        line = "\t".join(tmp_line)
        self.txtfile.write("%s\n" % line)

    def write(self, data=[]):
        """ 批量写入数据 参数: ‘行’列表，每行为’列‘列表 """
        # TODO 类型判断
        for line in data:
            self.append(line)

    def close(self):
        self.txtfile.close()


class XlsWriter(Writer):
    def __init__(self, **args):
        Writer.__init__(self)
        self.file_num = 0
        self.filetype = 'xls'
        self.setPath(args.get('path', None))
        self.setFileName(args.get('filename', None))
        self.orig_fname = self.filename
        self.setSheetName(args.get('sheetname', None))
        self.set_init()

    def set_init(self):
        self.file_num += 1
        if self.file_num > 1:
            fname = self.orig_fname.replace('.xls', '_%i.xls' % self.file_num)
            self.filename = fname

        self.total_cnt = 0
        self.max_rows = 250000
        self.row_limit = 50000
        self.cell_maxsize = 60000
        self.row_cnt = 0
        self.sheets = 0
        self.xlsfile = xlwt.Workbook()
        self.xlstable = self.getSheetTable()

    def setSheetName(self, sheet_name):
        if not sheet_name:
            self.sheetname = 'sheet'

    def getSheetTable(self):
        return self.xlsfile.add_sheet(self.sheetname + str(self.sheets))

    def append(self, line):
        cols = 0
        for item in line:
            if not isinstance(item, basestring):
                item = str(item)
            item = unicode(item.encode("gbk", "ignore"), "gbk")
            self.xlstable.write(self.row_cnt, cols, item)
            cols += 1
        self.row_cnt += 1
        self.total_cnt += 1

        if self.row_cnt >= self.row_limit:
            self.row_cnt = 0
            self.sheets += 1
            self.xlstable = self.getSheetTable()

        if self.total_cnt >= self.max_rows:
            self.close()
            self.set_init()

    def write(self, data):
        for line in data:
            self.append(line)

    def close(self):
        self.xlsfile.save(self.filename)


class CsvWriter(Writer):

    def __init__(self, **args):
        Writer.__init__(self)
        self.filetype = 'csv'
        self.setPath(args.get('path', None))
        self.setFileName(args.get('filename', None))

    def append(self, data):
        with open(self.filename, "wb") as csvfile:
            for line_data in data:
                if line_data == None:
                    csvfile.write("\n")
                else:
                    csvfile.write(line_data + "\n")
