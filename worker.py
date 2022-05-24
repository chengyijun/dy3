# -*- coding:utf-8 -*-
# 作者: 程义军
# 时间: 2022/5/24 14:27
import math
import operator
import typing

import PIL
import cv2
import numpy as np
import pyautogui
from PIL import ImageGrab
from PyQt5.QtCore import QThread, pyqtSignal, QObject

from config import Config


class Worker(QThread):
    data_signal = pyqtSignal(PIL.Image.Image, str)

    def __init__(self, parent: typing.Optional[QObject] = None) -> None:
        super().__init__(parent)
        self.handle_config()

    def handle_config(self):
        """
        处理配置
        :return:
        """

        config = Config()
        config_dict = config.read_config()

        # # 坐标样式的字符串转化为坐标样式的元祖
        t1 = tuple([int(t) for t in config_dict.get("left_top_point").split(",")])
        config_dict.update({"left_top_point": t1})
        t2 = tuple([int(t) for t in config_dict.get("right_down_point").split(",")])
        config_dict.update({"right_down_point": t2})
        t3 = tuple([int(t) for t in config_dict.get("target").split(",")])
        config_dict.update({"target": t3})
        t4 = tuple([int(t) for t in config_dict.get("mark").split(",")])
        config_dict.update({"mark": t4})
        t5 = tuple([int(t) for t in config_dict.get("course_position").split(",")])
        config_dict.update({"course_position": t5})

        # 找色区域左上点坐标
        self.left_top_point = config_dict.get("left_top_point")
        # print("------------------", self.left_top_point, type(self.left_top_point))
        # 找色区域右下点坐标
        self.right_down_point = config_dict.get("right_down_point")
        # 目标点色值
        self.target = config_dict.get("target")
        # 找目标点的允许的色值容差
        self.color_allowance = config_dict.get("color_allowance")
        # 给目标点上色的色值
        self.mark = config_dict.get("mark")
        # 检测上钩频率 (单位：ms)
        self.frequency = config_dict.get("frequency")
        # 判定上钩 水花阈值
        self.threshold = config_dict.get("threshold")
        # 判定上钩 检测半径
        self.radius = config_dict.get("radius")
        # 二值化阈值
        self.threshold_point = config_dict.get("threshold_point")
        # 甩杆后鼠标停靠位置
        self.course_position = config_dict.get("course_position")
        # 甩杆后鼠标是否移开
        self.is_course_move = config_dict.get("is_course_move")

    def run(self) -> None:
        while True:
            self.exec_fish()
            QThread.msleep(self.frequency)

    def exec_fish(self):
        """
        钓鱼
        """

        self.get_screenshot()
        points = self.find_points_by_color()
        center_point = self.get_center_point(points)
        # 判断鱼漂是否存在
        if not operator.eq(center_point, (-1, -1)):
            # 鱼漂存在 判定上钩
            # 以鱼漂为中心点取一个正方形 100x100px
            img = ImageGrab.grab(
                bbox=(self.left_top_point[0] + center_point[0] - self.radius,
                      self.left_top_point[1] + center_point[1] - self.radius,
                      self.left_top_point[0] + center_point[0] + self.radius,
                      self.left_top_point[1] + center_point[1] + self.radius))
            # img.save("test.png")
            flag, percent = self.check_yp(img)
            if flag:
                res = f"{percent}\t鱼上钩了，收杆！！！"
                self.get_fish(center_point)
            else:
                res = f"{percent}\t耐心等待鱼儿咬钩..."

        else:
            # 鱼漂不存在 重新甩杆
            res = "鱼漂不存在 重新甩杆"
            self.start_fish()

        self.data_signal.emit(self.img, res)

    def start_fish(self):
        """
        甩杆
        :return:
        """

        if self.is_course_move:
            pyautogui.moveTo(*self.course_position)
        pyautogui.press("1")

    def get_fish(self, center_point):
        """
        收杆
        :param center_point:
        :return:
        """
        pyautogui.moveTo(self.left_top_point[0] + center_point[0], self.left_top_point[1] + center_point[1])
        pyautogui.rightClick()

    def check_yp(self, img) -> tuple[bool, float]:
        """
        判断是否咬钩
        通过鱼漂附近是否有水花判断
        :param img:
        :return:
        """
        # 反相
        res = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
        # 转灰度
        gray_img = cv2.cvtColor(res, cv2.COLOR_BGR2GRAY)
        # 二值化
        _, dst = cv2.threshold(gray_img, self.threshold_point, 255, cv2.THRESH_BINARY)
        total = len(dst.ravel())
        white = int(sum(dst.ravel()) / 255)
        percent = white / total
        flag = percent > self.threshold
        return flag, percent

    def get_screenshot(self):
        """
        获取屏幕中心截图
        只在此截图范围内检测是否存在鱼漂
        """
        self.img = ImageGrab.grab(bbox=(*self.left_top_point, *self.right_down_point))

    def find_points_by_color(self) -> list[tuple[int, int]]:
        """
        找鱼漂位置
        根据颜色找目标点
        """
        w = self.right_down_point[0] - self.left_top_point[0]
        h = self.right_down_point[1] - self.left_top_point[1]
        # 找到的目标点列表
        points = []
        for x in range(w):
            for y in range(h):
                r, g, b = self.img.getpixel((x, y))
                if all([abs(r - self.target[0]) < self.color_allowance, abs(g - self.target[1]) < self.color_allowance,
                        abs(b - self.target[2]) < self.color_allowance]):
                    # print(f"找到了：({x},{y})")
                    # 给目标点上色
                    self.img.putpixel((x, y), self.mark)
                    # 将找到的目标点添加到目标点列表中
                    points.append((x, y))
        return points

    @staticmethod
    def get_center_point(f: list[tuple[int, int]]) -> tuple[int, int]:
        """
        找一组点的中心点
        """
        if not f:
            print("没有找到任何点")
            return -1, -1
        d = [0 for _ in range(len(f))]

        # print(f"目标点：", f)
        for i in range(len(f)):
            for j in range(len(f)):
                d[i] = d[i] + math.sqrt((f[i][0] - f[j][0]) ** 2 + (f[i][1] - f[j][1]) ** 2)
        s = d[0]
        m = 0
        for i in range(len(f)):
            if d[i] < s:
                s = d[i]
                m = i
        return f[m][0], f[m][1]
