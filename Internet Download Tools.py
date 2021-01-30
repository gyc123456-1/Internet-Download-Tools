from base64 import b64decode, b32encode
from hashlib import sha1
from os import path, getcwd, system, mkdir, unlink
from time import sleep, ctime, time
from bencodepy import encode, decode
import requests
from win32com.client import Dispatch
from sys import argv

version = 1.0

if path.isfile('Error.error'):
    with open('Error.error', 'rb') as Error_file:
        Error_text = Error_file.read().decode('gbk')
    if Error_text == 'Error!':
        print('检测到程序被修改,正在退出!')
        sleep(2)
        exit()

if not path.isdir('download'):
    mkdir('download')


def url_download(download_url_list: list):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko)'
                             ' Chrome/78.0.3904.108 Safari/537.36'}
    index = 1
    print('开始下载一个或多个链接:')
    start = time()
    Error = 0
    Error_list = []
    Error_reason = []
    for download_url in download_url_list:
        download_file_path = 'download/' + download_url.rsplit('/')[-1]
        try:
            response = requests.get(download_url, headers=headers)
        except Exception:
            print('第{}个链接请求失败，请检查后重试!'.format(index))
            Error += 1
            Error_list.append(index)
            Error_reason.append('链接请求失败')
        else:
            print('成功请求第{}个!'.format(index))
            size = 0
            chunk_size = 1024
            try:
                content_size = int(response.headers['content-length'])
            except KeyError:
                print('第{}个的大小无法获取,无法下载!'.format(index))
                Error += 1
                Error_list.append(index)
                Error_reason.append('大小无法获取')
            else:
                download_file_name = download_url.rsplit('/')[-1]
                print('正在下载第{}个({},大小:{}mb):'.format(index, download_file_name, content_size / chunk_size / 1024))
                if response.status_code == 200:
                    try:
                        with open(download_file_path, 'wb') as download_file:
                            for data in response.iter_content(chunk_size=chunk_size):
                                download_file.write(data)
                                size += len(data)
                                print('\r' + '[下载进度]:%s% .2f%%' % ('█' * int(size * 50 / content_size),
                                                                   float(size / content_size * 100)), end=' ')
                        print('')
                    except OSError:
                        try:
                            download_file_path = 'download/' + download_url.rsplit('/')[-2]
                            with open(download_file_path, 'wb') as download_file:
                                for data in response.iter_content(chunk_size=chunk_size):
                                    download_file.write(data)
                                    size += len(data)
                                    print('\r' + '[下载进度]:%s% .2f%%' % ('█' * int(size * 50 / content_size),
                                                                       float(size / content_size * 100)), end=' ')
                        except OSError:
                            print('第{}个的下载保存名称不允许这样命名或文件名太长,无法保存!'.format(index))
                            Error += 1
                            Error_list.append(index)
                            Error_reason.append('下载保存名称不允许这样命名或文件名太长')
                else:
                    print('第{}个链接访问出错!'.format(index))
                    Error += 1
                    Error_list.append(index)
                    Error_reason.append('链接访问出错')
        index += 1

    end = time()
    if Error == 0:
        print('链接全部下载完成并且没有出错!用时{}秒,文件在download文件夹!'.format(end - start))
    else:
        with open('download_log.log', 'w') as log_file:
            log_file.write('')
        with open('download_log.log', 'a') as log_file:
            for Error_index in Error_list:
                log_file.write('第{}个链接({})出错,因为{}!'.format(index, download_url_list[Error_index - 1],
                                                           Error_reason[Error_index - 1]))
        print('链接全部下载完成但有{}个出错!用时{}秒,日志在本目录下的download_log.log文件,文件在download文件夹!'
              .format(Error, end - start))


def thunder_download(url_list: list):
    index = 1
    thunder_url_list = []
    for thunder_url in url_list:
        thunder_url: str
        if 'thunder://' in thunder_url:
            print('检测到链接以thunder://开头,已为您添加至工具自带链接下载!')
            strb = thunder_url.lstrip('thunder://')
            urlb = b64decode(strb)
            strurl = urlb.decode('utf-8')
            zsrul = strurl.strip('AAZZ')
            thunder_url_list.append(zsrul)
        else:
            try:
                thunder = Dispatch('ThunderAgent.Agent64.1')
            except Exception:
                print('您没有安装迅雷,正在自动为您下载安装!')
                url_download(['https://down.sandai.net/thunder11/XunLeiWebSetup11.1.6.1242gw.exe'])
                print('正在运行安装迅雷程序,有杀毒软件拦截请放行!')
                system('download\\XunLeiWebSetup11.1.6.1242gw.exe')
            else:
                if 'ed2k://' in thunder_url:
                    file_name = thunder_url.rsplit('|')[2]
                    thunder.AddTask(thunder_url, file_name, path.join(getcwd(), 'download'))
                    thunder.CommitTasks()
                    print("第{}个任务已建立，开始下载：{}({})……".format(index, file_name, url_list[index - 1]))
                    index += 1
                else:
                    file_name = thunder_url.rsplit('/', 1)[-1]
                    thunder.AddTask(thunder_url, pPath=path.join(getcwd(), 'download'), nStartMode=1,
                                    nOriginThreadCount=10)
                    thunder.CommitTasks()
                    print("第{}个任务已建立，开始下载：{}({})……".format(index, file_name, url_list[index - 1]))
                    index += 1
    url_download(thunder_url_list)


def torrent_download(torrent_file_path_list):
    magneturi_list = []
    for torrent_file_path in torrent_file_path_list:
        with open(torrent_file_path, 'rb') as torrent_file:
            torrent = torrent_file.read()
        metadata = decode(torrent)
        metadata1 = {}
        for key in metadata:
            key1 = key.decode("utf-8")
            metadata1[key1] = metadata[key]
        hashcontents = encode(metadata1['info'])
        digest = sha1(hashcontents).digest()
        b32hash = b32encode(digest).decode("utf-8")
        magneturi_list.append('magnet:?xt=urn:btih:%s' % b32hash)
    thunder_download(magneturi_list)


def update():
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko)'
                             ' Chrome/78.0.3904.108 Safari/537.36'}
    try:
        html = requests.get('https://github.com/gyc123456-1/Internet-Download-Tools', headers=headers).text
        with open('html.txt', 'w', errors='ignore') as file:
            file.write(html)
    except EOFError:
        print('无法连接到更新服务器,请检查你的网络!')
    else:
        with open('html.txt') as file:
            html = file.readlines()
            new_version = html[1034]
        unlink('html.txt')
        new_version = float(new_version[-8:-5])
        if version == new_version:
            print('当前已是最新版本!')
        elif version < new_version:
            print('有新版本可用,版本号为{},正在自动下载!'.format(new_version))
            url_download(['https://github.com/gyc123456-1/Internet-Download-Tools/archive/main.zip'])
        else:
            print('错误!此程序被修改,正在退出!')
            exit()


try:
    url = argv[1]
except IndexError:
    while True:
        mode = input(
            '请输入模式(1.输入链接下载 2.输入存放链接的txt文档的路径下载 3.迅雷链接下载 4.输入存放迅雷链接的txt文档的路径下载 '
            '5.TB种子下载 6.输入存放TB种子路径的txt文档的路径下载 7.检查更新 8.关于 9.退出):')
        if mode == '1':
            url_download(input('请输入下载链接(多个用英文逗号分开):').rsplit(','))
        elif mode == '2':
            with open(input('请输入文件路径(每一个链接占一行):')) as links_file:
                download_urls = links_file.readlines()
            url_download(download_urls)
        elif mode == '3':
            thunder_download(input('请输入迅雷链接(多个用英文逗号分开):').rsplit(','))
        elif mode == '4':
            with open(input('请输入文件路径(每一个链接占一行):')) as links_file:
                download_urls = links_file.readlines()
            thunder_download(download_urls)
        elif mode == '5':
            TB_path_list = input().rsplit(',')
        elif mode == '6':
            with open(input('请输入文件路径(每一个链接占一行):')) as TB_file_list:
                download_TB_file = TB_file_list.readlines()
            torrent_download(download_TB_file)
        elif mode == '7':
            update()
        elif mode == '8':
            print('''
                                Internet Download Tools📥,版本{}
                    copyright © {}-{} system-windows on bilibili and github
            '''.format(version, 2020 + int(version), ctime()[-4:]))
            sleep(2)
        elif mode == '9':
            break
        else:
            print('输入错误,请重新输入!')
else:
    if 'http://' in url or 'https://' in url:
        url_download([url])
    elif 'ed2k://' in url or 'thunder://' in url or 'magnet:?xt=urn:btih:' in url or 'ftp://' in url:
        thunder_download([url])
    else:
        torrent_download([url])
