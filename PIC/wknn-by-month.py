import csv
import math
from datetime import datetime
from collections import OrderedDict
from decimal import Decimal
# import pandas as pd
import numpy as np
from matplotlib import pyplot as plt
import timeit
import time
import os
import logging
from tqdm import trange
from collections import Counter


def timestamp2datetime(timeStamp):
    try:
        d = datetime.fromtimestamp(int(timeStamp))
        str1 = d.strftime("%Y-%m-%d %H:%M:%S.%f")
        # 2015-08-28 16:43:37.283000'
        return str1
    except Exception as e:
        print(e)
        return ''


def clock(func):
    def clocked(*args):
        t0 = timeit.default_timer()
        result = func(*args)
        elapsed = timeit.default_timer() - t0
        logging.debug('Time_cost:[%0.8fs]' % elapsed)
        return result

    return clocked


def n2s(num):
    if num <= 9:
        return '0' + str(num)
    else:
        return str(num)


# 绘图函数
# 参数依次为list,抬头,X轴标签,Y轴标签,XY轴的范围
def draw_plot_rp(myList, Title, Xlabel, Ylabel):
    y1 = myList
    x1 = range(0, 96, 1)
    plt.plot(x1, y1, label='Error', linewidth=1, color='r', marker='o', markerfacecolor='blue', markersize=3)
    plt.xlabel(Xlabel)
    plt.ylabel(Ylabel)
    plt.title(Title)
    plt.legend()
    plt.show()


# 参数依次为list,抬头,X轴标签,Y轴标签,XY轴的范围
def draw_plot_month(myList, Title, Xlabel, Ylabel, No):
    y1 = myList
    x1 = range(1, 16, 1)
    plt.figure(int(No))
    plt.plot(x1, y1, label='Error WKNN', linewidth=1, color='r', marker='o', markerfacecolor='green', markersize=2)
    plt.xlabel(Xlabel)
    plt.ylabel(Ylabel)
    plt.title(Title)
    plt.savefig('WKNN-Error-75 of month No.%s.png' % No)
    logging.info('Fig saved!')
    plt.legend()
    plt.ion()
    plt.pause(1)
    plt.close()


def draw_error_acc(error_file, Title, Xlabel, Ylabel):
    lines = []
    with open(error_file, 'r') as f:
        lines = f.read().split('\n')

    dataSets = []
    for line in lines:
        # print(line)
        try:
            dataSets.append(line.split(','))
        except:
            print("Error: Exception Happened... \nPlease Check Your Data Format... ")

    temp = []
    for set in dataSets:
        temp2 = []
        for item in set:
            if item != '':
                temp2.append(float(item))
        temp2.sort()
        temp.append(temp2)
    dataSets = temp

    for set in dataSets:
        plotDataset = [[], []]
        count = len(set)
        for i in range(count):
            plotDataset[0].append(float(set[i]))
            plotDataset[1].append((i + 1) / count)
        # print(plotDataset)
        plt.plot(plotDataset[0], plotDataset[1], '-', linewidth=2)

    plt.xlabel(Xlabel)
    plt.ylabel(Ylabel)
    plt.title(Title)
    # plt.savefig(error_file[:-4] + '.png')
    # logging.info('error CDF saved!')
    plt.show()


# 按照参考点生成指纹库 每个参考点对应一个指纹 原方法
def rss_crd(tra_filename):
    """
    :param tra_filename: 训练集文件名
    :return: 指纹库
    """
    # get raw data from .csv file

    # get rss

    fp_coor = {}

    with open(tra_filename) as f:
        reader = list(csv.reader(f))
        fp_len = len(reader[0])
        for i in range(len(reader)):
            if i % 6 == 0:
                continue
            if i % 6 == 1:
                fp = fp_len * [0]
            for j in range(fp_len):
                if reader[i][j] == '100':
                    fp[j] = fp[j] - 105
                else:
                    fp[j] = fp[j] + int(reader[i][j])
            if i % 6 == 5:
                for j in range(fp_len):
                    fp[j] = fp[j] // 5
                    # if fp[j] == -100:
                    #    fp[j] = 100
                fp_coor['rp' + str(i // 6)] = fp

    # get crd match fp

    crd_filename = tra_filename.split('.')[0][:-3] + 'crd.csv'
    with open(crd_filename) as crd:
        coor = list(csv.reader(crd))
        crd_len = len(coor)
        for i in range(0, crd_len, 6):
            fp_coor['rp' + str(i // 6)] = fp_coor['rp' + str(i // 6)] + coor[i]

    return fp_coor

# 按照参考点生成指纹库 每个参考点对应一个指纹 最大值替换平均值
def rss_crd_max(tra_filename):
    """
    :param tra_filename: 训练集文件名
    :return: 指纹库
    """
    # get raw data from .csv file

    # get rss

    fp_coor = {}

    with open(tra_filename) as f:
        reader = list(csv.reader(f))
        r_len = int(len(reader))
        fp_len = len(reader[0])
        rss = np.array(list(map(int, reader[0])))
        for i in range(1, r_len):
            rss = np.vstack((rss, list(map(int, reader[i]))))
        rss[rss == 100] = -105

    max_rss = [0] * r_len
    for i in range(0, r_len, 6):
        _max_rss = np.max(rss[i:i + 6, :], 0)
        if i == 0:
            max_rss = _max_rss
        else:
            max_rss = np.vstack((max_rss, _max_rss))

    for i in range(0, r_len, 6):
        fp_coor['rp' + str(i // 6)] = list(map(str, max_rss[i // 6, :]))

    # get crd match fp

    crd_filename = tra_filename.split('.')[0][:-3] + 'crd.csv'
    with open(crd_filename) as crd:
        coor = list(csv.reader(crd))
        crd_len = len(coor)
        for i in range(0, crd_len, 6):
            fp_coor['rp' + str(i // 6)] = fp_coor['rp' + str(i // 6)] + coor[i]

    return fp_coor, max_rss

# 实现聚类
def k_means(f_rss):
    max_itor = 50

    pass

# 高斯滤波预处理 RSS属于(u-o，u+o) 效果不佳

# 按照参考点生成指纹库 每个参考点对应一个指纹 原方法
# def rss_crd(tra_filename):
#     """
#     :param tra_filename: 训练集文件名
#     :return: 指纹库
#     """
#     # get raw data from .csv file
#
#     # get rss
#
#     fp_coor = {}
#
#     with open(tra_filename) as f:
#         reader = list(csv.reader(f))
#         fp_len = len(reader[0])
#         for i in range(len(reader)):
#             if i % 6 == 0:
#                 fp = fp_len * [0]
#             for j in range(fp_len):
#                 if reader[i][j] == '100':
#                     fp[j] = fp[j] - 105
#                 else:
#                     fp[j] = fp[j] + int(reader[i][j])
#             if i % 6 == 5:
#                 for j in range(fp_len):
#                     fp[j] = fp[j] // 6
#                     # if fp[j] == -100:
#                     #    fp[j] = 100
#                 fp_coor['rp' + str(i // 6)] = fp
#
#     # get crd match fp
#
#     crd_filename = tra_filename.split('.')[0][:-3] + 'crd.csv'
#     with open(crd_filename) as crd:
#         coor = list(csv.reader(crd))
#         crd_len = len(coor)
#         for i in range(0, crd_len, 6):
#             fp_coor['rp' + str(i // 6)] = fp_coor['rp' + str(i // 6)] + coor[i]
#
#     return fp_coor

def rss_crd_filter(tra_filename):
    """
    :param tra_filename: 训练集文件名
    :return: 指纹库
    """
    # get raw data from .csv file

    # get rss

    fp_coor = {}

    with open(tra_filename) as f:
        reader = list(csv.reader(f))
        r_len = len(reader)
        fp_len = len(reader[0])
        rss = np.array(list(map(int, reader[0])))
        for i in range(1, r_len):
            rss = np.vstack((rss, list(map(int, reader[i]))))
        rss[rss == 100] = -105

    up_rss = [0] * r_len
    down_rss = [0] * r_len
    for i in range(0, r_len, 6):
        mean_rss = np.mean(rss[i:i + 6, :], 0)
        std_rss = np.std(rss[i:i + 6, :], 0)
        if i == 0:
            up_rss = mean_rss + std_rss
            down_rss = mean_rss - std_rss
        else:
            _up_rss = mean_rss + std_rss
            _down_rss = mean_rss - std_rss
            up_rss = np.vstack((up_rss, _up_rss))
            down_rss = np.vstack((down_rss, _down_rss))

    for i in range(r_len):
        index = i // 6
        if i % 6 == 0:
            fp = [0] * fp_len
            count = [0] * fp_len
        for j in range(fp_len):
            if down_rss[index][j] <= rss[i][j] <= up_rss[index][j]:
                count[j] = count[j] + 1
                fp[j] = fp[j] + rss[i][j]
        if i % 6 == 5:
            for j in range(fp_len):
                fp[j] = fp[j] / count[j]
            fp_coor['rp' + str(i // 6)] = fp

    crd_filename = tra_filename.split('.')[0][:-3] + 'crd.csv'
    with open(crd_filename) as crd:
        coor = list(csv.reader(crd))
        crd_len = len(coor)
        for i in range(0, crd_len, 6):
            fp_coor['rp' + str(i // 6)] = fp_coor['rp' + str(i // 6)] + coor[i]

    return fp_coor


# 引入SSD
def rss_crd_ssd(tra_filename):
    """
    :param tra_filename: 训练集文件名
    :return: 指纹库
    """
    # get raw data from .csv file

    # get rss

    fp_coor = {}

    with open(tra_filename) as f:
        reader = list(csv.reader(f))
        r_len = int(len(reader) / 2)
        fp_len = len(reader[0]) - 1
        rss = np.array(list(map(int, reader[0])))
        for i in range(1, r_len):
            rss = np.vstack((rss, list(map(int, reader[i]))))
        rss[rss == 100] = -105

    ssd = np.copy(rss[:, 1:])
    # 使用copy不会影响原来rss的值
    rss1 = rss[:, 0]
    for i in range(fp_len):
        ssd[:, i] = ssd[:, i] - rss1

    rss = ssd

    for i in range(r_len):
        if i % 6 == 0:
            fp = fp_len * [0]
        for j in range(fp_len):
            fp[j] = fp[j] + int(reader[i][j])
        if i % 6 == 5:
            for j in range(fp_len):
                fp[j] = fp[j] // 6
                # if fp[j] == -100:
                #    fp[j] = 100
            fp_coor['rp' + str(i // 6)] = fp
    final_rss = rss

    crd_filename = tra_filename.split('.')[0][:-3] + 'crd.csv'
    with open(crd_filename) as crd:
        coor = list(csv.reader(crd))
        crd_len = int(len(coor) / 2)
        for i in range(0, crd_len, 6):
            fp_coor['rp' + str(i // 6)] = fp_coor['rp' + str(i // 6)] + coor[i]

    return fp_coor, final_rss


# 引入RMSE 剔除粗大误差 取平均
def rss_crd_rmse(tra_filename):
    """
    :param tra_filename: 训练集文件名
    :return: 指纹库 字典形式fp_coor + 矩阵形式final_fp
    """
    # get raw data from .csv file

    # get rss

    fp_coor = {}

    with open(tra_filename) as f:
        reader = list(csv.reader(f))
        r_len = int(len(reader) / 2)
        fp_len = len(reader[0])
        rss = np.array(list(map(int, reader[0])))
        for i in range(1, r_len):
            rss = np.vstack((rss, list(map(int, reader[i]))))
        rss[rss == 100] = -105

    # query = rss[0, :]
    # tp_rss = np.tile(query, (r_len, 1))

    # RMSE预处理
    mean_rss = [0] * r_len
    for i in range(0, r_len, 6):
        _mean_rss = np.mean(rss[i:i + 6, :], 0)
        if i == 0:
            mean_rss = _mean_rss
        else:
            mean_rss = np.vstack((mean_rss, _mean_rss))

    # v 残差矩阵
    v = [0] * fp_len
    for i in range(r_len):
        _v = (rss[i] - mean_rss[i // 6]) ** 2
        if i == 0:
            v = _v
        else:
            v = np.vstack((v, _v))
    # sigma 均方根误差矩阵
    sigma = [0] * r_len
    for i in range(0, r_len, 6):
        _sigma = np.sqrt(0.2 * np.sum(v[i:i + 6, :], 0))
        if i == 0:
            sigma = _sigma
        else:
            sigma = np.vstack((sigma, _sigma))
    three_sigma = 3 * sigma

    v = np.sqrt(v)

    fv = [0] * r_len
    for i in range(r_len):
        _v = v[i] - three_sigma[i // 6]
        if i == 0:
            fv = _v
        else:
            fv = np.vstack((fv, _v))
    # v < 3 * simga 保留 存为1
    fv[fv >= 0] = 0
    fv[fv < 0] = 1
    # 对RSS进行过滤
    f_rss = fv * rss

    # 求均值 形成最终的RSS指纹
    final_rss = [0] * r_len
    count = [0] * r_len
    for i in range(0, r_len, 6):
        _f_rss = np.sum(f_rss[i:i + 6, :], 0)
        _count = np.sum(fv[i:i + 6, :], 0)
        if i == 0:
            final_rss = _f_rss
            count = _count
        else:
            final_rss = np.vstack((final_rss, _f_rss))
            count = np.vstack((count, _count))
    final_rss = final_rss / count

    where_are_nan = np.isnan(final_rss)
    final_rss[where_are_nan] = -105

    # powed RSS
    # min_t = np.min(final_rss)
    # # -105dBm
    # final_rss = final_rss - min_t
    # final_rss = (final_rss / (-min_t)) ** 2.71828

    for i in range(0, r_len, 6):
        fp_coor['rp' + str(i // 6)] = list(map(str, final_rss[i // 6, :]))

    crd_filename = tra_filename.split('.')[0][:-3] + 'crd.csv'
    with open(crd_filename) as crd:
        coor = list(csv.reader(crd))
        crd_len = int(len(coor) / 2)

        # 初始化第一行
        crd = np.array(list(map(float, coor[0])))
        fp_coor['rp' + str(0)] = fp_coor['rp' + str(0)] + coor[0]
        # 循环
        for i in range(6, crd_len, 6):
            crd = np.vstack((crd, list(map(float, coor[i]))))
            fp_coor['rp' + str(i // 6)] = fp_coor['rp' + str(i // 6)] + coor[i]

    # 拼接RSS与CRD
    final_fp = np.hstack((final_rss, crd))

    return fp_coor, final_fp


# 引入strong AP 概念 Fisher准则
def AP_r_get(tra_filename):
    """
    :param tra_filename: 训练集文件名
    :return: AP可靠性字典
    """
    # get raw data from .csv file

    # get rss

    fp_coor = {}

    with open(tra_filename) as f:
        reader = list(csv.reader(f))
        r_len = int(len(reader) / 2)
        fp_len = len(reader[0])
        rss = np.array(list(map(int, reader[0])))
        for i in range(1, r_len):
            rss = np.vstack((rss, list(map(int, reader[i]))))
        rss[rss == 100] = -105

    # ①信号强度大小 最大值 均值

    mean = rss.copy()
    mean[mean == -105] = 0

    p_rss = rss.copy()
    p_rss[p_rss != -105] = 1
    p_rss[p_rss == -105] = 0

    sum = np.max(mean, 0)
    p_sum = np.sum(p_rss, 0)
    # sum = sum / p_sum
    #
    # where_are_nan = np.isnan(sum)
    # sum[where_are_nan] = -105

    AP_rss = {}
    for i in range(fp_len):
        # AP_rss["AP" + str(i)] = 1
        AP_rss["AP" + str(i)] = float(Decimal((sum[i] + 105) / 105).quantize(Decimal('0.000')))
    # sort 升序排序
    # AP_rss = OrderedDict(sorted(AP_rss.items(), key=lambda d: d[1], reverse=True))

    # ②信号出现频率
    p_sum = p_sum / 288
    p_sum[p_sum <= 0.05] = 0

    AP_p = {}
    for i in range(fp_len):
        if p_sum[i] == 0:
            AP_p["AP" + str(i)] = 0
        elif p_sum[i] == 1:
            AP_p["AP" + str(i)] = 100
        else:
            AP_p["AP" + str(i)] = float(Decimal(1 / (1 - p_sum[i])).quantize(Decimal('0.000')))
    # sort 升序排序
    # AP_p = OrderedDict(sorted(AP_p.items(), key=lambda d: d[1], reverse=True))

    # ③Fisher-AP
    mean_ap = np.mean(rss, 0)
    var_rss = [0] * r_len
    mean_rss = [0] * r_len
    for i in range(0, r_len, 6):
        _var_rss = np.var(rss[i:i + 6, :], 0)
        _mean_rss = np.mean(rss[i:i + 6, :], 0)
        if i == 0:
            var_rss = _var_rss
            mean_rss = _mean_rss
        else:
            var_rss = np.vstack((var_rss, _var_rss))
            mean_rss = np.vstack((mean_rss, _mean_rss))

    # Fisher 准则
    up_sum = 0
    down_sum = 0
    for i in range(int(r_len / 6)):
        temp = (mean_rss[i] - mean_ap) ** 2
        up_sum = up_sum + (mean_rss[i] - mean_ap) ** 2
        down_sum = down_sum + var_rss[i] ** 2
    Fisher_ap = up_sum / down_sum

    where_are_nan = np.isnan(Fisher_ap)
    Fisher_ap[where_are_nan] = 0

    AP = {}
    for i in range(fp_len):
        AP["AP" + str(i)] = Fisher_ap[i]
        # AP["AP" + str(i)] = 1
    # sort 升序排序
    # AP = OrderedDict(sorted(AP.items(), key=lambda d: d[1], reverse=True))

    # 综合三种指标 形成AP的可靠性参数

    AP_r = {}
    for i in range(fp_len):
        AP_r["AP" + str(i)] = AP["AP" + str(i)] * AP_p["AP" + str(i)] * AP_rss["AP" + str(i)]
    # sort 升序排序
    AP_r = OrderedDict(sorted(AP_r.items(), key=lambda d: d[1], reverse=True))

    return AP_r


# 按照每个测量样本生成指纹库 每个参考点处的每次测量对应的一个指纹
def rss_crd_row(tra_filename):
    """
    :param tra_filename: 训练集文件名
    :return:指纹库
    """
    # get raw data from .csv file
    # fp_coor per row

    fp_coor = {}

    with open(tra_filename) as f:
        reader = list(csv.reader(f))
        fp_len = len(reader[0])
        for i in range(len(reader)):
            fp = [None] * fp_len
            if i % 6 == 0:
                fp_coor['row' + str(i)] = fp
            else:
                for j in range(fp_len):
                    if reader[i][j] == '100':
                        fp[j] = -105
                    else:
                        fp[j] = int(reader[i][j])
                fp_coor['row' + str(i)] = fp

    # get crd match fp

    crd_filename = tra_filename.split('.')[0][:-3] + 'crd.csv'
    with open(crd_filename) as crd:
        coor = list(csv.reader(crd))
        crd_len = len(coor)
        for i in range(crd_len):
            if i % 6 != 0:
                fp_coor['row' + str(i)] = fp_coor['row' + str(i)] + coor[i]
    return fp_coor

# 引入RMSE 剔除粗大误差 取平均
# def rss_crd_row(tra_filename):
#     """
#     :param tra_filename: 训练集文件名
#     :return: 指纹库
#     """
#     # get raw data from .csv file
#
#     # get rss
#
#     fp_coor = {}
#
#     with open(tra_filename) as f:
#         reader = list(csv.reader(f))
#         r_len = int(len(reader) / 2)
#         fp_len = len(reader[0])
#         rss = np.array(list(map(int, reader[0])))
#         for i in range(1, r_len):
#             rss = np.vstack((rss, list(map(int, reader[i]))))
#         rss[rss == 100] = -105
#
#     mean_rss = [0] * r_len
#     for i in range(0, r_len, 6):
#         _mean_rss = np.mean(rss[i:i + 6, :], 0)
#         if i == 0:
#             mean_rss = _mean_rss
#         else:
#             mean_rss = np.vstack((mean_rss, _mean_rss))
#
#     # RMSE 均方根误差
#     # v 残差矩阵
#     v = [0] * fp_len
#     for i in range(r_len):
#         _v = (rss[i] - mean_rss[i // 6]) ** 2
#         if i == 0:
#             v = _v
#         else:
#             v = np.vstack((v, _v))
#     # sigma 均方根误差矩阵
#     sigma = [0] * r_len
#     for i in range(0, r_len, 6):
#         _sigma = np.sqrt(0.2 * np.sum(v[i:i + 6, :], 0))
#         if i == 0:
#             sigma = _sigma
#         else:
#             sigma = np.vstack((sigma, _sigma))
#     three_sigma = 3 * sigma
#
#     v = np.sqrt(v)
#
#     fv = [0] * r_len
#     for i in range(r_len):
#         _v = v[i] - three_sigma[i // 6]
#         if i == 0:
#             fv = _v
#         else:
#             fv = np.vstack((fv, _v))
#     # v < 3 * simga 保留 存为1
#     fv[fv >= 0] = 0
#     fv[fv < 0] = 1
#     # 对RSS进行过滤
#     f_rss = fv * rss
#     f_rss[f_rss == 0] = -105
#
#     # # 求均值 形成最终的RSS指纹
#     # final_rss = [0] * r_len
#     # count = [0] * r_len
#     # for i in range(0, r_len, 6):
#     #     _f_rss = np.sum(f_rss[i:i + 6, :], 0)
#     #     _count = np.sum(fv[i:i + 6, :], 0)
#     #     if i == 0:
#     #         final_rss = _f_rss
#     #         count = _count
#     #     else:
#     #         final_rss = np.vstack((final_rss, _f_rss))
#     #         count = np.vstack((count, _count))
#     # final_rss = final_rss / count
#
#     # where_are_nan = np.isnan(final_rss)
#     # final_rss[where_are_nan] = -105
#
#     for i in range(r_len):
#         fp_coor['row' + str(i)] = list(map(str, f_rss[i, :]))
#
#     crd_filename = tra_filename.split('.')[0][:-3] + 'crd.csv'
#     with open(crd_filename) as crd:
#         coor = list(csv.reader(crd))
#         crd_len = int(len(coor) / 2)
#         for i in range(crd_len):
#             fp_coor['row' + str(i)] = fp_coor['row' + str(i)] + coor[i]
#
#     return fp_coor

# 根据楼层过滤数据
def floor_filter(tra, floor):
    f_c_tra = {}
    for rp, fp in tra.items():
        if fp[-1] == floor:
            f_c_tra[rp] = fp
    return f_c_tra


# 通过AP_r获取AP_list
def r2list(AP_r):
    """
    :param AP_r:
    :return:
    """
    tag = 0
    ap_list = []
    ap_mat_list = []
    for key in AP_r.keys():
        tag = tag + 1
        if tag > 50:
            break
        else:
            ap_list.append(key)
            ap_mat_list.append(int(key[2:]))
    return ap_list, ap_mat_list


# 获取训练集对应的r参数字典
def radius_get(f_c_tra, AP_r):
    """
    :param f_c_tra:指纹库
    :return: radius_dict:对应每个参考点的r参数字典 rp：r
    """
    radius_dict = {}
    euclid_dis = {}
    AP_list = r2list(AP_r)
    for out_rp in f_c_tra.keys():
        for in_rp, fp in f_c_tra.items():
            fp_lens = len(fp) - 3
            temp_dis = 0
            # 欧氏距离
            for i in range(fp_lens):
                temp_dis = temp_dis + (float(fp[i]) - float(f_c_tra[out_rp][i])) ** 2
            euclid_dis[in_rp] = [float(Decimal(math.sqrt(temp_dis)).quantize(Decimal('0.000'))),
                                 [f_c_tra[in_rp][-3], f_c_tra[in_rp][-2]]]
            # 优选
            # for i in AP_list:
            #     temp_dis = temp_dis + (float(fp[int(i[2:])]) - float(f_c_tra[out_rp][int(i[2:])])) ** 2
            # euclid_dis[in_rp] = [float(Decimal(math.sqrt(temp_dis)).quantize(Decimal('0.000'))),
            #                      [f_c_tra[in_rp][-3], f_c_tra[in_rp][-2]]]
        euclid_dis = OrderedDict(sorted(euclid_dis.items(), key=lambda d: d[1]))
        min_dis = list(euclid_dis.values())
        for i in range(len(min_dis)):
            if min_dis[i][1] != min_dis[0][1]:
                radius_dict[out_rp] = min_dis[i][0]
                break
    return radius_dict


# 寻找对应dict中前k个rp点较多rp对应的类
def class_get(dis_dict, k, tra_data):
    tag = 1
    class_list = []
    class_dict = {}
    for key in dis_dict.keys():
        if tag > k:
            break
        else:
            tag = tag + 1
            class_list.append(tra_data[key][-3] + "-"+ tra_data[key][-2])
    len_list = len(class_list)
    for i in range(len_list):
        class_dict[i] = class_list.count(class_list[i])
    class_dict = OrderedDict(sorted(class_dict.items(), key=lambda d: d[1], reverse=True))
    for key in class_dict.keys():
        return class_list[int(key)]


# 指纹匹配方法
def tst_rss_crd(f_c_tra, f_c_tst, k, tst_rp, radius_dict, AP_r):
    # euclidean metric
    euclid_dis = {}

    # for i in range(448):
    #     AP_r["AP" + str(i)] = AP_r["AP" + str(i)] * AP_r_tst["AP" + str(i)]
    #
    # AP_r = OrderedDict(sorted(AP_r.items(), key=lambda d: d[1], reverse=True))

    AP_list, ap_mat_list = r2list(AP_r)

    # cont = {}

    # M-WKNN
    # m_dis = {}
    # # 计算指纹之间的曼哈顿距离
    # for rp, fp in f_c_tra.items():
    #     temp_dis = 0
    #     sum = 0
    #     fp_lens = len(fp) - 3
    #     for i in range(fp_lens):
    #         temp_dis = temp_dis + np.abs(float(fp[i]) - float(f_c_tst[tst_rp][i]))
    #
    #     m_dis[rp] = 1 / (1.01 ** temp_dis)
    #     # sum = sum + m_dis[rp]
    #
    # weight = OrderedDict(m_dis)
    #
    # tag = 1
    # xcoor, ycoor, sum_weight = 0, 0, 0
    #
    # for rp, w in weight.items():
    #     if tag > k:
    #         break
    #     else:
    #         tag = tag + 1
    #         rpx, rpy = float(f_c_tra[rp][-3]), float(f_c_tra[rp][-2])
    #         xcoor = xcoor + rpx * w
    #         ycoor = ycoor + rpy * w
    #         sum_weight = sum_weight + w
    #
    # xcoor = float(Decimal(xcoor / sum_weight).quantize(Decimal('0.00')))
    # ycoor = float(Decimal(ycoor / sum_weight).quantize(Decimal('0.00')))

    # 计算指纹之间的欧氏距离

    # 指纹相似度比较 by MAT

    temp_dis = np.zeros((np.shape(f_c_tra)))
    query = f_c_tst[int(tst_rp[2:])]
    f_tst = np.tile(query, (np.shape(temp_dis)[0], 1))

    temp_dis = (f_c_tra - f_tst) ** 2
    # rp_points = np.sqrt(np.sum(temp_dis[:, ap_mat_list], axis=1))
    rp_points = np.sqrt(np.sum(temp_dis[:, 0:448], axis=1))

    for i, dis in enumerate(rp_points):
        euclid_dis["rp" + str(i)] = dis

    # 原方法
    # for rp, fp in f_c_tra.items():
    #     temp_dis = 0
    #     fp_lens = len(fp) - 3
    #
    #     # for i in range(fp_lens):
    #     #     temp_dis = temp_dis + (float(fp[i]) - float(f_c_tst[tst_rp][i])) ** 2
    #     for i in AP_list:
    #         temp_dis = temp_dis + (float(fp[int(i[2:])]) - float(f_c_tst[tst_rp][int(i[2:])])) ** 2
    #
    #     euclid_dis[rp] = float(Decimal(math.sqrt(temp_dis)).quantize(Decimal('0.00')))
    #     # cont[rp] = float(Decimal(math.sqrt(temp_dis)).quantize(Decimal('0.00')))

    # using r 使用r参数
    # if radius_dict != {}:
    #     for rp, dis in euclid_dis.items():
    #         euclid_dis[rp] = dis / radius_dict[rp]

    # sort 升序排序
    euclid_dis = OrderedDict(sorted(euclid_dis.items(), key=lambda d: d[1]))

    # k = get_k(euclid_dis)
    # cont = OrderedDict(sorted(cont.items(), key=lambda d: d[1]))

    # weighted knn (Fuzzy KNN m = 3)

    weight = {}
    for rp, dis in euclid_dis.items():
        weight[rp] = 1 / (dis + 1e-8)
    weight = OrderedDict(weight)

    # Fuzzy KNN m = ?

    # weight = {}
    # for rp, dis in euclid_dis.items():
    #     weight[rp] = 1 / (dis + 1e-8)
    # weight = OrderedDict(weight)

    tag = 1
    xcoor, ycoor, sum_weight = 0, 0, 0

    for rp, w in weight.items():
        if tag > k:
            break
        else:
            tag = tag + 1
            rpx, rpy = float(f_c_tra[int(rp[2:]), -2]), float(f_c_tra[int(rp[2:]), -1])
            xcoor = xcoor + rpx * w
            ycoor = ycoor + rpy * w
            sum_weight = sum_weight + w

    xcoor = float(Decimal(xcoor / sum_weight).quantize(Decimal('0.000')))
    ycoor = float(Decimal(ycoor / sum_weight).quantize(Decimal('0.000')))

    # knn
    # not using r 不使用r参数 使用KNN方法估计位置坐标

    # if radius_dict == {}:
    #     tag = 1
    #     xcoor, ycoor = 0, 0
    #
    #     for rp in euclid_dis.keys():
    #         if tag > k:
    #             break
    #         else:
    #             tag = tag + 1
    #             rpx, rpy = float(f_c_tra[rp][-3]), float(f_c_tra[rp][-2])
    #             xcoor = xcoor + rpx
    #             ycoor = ycoor + rpy
    #
    #     xcoor = float(Decimal(xcoor / k).quantize(Decimal('0.000')))
    #     ycoor = float(Decimal(ycoor / k).quantize(Decimal('0.000')))

    # using-r 使用r参数

    # elif radius_dict != {}:
    #     new_dis = {}
    #
    #     for rp, value in euclid_dis.items():
    #         if value <= 1:
    #             new_dis[rp] = value
    #         else:
    #             break
    #
    #     # 如果值均大于1，则寻找前k个rp中出现次数最多的类当做分类结果
    #     if new_dis == {}:
    #         class_1 = class_get(euclid_dis, k, f_c_tra)
    #         xcoor = class_1.split("-")[0]
    #         ycoor = class_1.split("-")[1]
    #     else:
    #         len_new_dis = len(new_dis)
    #         class_2 = class_get(new_dis, len_new_dis, f_c_tra)
    #         xcoor = class_2.split("-")[0]
    #         ycoor = class_2.split("-")[1]

    # 测试rp点的真实坐标
    [realx, realy] = f_c_tst[int(tst_rp[2:]), [-2, -1]]

    # vis_temp = [tst_rp, realx, realy, xcoor, ycoor]

    # visible_file = r'E:\db\wknn919_point_visible.csv'
    # with open(visible_file, 'a+', newline='') as vis:
    #     writer = csv.writer(vis)
    #     writer.writerow(vis_temp)

    # 计算定位误差
    error_dis = (float(xcoor) - float(realx)) ** 2 + (float(ycoor) - float(realy)) ** 2

    error_dis = float(Decimal(math.sqrt(error_dis)).quantize(Decimal('0.000')))

    # print('%s target coordinates : (%s, %s) , error = %s' % (tst_rp, xcoor, ycoor, error_dis))

    return error_dis


# 实现仿真定位部分
def select_tra_tst(month, test_no, fp_coor_tra, radius_d, floor, row_state, AP_r):
    logging.debug('Reading train_data and test_data.')

    # 生成待读取测试集文件名
    tst_filename = "E:\\db\\" + n2s(month) + "\\tst" + n2s(test_no) + "rss.csv"

    # 设定w_k参数
    w_k = 3

    # 获取指纹训练样本集，按照r参数分开处理
    if row_state == 1:
        fp_coor_tst = floor_filter(rss_crd_row(tst_filename), floor)
    else:
        fp_coor, fp_mat = rss_crd_rmse(tst_filename)
        # AP_r_tst = AP_r_get(tst_filename)
        # 字典
        # fp_coor_tst = floor_filter(fp_coor, floor)
        # 矩阵
        fp_coor_tst = np.delete(fp_mat, -1, axis=1)

    # # 将处理后的RSS写入csv文件
    # output_file = 'E:\\db\\cdf2019\\m2_data\\m2-online.csv'
    # with open(output_file, 'a+', newline='') as csvfile:
    #     writer = csv.writer(csvfile)
    #     for i in range(48):
    #         writer.writerow(fp_coor_tst[i])

    error_s = []
    # error_s 数组保存定位误差，用于绘制CDF图
    for rp in range(np.shape(fp_coor_tst)[0]):
        # 按照row参数的取值，分为两种情况进行定位误差估计
        # 上面的rp是指从测试集中选取出的参考点序号
        if row_state == 0:
            e_dis = tst_rss_crd(fp_coor_tra, fp_coor_tst, w_k, 'rp' + str(rp), radius_d, AP_r)
            error_s = error_s + [e_dis]
        elif rp % 6 != 0 and row_state == 1:
            e_dis = tst_rss_crd(fp_coor_tra, fp_coor_tst, w_k, 'row' + str(rp), radius_d, AP_r)
            error_s = error_s + [e_dis]

    # 75%的定位误差
    err_75 = np.percentile(np.array(error_s), 75)
    err_75 = float(Decimal(err_75).quantize(Decimal('0.000')))

    # 将定位误差写入csv文件
    output_file = 'E:\\db\\cdf2019\\wknn-5.31.csv'
    with open(output_file, 'a+', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(error_s)

    # 记录日志
    logging.debug('error_list -> .csv file: OK!')
    logging.debug('max error = %s, min error = %s' % (max(error_s), min(error_s)))

    # 画直方图
    # draw_plot_rp(error_s, 'Error Distance Plot', 'RP', 'error/m')  # 直方图展示
    # draw_error_acc(output_file, 'Error CDF Graph', 'error/m', 'percentage')  # 累计误差分布图

    return err_75


def main():
    # 配置日志设置
    LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
    DATE_FORMAT = "%m/%d/%Y %H:%M:%S %p"
    logging.basicConfig(level=logging.INFO, format=LOG_FORMAT, datefmt=DATE_FORMAT)
    np.seterr(divide='ignore', invalid='ignore')
    logging.info('Start test!')
    # 测试序列
    # output_merge_file = 'E:\\db\\wknn_error\\wknn-m2-ori.csv'

    # param
    test_m_end = 2
    test_m_start = 2
    # 训练集序号
    test_tra_no = 1
    floor = "3"
    # 是否引入r参数
    r_state = 0
    # 是否使用全部测量样本
    row_state = 0

    # match by month 根据月份来进行实验
    for month in range(test_m_start, test_m_end + 1):

        # read trn data 生成训练集文件名
        filename = "E:\\db\\" + n2s(month) + "\\trn" + n2s(test_tra_no) + "rss.csv"

        # using r_statue row_state
        if r_state == 0 and row_state == 0:
            fp_coor, fp_mat = rss_crd_rmse(filename)
            AP_r = AP_r_get(filename)
            # 字典
            # tra_data = floor_filter(fp_coor, floor)
            # 矩阵
            tra_data = np.delete(fp_mat, -1, axis=1)

            # # 将处理后的RSS写入csv文件
            # output_file = 'E:\\db\\cdf2019\\m2_data\\m2-offline.csv'
            # with open(output_file, 'a+', newline='') as csvfile:
            #     writer = csv.writer(csvfile)
            #     for i in range(48):
            #         writer.writerow(tra_data[i])

            # 方案一 奇数RP用于测试
            # f_odd = {}
            # for k, v in tra_data.items():
            #     if int(k[2:]) % 2 == 0:
            #         f_odd[k] = v
            # tra_data = f_odd

            # # 方案三
            # f_odd = {}
            # for k, v in tra_data.items():
            #     if int(k[2:]) % 6 != 0 and int(k[2:]) % 6 != 1:
            #         f_odd[k] = v
            # tra_data = f_odd

            radius = {}
        elif r_state == 0 and row_state == 1:
            tra_data = floor_filter(rss_crd_row(filename), floor)

            # 选择奇数RP用于测试
            # f_odd = {}
            # for k, v in tra_data.items():
            #     if (int(k[3:]) // 6) % 2 == 0:
            #         f_odd[k] = v
            # tra_data = f_odd

            # 方案三
            # f_odd = {}
            # for k, v in tra_data.items():
            #     new_rp = int(k[3:]) // 6
            #     if new_rp % 6 != 0 and new_rp % 6 != 1:
            #         f_odd[k] = v
            # tra_data = f_odd

            radius = {}
        elif r_state == 1 and row_state == 0:
            fp_coor, final_rss = rss_crd_rmse(filename)
            AP_r = AP_r_get(filename)
            tra_data = floor_filter(fp_coor, floor)

            # 选择奇数RP用于测试
            # f_odd = {}
            # for k, v in tra_data.items():
            #     if int(k[2:]) % 2 == 0:
            #         f_odd[k] = v
            # tra_data = f_odd

            # 方案三
            # f_odd = {}
            # for k, v in tra_data.items():
            #     if int(k[2:]) % 6 != 0 and int(k[2:]) % 6 != 1:
            #         f_odd[k] = v
            # tra_data = f_odd

            radius = radius_get(tra_data, AP_r)
        else:
            tra_data = floor_filter(rss_crd_row(filename), floor)
            AP_r = AP_r_get(filename)
            # 选择奇数RP用于测试
            # f_odd = {}
            # for k, v in tra_data.items():
            #     if (int(k[3:]) // 6) % 2 == 0:
            #         f_odd[k] = v
            # tra_data = f_odd

            # 方案三
            # f_odd = {}
            # for k, v in tra_data.items():
            #     new_rp = int(k[3:]) // 6
            #     if new_rp % 6 != 0 and new_rp % 6 != 1:
            #         f_odd[k] = v
            # tra_data = f_odd

            radius = radius_get(tra_data)

        # match test set error_list用于绘图
        error_list = []
        for test_no in trange(1, 6):
            error_75 = select_tra_tst(month, test_no, tra_data, radius, floor, row_state, AP_r)
            error_list = error_list + [error_75]
        # print(error_list)

    logging.info('Test end!')

    # for test_tst_no in range(1, 6):
    #     error_list = month_error_75_func(test_m_start, test_m_end, test_tra_no, test_tst_no)
    #     # draw_plot_month(error_list, 'Error Distance Plot TEST NO.%s' % test_tst_no, 'Month', 'error/m', test_tst_no)
    #     with open(output_merge_file, 'a+', newline='') as csvfile:
    #         writer = csv.writer(csvfile)
    #         # writer.writerow([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15])
    #         writer.writerow(error_list)


if __name__ == "__main__":
    main()
