import sys
import os
import base64
import time
import getopt
import msvcrt

from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium.common.exceptions import TimeoutException
from reportlab import rl_config
from reportlab.pdfgen import canvas
from tkinter import *


class WebCrawler:
    def __init__(self, url, filename, isImage, isPDF, path, index):
        self.url = url
        self.filename = filename
        self.isImage = isImage
        self.isPDF = isPDF
        self.path = path
        self.index = index

        self.IMAGEFILES = []

        self.username = input("ID: ")
        self.password = self.getpwd("Password: ")

        self.crawl()

        if self.isPDF:
            self.transToPDF()

        if not self.isImage:    # 删除图片文件夹
            delete_list = os.listdir(os.path.join(self.path, self.filename))
            for file in delete_list:
                file_path = os.path.join(self.path, self.filename, file)
                os.remove(file_path)
            os.rmdir(os.path.join(self.path, self.filename))

        print("文件已爬取完毕，下载路径为" + self.path + os.sep + self.filename)


    def crawl(self):
        folder = Path(self.path+self.filename)
        if not folder.exists():
            os.mkdir(self.path+self.filename)

        browser = webdriver.Chrome()
        browser.get(self.url)
        username = browser.find_element_by_id("username")
        password = browser.find_element_by_id("password")
        username.send_keys(self.username)
        password.send_keys(self.password)
        password.send_keys(Keys.ENTER)

        if not os.path.exists(os.path.join(self.path, self.filename)):
            os.mkdir(os.path.join(self.path, self.filename))

        try:
            wait = WebDriverWait(browser, 10)
            wait.until(EC.presence_of_element_located((By.ID, 'pagebox')))
        except TimeoutException:
            raise TimeoutException("ID密码错误，或网络连接状态不好")

        time.sleep(2)
        pageNum = len(browser.find_elements_by_class_name("page-img-box"))

        for i in range(int(self.index), pageNum):
            element = browser.find_elements(By.CSS_SELECTOR, '[index="' + str(i) + '"] img')[0]
            browser.execute_script('window.scrollTo(0,' + str(element.location.get("y")) + ')')
            order_num = (len(str(pageNum)) - len(str(i))) * "0" + str(i)
            file_path = os.path.join(self.path, self.filename, order_num)
            file = open(file_path+".jpg", "wb")
            image_str = element.get_attribute("src")
            while image_str is None or len(image_str) < 25000:
                if image_str is not None and "AAAAAAAAAAAAAAAAAAAAAAAAAAAAA" in image_str:
                    break
                image_str = element.get_attribute("src")
                time.sleep(1)
            image_data = base64.b64decode(image_str.split(",")[1])
            file.write(image_data)
            file.close()

        browser.close()


    def transToPDF(self):
        self.getListImages(os.path.join(self.path, self.filename))
        pdfFile = os.path.join(self.path, self.filename) + ".pdf"
        cv = canvas.Canvas(pdfFile)
        (w, h) = rl_config.defaultPageSize
        for imagePath in self.IMAGEFILES:
            cv.drawImage(imagePath, 0, 0, w, h)
            cv.showPage()
        cv.save()


    def getListImages(self, path):
        if path is None or path == 0:
            raise ValueError('dirPath不能为空，该值为存放图片的具体路径文件夹！')
        if os.path.isfile(path):
            raise ValueError('dirPath不能为具体文件，该值为存放图片的具体路径文件夹！')
        if os.path.isdir(path):
            for imageName in os.listdir(path):
                if imageName.endswith('.jpg') or imageName.endswith('.jpeg'):
                    absPath = os.path.join(self.path, self.filename, imageName)
                    self.IMAGEFILES.append(absPath)


    def getpwd(self, msg=""):
        print(msg, end="")
        sys.stdout.flush()

        pwd = []

        while True:
            ch = msvcrt.getch()
            if ch == b'\r':
                msvcrt.putch(b'\n')
                return b"".join(pwd).decode()
                break
            elif ch == b'\x08':
                if pwd:
                    pwd.pop()
                    msvcrt.putch(b'\b')
                    msvcrt.putch(b' ')
                    msvcrt.putch(b'\b')
            elif ch == b'\x03':
                raise KeyboardInterrupt()
            elif ch == b'\x1b':
                break
            else:
                pwd.append(ch)
                msvcrt.putch(b'*')


def main():
    opts, args = getopt.getopt(sys.argv[1:], '-i-image-p-pdf', ["path=", "index=", "url=", "filename="])

    path = ""
    index = 1
    isImage = False
    isPDF = False
    url = ""
    filename = ""

    for opt_name, opt_content in opts:
        if opt_name == "--path":
            path = opt_content
        if opt_name == "--index":
            index = opt_content
        if opt_name == "--url":
            url = opt_content
        if opt_name == "--filename":
            filename = opt_content
        if opt_name == "-p" or opt_name == "-pdf":
            isPDF = True
        if opt_name == "-i" or opt_name == "image":
            isImage = True

    if not url:
        raise Exception("请指定URL")
    if not filename:
        raise Exception("请输入文件名")
    if not isPDF and not isImage:
        isPDF = True  # 默认情况下只保留pdf形式

    WebCrawler(isImage=isImage, isPDF=isPDF, path=path, index=index, filename=filename, url=url)


if __name__ == "__main__":
    main()