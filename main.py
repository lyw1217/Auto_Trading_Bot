import sys
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QAxContainer import *

class MyWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyStock")
        self.setGeometry(300, 300, 300, 150)

        # 키움증권에서 제공하는 클래스는 각각 고유의 ProgID와 CLSID 를 가지는데
        # 해당 값을 QAxWidget 클래스의 생성자로 전달하면 인스턴스 생성
        # 컨트롤 클래스의 CLSID 는 "{A1574A0D-6BFA-4BD7-9020-DED88711818D}"
        # 레지스트리 편집기에서 검색하면 해당 CLSID 의 ProgID는 "KHOPENAPI.KHOpenAPICtrl.1"
        self.kiwoom = QAxWidget("KHOPENAPI.KHOpenAPICtrl.1")

        btn1 = QPushButton("Login", self)
        btn1.move(20, 20)
        btn1.clicked.connect(self.btn1_clicked)

        btn2 = QPushButton("Check state", self)
        btn2.move(20, 70)
        btn2.clicked.connect(self.btn2_clicked)

    # 인스턴스를 통해 메서드를 호출하면 기능이 실행됨
    # 키움증권 개발 가이드를 참고
    # OCX 방식에서는 QAxBase 클래스의 dynamicCall 메서드를 사용해 원하는 메서드 호출 가능
    # 즉, 키움증권의 Open API+ 가 제공하는 메서드를 사용하려면 self.kiwoom 객체를 통해 dynamicCall 메서드를 호출해야 함
    def btn1_clicked(self):
        # CommConnect()
        # 0 - 성공, 음수값 - 실패
        ret = self.kiwoom.dynamicCall("CommConnect()")

    def btn2_clicked(self):
        # GetConnectState()
        # 0 - 미연결, 1 - 연결 완료
        if self.kiwoom.dynamicCall("GetConnectState()") == 0:
            self.statusBar().showMessage("Not connected")
        else:
            self.statusBar().showMessage("Connected")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    myWindow = MyWindow()
    myWindow.show()
    app.exec_()