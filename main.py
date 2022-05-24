# -*- coding:utf-8 -*-
# 作者: 程义军
# 时间: 2022/5/24 13:55
import sys

import PIL
from PIL import ImageQt
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMainWindow, QApplication

from config import Config
from mainui_ui import Ui_MainWindow
from worker import Worker


class MainWin(QMainWindow, Ui_MainWindow):

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setupUi(self)
        # 重置一下作为画板的label_5的默认文字
        self.label_5.setText("")
        # 设置窗体大小
        self.resize(300, 770)
        # 事件绑定
        self.bind_event_handler()
        # 将配置数据解析到界面上
        self.show_config_to_view()

    def bind_event_handler(self):
        self.pushButton.clicked.connect(self.handle_modify_config)
        self.pushButton_2.clicked.connect(self.handle_start_fish_event)
        self.pushButton_3.clicked.connect(self.handle_end_fish_event)

    def show_config_to_view(self):
        """
        将配置数据解析到界面上
        :return:
        """
        # 读取配置文件
        self.config = Config()
        config_dict = self.config.read_config()
        # 回显扫描区域
        tmp1 = config_dict.get("left_top_point")
        tmp2 = config_dict.get("right_down_point")
        self.lineEdit.setText(f"{tmp1},{tmp2}")
        # 回显鱼漂取色
        self.lineEdit_2.setText(config_dict.get("target"))
        # 回显白色水花阈值
        self.lineEdit_3.setText(str(config_dict.get("threshold_point")))
        # 回显白色占比阈值
        self.lineEdit_4.setText(str(config_dict.get("threshold")))
        # 甩杆后是否移开鼠标
        is_course_move = config_dict.get("is_course_move")
        if is_course_move:
            self.radioButton.setChecked(True)
            self.radioButton_2.setChecked(False)
        else:
            self.radioButton.setChecked(False)
            self.radioButton_2.setChecked(True)

    def draw_img_to_label(self, img: PIL.Image.Image):
        """
        绘制图像到画布
        """
        # self.label.setPixmap(QPixmap("sc.png"))  # 我的图片格式为png.与代码在同一目录下
        # self.label.setScaledContents(True)  # 图片大小与label适应，否则图片可能显示不全

        # 将img对象加载到内存
        img.load()
        # 设置图片模式
        img.mode = "RGBA"
        # 根据图片创建一个Pixmap对象（也就是Qt能够使用的图片对象）
        pm = ImageQt.toqpixmap(img).scaled(self.label_5.size(), aspectRatioMode=Qt.KeepAspectRatio)
        # 将画布（QLabel）设置上图片
        self.label_5.setPixmap(pm)

    def handle_data_signal(self, img, res):
        # 显示实时的屏幕中心截图
        self.draw_img_to_label(img)
        # 显示钓鱼的信息
        self.textBrowser.append(res)

    def handle_start_fish_event(self):
        # 启动钓鱼线程
        # print(self.config.config_dict)
        self.textBrowser.append("开始钓鱼")
        self.worker = Worker()
        self.worker.data_signal.connect(self.handle_data_signal)
        self.worker.start()

    def handle_end_fish_event(self):
        self.textBrowser.append("停止钓鱼")
        self.worker.terminate()
        self.worker.deleteLater()

    def handle_modify_config(self):
        print("修改参数")
        tmp = self.lineEdit.text().split(",")
        # print(tmp)
        if self.buttonGroup.checkedButton().objectName() == "radioButton":
            is_course_move = True
        else:
            is_course_move = False

        # print(self.config.config_dict)
        modify_data = {
            "left_top_point": f"{tmp[0]},{tmp[1]}",
            "right_down_point": f"{tmp[2]},{tmp[3]}",
            "target": self.lineEdit_2.text(),
            "threshold_point": int(self.lineEdit_3.text()),
            "threshold": float(self.lineEdit_4.text()),
            "is_course_move": is_course_move,

        }

        # 读出原来的配置文件
        config_data = self.config.read_config()
        config_data.update(modify_data)
        self.config.modify_config(config_data)
        self.textBrowser.append("参数修改成功！")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_win = MainWin()
    main_win.show()
    sys.exit(app.exec_())
