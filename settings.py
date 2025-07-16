import os
import sys
import requests
import subprocess
import urllib.request
import re
import maxminddb
import ipaddress
from time import sleep
from datetime import datetime
import sqlite3
from PySide6 import QtCore, QtWidgets, QtGui
import main

class SettingsWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Settings")
        
        self.flatpak_local_dir = srb2_dir = os.path.join(
            os.environ.get("XDG_DATA_HOME") or f'{ os.environ["HOME"] }/.var/app/org.srb2.SRB2',
            ".srb2",
        )

        self.native_local_dir = srb2_dir = os.path.join(
            os.environ.get("XDG_DATA_HOME") or f'{ os.environ["HOME"] }',
            ".srb2",
        )
        
        self.local_path = os.path.join(
            os.environ.get("XDG_DATA_HOME") or f'{ os.environ["HOME"] }/.local/share',
            "selenite",
        )
        
        self.text1 = QtWidgets.QLabel("Preferred SRB2 installation", alignment=QtCore.Qt.AlignCenter)
        
        self.combobox1 = QtWidgets.QComboBox()
        self.combobox1.addItems(['Flatpak', 'Other'])
        
        dir_dialog_icon = self.style().standardIcon(getattr(QtWidgets.QStyle.StandardPixmap, 'SP_FileDialogStart'))   
        
        self.fileOpenButton = QtWidgets.QPushButton('Select...',self)
        self.fileOpenButton.setIcon(dir_dialog_icon)
        self.fileOpenButton1 = QtWidgets.QPushButton('Select...',self)
        self.fileOpenButton1.setIcon(dir_dialog_icon)
        self.fileOpenButton2 = QtWidgets.QPushButton('Select...',self)
        self.fileOpenButton2.setIcon(dir_dialog_icon)

        self.bin_label = QtWidgets.QLabel("Path")
        self.dir_label = QtWidgets.QLabel("Local Folder")
        self.json_label = QtWidgets.QLabel("JSON URL")
        self.ua_label = QtWidgets.QLabel("User Agent")
        self.cdb_label = QtWidgets.QLabel("Country Database")
        
        #self.icon = QtGui.Qicon("document-new")
        #self.pushButton_n6.setIcon(icon)

        #self.text = QtWidgets.QLabel("Hello World", alignment=QtCore.Qt.AlignLeft)

        self.reset_button = QtWidgets.QPushButton("Reset")
        
        self.cancel_button = QtWidgets.QPushButton("Cancel")

        self.save_button = QtWidgets.QPushButton("Save")

        self.bin_edit = QtWidgets.QLineEdit()
        self.dir_edit = QtWidgets.QLineEdit()
        self.json_edit = QtWidgets.QLineEdit()
        self.ua_edit = QtWidgets.QLineEdit()
        self.cdb_edit = QtWidgets.QLineEdit()

        self.layout = QtWidgets.QVBoxLayout(self)

        #self.setlayout(self.layout)

        self.initLayout()

        #for i in (self.text, self.tab_widget):
        self.layout.addWidget(self.var_form)

        self.layout.addSpacing(600)

        self.reset_button.clicked.connect(self.reset_data)
        self.cancel_button.clicked.connect(self.cancel)
        self.save_button.clicked.connect(self.save_data)
        self.fileOpenButton.clicked.connect(self.choose_bin)
        self.fileOpenButton1.clicked.connect(self.choose_mmdb)
        self.combobox1.activated.connect(self.enable_path)

        self.load_data()
        if not main.flatpak_check():
            self.combobox1.model().item(0).setEnabled(False)
            self.combobox1.setCurrentIndex(1)

        if self.results[0][1] == "flatpak run org.srb2.SRB2":
            self.combobox1.setCurrentIndex(0)
            self.bin_edit.setEnabled(False)
            self.fileOpenButton.setEnabled(False)
            self.bin_label.setEnabled(False)
            self.dir_edit.setEnabled(False)
            self.fileOpenButton2.setEnabled(False)
            self.dir_label.setEnabled(False)
        else:
            self.combobox1.setCurrentIndex(1)

    @QtCore.Slot()
    def initLayout(self):

        self.h_layout0 = QtWidgets.QHBoxLayout()
        self.h_layout0.addWidget(self.text1)
        self.h_layout0.addWidget(self.combobox1)
        self.h_layout0.addSpacing(600)

        self.h_layout1 = QtWidgets.QHBoxLayout()
        self.h_layout1.addWidget(self.bin_label)
        self.h_layout1.addWidget(self.bin_edit)
        self.h_layout1.addWidget(self.fileOpenButton)

        self.h_layout1_2 = QtWidgets.QHBoxLayout()
        self.h_layout1_2.addWidget(self.dir_label)
        self.h_layout1_2.addWidget(self.dir_edit)
        self.h_layout1_2.addWidget(self.fileOpenButton2)

        self.h_layout2 = QtWidgets.QHBoxLayout()
        self.h_layout2.addWidget(self.json_label)
        self.h_layout2.addWidget(self.json_edit)

        self.h_layout3 = QtWidgets.QHBoxLayout()
        self.h_layout3.addWidget(self.ua_label)
        self.h_layout3.addWidget(self.ua_edit)

        self.h_layout4 = QtWidgets.QHBoxLayout()
        self.h_layout4.addWidget(self.cdb_label)
        self.h_layout4.addWidget(self.cdb_edit)
        self.h_layout4.addWidget(self.fileOpenButton1)

        self.h_layout5 = QtWidgets.QHBoxLayout()
        self.h_layout5.addWidget(self.reset_button)
        self.h_layout5.addSpacing(600)
        self.h_layout5.addWidget(self.cancel_button)
        self.h_layout5.addWidget(self.save_button)

        self.var_form = QtWidgets.QGroupBox("Set variables")
        self.layout_2 = QtWidgets.QVBoxLayout()
        self.layout_2.addLayout(self.h_layout0)
        self.layout_2.addLayout(self.h_layout1)
        self.layout_2.addLayout(self.h_layout1_2)
        self.layout_2.addLayout(self.h_layout2)
        self.layout_2.addLayout(self.h_layout3)
        self.layout_2.addLayout(self.h_layout4)
        self.layout_2.addLayout(self.h_layout5)
        self.var_form.setLayout(self.layout_2)

    @QtCore.Slot()
    def ref_list(self):
        pass

    @QtCore.Slot()
    def enable_path(self, index):
        match index:
            case 0:
                self.bin_edit.setEnabled(False)
                self.fileOpenButton.setEnabled(False)
                self.bin_label.setEnabled(False)
                self.bin_edit.setText("flatpak run org.srb2.SRB2")
                self.dir_edit.setEnabled(False)
                self.fileOpenButton2.setEnabled(False)
                self.dir_label.setEnabled(False)
                self.dir_edit.setText(self.flatpak_local_dir)
            case 1:
                self.bin_label.setEnabled(True)
                self.bin_edit.setEnabled(True)
                self.fileOpenButton.setEnabled(True)
                self.dir_edit.setEnabled(True)
                self.fileOpenButton2.setEnabled(True)
                self.dir_label.setEnabled(True)
                if self.results[0][1] == "flatpak run org.srb2.SRB2":
                    self.bin_edit.clear()
                    self.dir_edit.clear()
                else:
                    self.bin_edit.setText(self.results[0][1])
                    self.dir_edit.setText(self.results[1][1])
                
        #print(index)

    @QtCore.Slot()
    def cancel(self):
        sys.exit(app.exec())

    @QtCore.Slot()
    def choose_bin(self):
        filename = QtWidgets.QFileDialog.getOpenFileName(self, \
            str("Select SRB2 binary"), "/usr/bin", str("Binary Files (*)"))
        if filename[0]:
            self.bin_edit.setText(filename[0])

    def warn(self, msg):
        Warning = QtWidgets.QMessageBox.warning(self, 'Warning', msg)

    @QtCore.Slot()
    def choose_mmdb(self):
        filename = QtWidgets.QFileDialog.getOpenFileName(self, \
            str("Select MMDB file"), f"/home/{os.environ.get('USER')}", str("MMDB Files (*.mmdb)"))
        if filename[0]:
            self.cdb_edit.setText(filename[0])

    @QtCore.Slot()
    def reset_data(self):
        self.cursor = self.create_connection().cursor()

        try:
            self.cursor.execute("drop table var_list")
        except:
            pass
        
        self.cursor.execute("create table var_list (Name text, Value text)")

        if main.flatpak_check():
            bin_dir = "flatpak run org.srb2.SRB2"
            srb2_dir = self.flatpak_local_dir
        elif main.native_check():
            bin_dir = "/usr/bin/srb2"
            srb2_dir = self.native_local_dir
        else:
            bin_dir = ""
            srb2_dir = ""
        
        self.Var_list = [
            ("binpath", f"{bin_dir}"),
            ("dir", f"{srb2_dir}"),
            ("json", "https://ms.srb2.org/list.json"),
            ("ua", "Sonic Robo Blast 2/v2.2.13"),
            ("cdb", "dbip-country-lite-2024-10.mmdb"),
        ]

        self.cursor.executemany("Insert into var_list values (?,?)", self.Var_list)

        self.connection.commit()
        self.connection.close

        self.load_data()

    @QtCore.Slot()
    def load_data(self):
        self.cursor = self.create_connection().cursor()
        rowCount_sqlquery = "SELECT COUNT(*) FROM var_list"
        vars_sqlquery = "SELECT * FROM var_list"

        try:
            self.cursor.execute(vars_sqlquery)
        except:
            main.silent_remove(f'{(self.local_path)}/selenite.db')
            self.reset_data()
            self.cursor.execute(vars_sqlquery)

        self.results = self.cursor.fetchall()

        #results = [item[1] for item in results]
        colcnt = len(self.results[0])
        rowcnt = len(self.results)

        print(self.results)

        self.bin_edit.setText(self.results[0][1])
        self.dir_edit.setText(self.results[1][1])
        self.json_edit.setText(self.results[2][1])
        self.ua_edit.setText(self.results[3][1])
        self.cdb_edit.setText(self.results[4][1])
        #i.setText(str(results[j][0]))

    @QtCore.Slot()
    def save_data(self):
        self.cursor = self.create_connection().cursor()

        params = [
            (self.bin_edit.text(), 'binpath'),
            (self.dir_edit.text(), 'dir'),
            (self.json_edit.text(), 'json'),
            (self.ua_edit.text(), 'ua'),
            (self.cdb_edit.text(), 'cdb'),
        ]

        for i in enumerate(params):
            self.cursor.executemany(f"UPDATE var_list SET Value = ? WHERE Name = ?", params)
        self.connection.commit()
        self.connection.close
    
    @QtCore.Slot()
    def create_connection(self):
        self.connection = sqlite3.connect(f"{(self.local_path)}/selenite.db")
        return self.connection

if __name__ == "__main__":
    app = QtWidgets.QApplication([])

    widget = SettingsWindow()
    #widget.resize(900, 600)
    widget.show()

    sys.exit(app.exec())