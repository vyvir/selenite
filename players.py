import os
import sys
import requests
import subprocess
import urllib.request
import re
from time import sleep
from datetime import datetime
from PySide6 import QtCore, QtWidgets, QtGui
import main

class PlayersWindow(QtWidgets.QWidget):
    def __init__(self, players_list=""):
        super().__init__()

        self.players_list = players_list
        print(self.players_list)

        self.local_path = os.path.join(
            os.environ.get("XDG_DATA_HOME") or f'{ os.environ["HOME"] }/.local/share',
            "selenite",
        )

        if not os.path.exists(self.local_path):  # Creates $HOME/.local/share/selenite
            os.mkdir(self.local_path)

        self.setWindowTitle("Players")

        self.create_tablewidget()

        self.text = QtWidgets.QLabel(f"{(len(self.players_list))} players", alignment=QtCore.Qt.AlignCenter)

        self.ref_button = QtWidgets.QPushButton("Refresh")

        self.join_button = QtWidgets.QPushButton("Join")

        self.layout = QtWidgets.QVBoxLayout(self)

        for i in (self.tablewidget, self.text, self.ref_button, self.join_button):
             self.layout.addWidget(i)

        self.ref_button.clicked.connect(self.ref_list)
        self.join_button.clicked.connect(self.join_srb2)
    
    @QtCore.Slot()
    def eventFilter(self, source, event):
        if event.type() == QtCore.QEvent.ContextMenu and source is self.tablewidget:
            
            self.menu = QtWidgets.QMenu()
            #self.menu.setIconSize(QtCore.QSize(32, 32))
            #self.menu.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)

            mn_items = [("fv", "star", "&Favorite", self.ip_join, "Ctrl+s"),
                    ("bl", "gear", "&Blocklist", self.settings, "Ctrl+b"),
                    ("pl", "gear", "&Players", self.settings, "Ctrl+Shift+s"),
                    ("fl", "gear", "&Files", self.settings, "Ctrl+Shift+f")]

            for i, (name, icon, label, action, shortcut) in enumerate(mn_items):
                name = QtGui.QAction(QtGui.QIcon(f"icons/{icon}.svg"), label, self)
                name.triggered.connect(action)
                name.setShortcut(QtGui.QKeySequence(shortcut))
                self.menu.addAction(name)

            if self.menu.exec(event.globalPos()):
                item = source.itemAt(event.pos())
                print(item.text())
            return True
        return super().eventFilter(source, event)
    
    @QtCore.Slot()
    def search_online(self):

        ip = QtWidgets.QInputDialog.getText(self, 'text', 'Enter the IP address')
        if not ip[1] == False:
            port = QtWidgets.QInputDialog.getText(self, 'text', 'Enter the port')
            if not port[1] == False:
                # Input validation
                try:
                    ipaddress.ip_address(ip[0])
                    try:
                        if 1 <= int(port[0]) <= 65535:
                            self.join_srb2(ip[0], port[0])
                        else:
                            self.warn("The port is invalid.")
                    except ValueError:
                        self.warn("The port is invalid.")
                except ValueError:
                    self.warn("The IP address is invalid.")
    
    @QtCore.Slot()
    def settings(self):
        self.widget = settings.SettingsWindow()
        self.widget.resize(900, 600)
        self.widget.show()
    
    @QtCore.Slot()
    def connection_check(self):
        #try:
            #urlopen("http://www.example.com", timeout=5)
            msgBox = QtWidgets.QMessageBox()
            msgBox.setText("Settings are WIP.")
            msgBox.exec()
        #except:
        #    return False   

    @QtCore.Slot()
    def fav_add(self):
        #msgBox = QtWidgets.QMessageBox()
        #msgBox.setText("Favorite server added!")
        #msgBox.exec()
        
        print("This worked")  

    @QtCore.Slot()
    def ref_list(self):
        self.layout_all.removeWidget(self.tablewidget)
        #for i in (self.tablewidget):
        #     self.layout_all.removeWidget(i)
        self.pull_server_list()
        self.create_tablewidget()
        self.layout_all.addWidget(self.tablewidget)
        #for i in (self.tablewidget):
        #     self.layout_all.addWidget(i)
                
    @QtCore.Slot()
    def join_srb2(self, ip="no", port="no"):
        if "no" in {ip, port}:
            ip = self.cur_row(0)
            print(self.cur_row(0))
            port = self.cur_row(16)
            print(self.cur_row(16))
        #srb2 = 'flatpak run org.srb2.SRB2'
        self.p = QtCore.QProcess()
        print("flatpak", ["run", "org.srb2.SRB2", "-connect", f"{ip}:{port}"])
        self.p.start("flatpak", ["run", "org.srb2.SRB2", "-connect", f"{ip}:{port}"])
        sleep(1)
        sys.exit(app.exec())

    @QtCore.Slot()
    def cur_row(self, row):
        return self.players_list[self.tablewidget.currentRow()][row]

    @QtCore.Slot()
    def warn(self, msg):
        Warning = QtWidgets.QMessageBox.warning(self, 'Warning', msg)
    
    @QtCore.Slot()
    def create_tablewidget(self):
        
        colcnt = len(self.players_list[0])
        rowcnt = len(self.players_list)

        self.tablewidget = QtWidgets.QTableWidget(rowcnt, colcnt)
        self.tablewidget.setSelectionBehavior(QtWidgets.QTableWidget.SelectRows);
        self.tablewidget.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        vheader = QtWidgets.QHeaderView(QtCore.Qt.Orientation.Vertical)
        vheader.setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self.tablewidget.setVerticalHeader(vheader)
        #self.tablewidget.setSortingEnabled(True)
        hheader = QtWidgets.QHeaderView(QtCore.Qt.Orientation.Horizontal)
        hheader.setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self.tablewidget.setHorizontalHeader(hheader)
        self.tablewidget.setHorizontalHeaderLabels(["Name", "Team", "Skin", "Score", "Time playing", "Tagged IT", "Holding CTF Flag", "Is Super"])

        #print(len(self.tuples_list[0]))
        #print(len(self.dict_list))
        for i, (name, team, skin, score, time, tagged_it, holding_ctf_flag, is_super) in enumerate(self.players_list):
                for j in range(colcnt):
                    item = QtWidgets.QTableWidgetItem(self.players_list[i][j])
                    self.tablewidget.setItem(i, j, item)

        self.tablewidget.setIconSize(QtCore.QSize(24, 24))
        self.tablewidget.installEventFilter(self)
    
    @QtCore.Slot()
    def files_data(self):
        pass

if __name__ == "__main__":
    app = QtWidgets.QApplication([])

    widget = FilesWindow()
    widget.resize(900, 600)
    widget.show()

    sys.exit(app.exec())