import os
import sys
import requests
import urllib.request
import re
import maxminddb
import ipaddress
from time import sleep
from datetime import datetime
from PySide6 import QtCore, QtWidgets, QtGui
import settings
import sqlite3
import files
import players
import subprocess
#import database

class MainWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.local_path = os.path.join(
            os.environ.get("XDG_DATA_HOME") or f'{ os.environ["HOME"] }/.local/share',
            "selenite",
        )

        if not os.path.exists(self.local_path):  # Creates $HOME/.local/share/selenite
            os.mkdir(self.local_path)

        self.setWindowTitle("Selenite Launcher")

        self.load_data()

        self.online = True
        self.pull_server_list()
        if self.online:
            self.create_tablewidget()

        # -----------------------------------

        self.toolbar = QtWidgets.QToolBar()
        self.toolbar.setIconSize(QtCore.QSize(32, 32))
        self.toolbar.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)

        tb_items = [("join", "join", "&Join by IP", self.ip_join, "Ctrl+j"),
                    ("settings", "gear", "&Settings", self.settings, "Ctrl+p")]

        for i, (name, icon, label, action, shortcut) in enumerate(tb_items):
            name = QtGui.QAction(QtGui.QIcon(f"icons/{icon}.svg"), label, self)
            name.triggered.connect(action)
            name.setShortcut(QtGui.QKeySequence(shortcut))
            self.toolbar.addAction(name)
        
        # -----------------------------------

        self.tab_widget = QtWidgets.QTabWidget()
        self.tab1 = QtWidgets.QWidget()
        self.tab2 = QtWidgets.QWidget()
        self.tab3 = QtWidgets.QWidget()
        self.tab4 = QtWidgets.QWidget()

        self.tab_widget.addTab(self.tab1, "All servers")
        self.tab_widget.addTab(self.tab2, "Recent")
        self.tab_widget.addTab(self.tab3, "Favorite")
        self.tab_widget.addTab(self.tab4, "Blocklist")

        self.text = QtWidgets.QLabel(f"{(sum(len(p) for p in self.players_list))} players on {(len(self.dict_list))} servers", alignment=QtCore.Qt.AlignCenter)

        #self.files_2_download_text = QtWidgets.QLabel(f"{(sum(len(p) for p in self.files_list))} files to download", alignment=QtCore.Qt.AlignCenter)
        
        self.ref_button = QtWidgets.QPushButton("Refresh")

        self.join_button = QtWidgets.QPushButton("Join")

        self.layout = QtWidgets.QVBoxLayout(self)

        if self.online:
            self.initTab1()
            self.initTab2()
            self.initTab3()
            self.initTab4()

        for i in (self.toolbar, self.tab_widget, self.text, self.ref_button, self.join_button):
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
                    ("bl", "block", "&Block", self.settings, "Ctrl+b"),
                    ("pl", "human", "&Players", self.players, "Ctrl+Shift+s"),
                    ("fl", "file", "&Files", self.files, "Ctrl+Shift+f")]

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
    def initTab1(self):
        self.layout_all = QtWidgets.QVBoxLayout(self.tab1)
        self.layout_all.addWidget(self.tablewidget)

    @QtCore.Slot()
    def initTab2(self):
        self.layout_2 = QtWidgets.QVBoxLayout(self.tab2)
        label = QtWidgets.QLabel("TBD")
        self.layout_2.addWidget(label)
    
    @QtCore.Slot()
    def initTab3(self):
        self.layout_3 = QtWidgets.QVBoxLayout(self.tab3)
        label = QtWidgets.QLabel("TBD")
        self.layout_3.addWidget(label)

    @QtCore.Slot()
    def initTab4(self):
        self.layout_4 = QtWidgets.QVBoxLayout(self.tab4)
        label11 = QtWidgets.QLabel("TBD")
        self.layout_4.addWidget(label11)

    @QtCore.Slot()
    def files(self):

        cur_files_list = []

        cur_files_list = self.files_list[self.tablewidget.currentRow()]

        try:
            for item in cur_files_list:
                for key in list(item):
                    match key:
                        case 'size':
                            if int(item[key]) >= 1024 * 1024:
                                item[key] = f"{round((int(item[key]) / 1024 ** 2), 1)} MiB"
                            else:
                                item[key] = f"{round((int(item[key]) / 1024), 1)} KiB"
                        case 'name':
                            if os.path.isfile(f'{self.srb2dir}/DOWNLOAD/{item[key]}'):
                                item['installed'] = "True"
                            else:
                                item['installed'] = "False"
                            item[key] = str(item[key])
                        case _:
                            item[key] = str(item[key])


            #print(self.files_list)
            #print(self.players_list)

            # this is stupid
            tuples_list = []
            workaround_list = []
            for d in cur_files_list:
                workaround_list.extend(d.values())  

            tuples_list = [tuple(workaround_list[i:i + 6]) for i in range(0, len(workaround_list), 6)] 
            self.widget = files.FilesWindow(tuples_list)
            self.widget.resize(900, 600)
            self.widget.show()

        except IndexError:
            self.warn("This is a vanilla server. There are no files.")

        self.tablewidget.clearSelection()

    @QtCore.Slot()
    def players(self):

        cur_players_list = []
        flattened_data = []

        cur_players_list = self.players_list[self.tablewidget.currentRow()]

        try:
            for entry in cur_players_list:
                flat_entry = entry.copy()
                if 'flags' in flat_entry and isinstance(flat_entry['flags'], dict):
                    flat_entry.update(flat_entry['flags'])
                    del flat_entry['flags']
                flattened_data.append(flat_entry)

            cur_players_list = flattened_data

            for item in cur_players_list:
                for key in list(item):
                    match key:
                        case 'time':
                            total_secs = int(item[key])
                            mins = total_secs // 60
                            secs = total_secs % 60
                            item[key] = f"{mins}:{secs:02d}"
                        case 'flags':
                            for subkey in item[key]:
                                match subkey:
                                    case 'tagged_it':
                                        item[tagged_it] = str(item[subkey])
                                    case 'holding_ctf_flag':
                                        item[holding_ctf_flag] = str(item[subkey])
                                    case  'is_super':
                                        item [is_super] = str(item[is_super])
                        case _:
                            item[key] = str(item[key])

            for item in cur_players_list:
                for key in list(item):
                    item.pop('flags', None)

            print(cur_players_list)

            #print(self.files_list)
            #print(self.players_list)

            # this is stupid
            tuples_list = []
            workaround_list = []
            for d in cur_players_list:
                workaround_list.extend(d.values())

            tuples_list = [tuple(workaround_list[i:i + 8]) for i in range(0, len(workaround_list), 8)] 
            self.widget = players.PlayersWindow(tuples_list)
            self.widget.resize(900, 600)
            self.widget.show()

        except IndexError:
            self.warn("There are no players on this server.")

    @QtCore.Slot()
    def ip_join(self):

        ip = QtWidgets.QInputDialog.getText(self, 'text', 'Enter the IP address')
        if ip[1]:
            port = QtWidgets.QInputDialog.getText(self, 'text', 'Enter the port', QtWidgets.QLineEdit.Normal, '5029')
            if port[1]:
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
        self.text.setText(f"{(sum(len(p) for p in self.players_list))} players on {(len(self.dict_list))} servers")
        #for i in (self.tablewidget):
        #     self.layout_all.addWidget(i)
                
    @QtCore.Slot()
    def join_srb2(self, ip="no", port="no"):
        if "no" in {ip, port}:
            ip = self.cur_row(0)
            print(self.cur_row(0))
            port = self.cur_row(17)
            print(self.cur_row(17))
        #srb2 = 'flatpak run org.srb2.SRB2'
        self.p = QtCore.QProcess()
        print("flatpak", ["run", "org.srb2.SRB2", "-connect", f"{ip}:{port}"])
        self.p.start("flatpak", ["run", "org.srb2.SRB2", "-connect", f"{ip}:{port}"])
        sleep(1)
        sys.exit(app.exec())

    @QtCore.Slot()
    def cur_row(self, row):
        return self.tuples_list[self.tablewidget.currentRow()][row]

    @QtCore.Slot()
    def warn(self, msg):
        Warning = QtWidgets.QMessageBox.warning(self, 'Warning', msg)
    
    @QtCore.Slot()
    def create_tablewidget(self):
        
        colcnt = len(self.tuples_list[0])
        rowcnt = len(self.dict_list)

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
        self.tablewidget.setHorizontalHeaderLabels(["Address", "Room", "Version", "Players", "Max players", "Can join", \
            "Gametype", "Modified", "Cheats", "Map time", "Name", "Map lump",\
                "Map MD5", "HTTP Source", "Dedicated", "Map title", "Bots", "Port", "Country"])

        #print(len(self.tuples_list[0]))
        #print(len(self.dict_list))
        for i, (address, room, version, num_humans, max_connections, \
            joinable_state, gametype, modified, cheats, map_time, server_name, \
                map_lump, map_md5, http_source, dedicated, map_title, num_bots, port, country) in enumerate(self.tuples_list):
                for j in range(colcnt):
                    item = QtWidgets.QTableWidgetItem(self.tuples_list[i][j])
                    self.tablewidget.setItem(i, j, item)

        self.tablewidget.setIconSize(QtCore.QSize(24, 24))
        self.tablewidget.installEventFilter(self)
        #self.tablewidget.horizontalHeader().setSortIndicator(10, QtCore.Qt.SortOrder.AscendingOrder)
        #self.tablewidget.setSortingEnabled(True)
        self.tablewidget.hideColumn(1)
    
    @QtCore.Slot()
    def pull_server_list(self):
        
        session = requests.Session()
        session.headers.update(self.useragent)
            
        self.dict_list = []
        self.files_list = []
        self.players_list = []

        # retrieving data from JSON Data
        try:
            response = session.get(self.baseUrl)
            if response.status_code == 200:
                data = response.json()

                self.dict_list.append(data["servers"])

                self.dict_list = self.dict_list[0]

                self.dict_list = [item for item in self.dict_list if 'error' not in item]

                print(self.dict_list)

                self.files_list = [item['files'] for item in self.dict_list if 'files' in item]
                self.players_list = [item['players'] for item in self.dict_list if 'players' in item]
                
                for item in self.dict_list:
                    # Separate port and address info
                    item['port'] = item['address'][1]
                    item['address'] = item['address'][0]
                    for x in ('files', 'players'):
                        item.pop(x, None)
                    for key in list(item):
                        match key:
                            case 'map_time':
                                total_secs = int(item[key])
                                mins = total_secs // 60
                                secs = total_secs % 60
                                item[key] = f"{mins}:{secs:02d}"
                            case 'server_name':
                                item[key] = re.sub(r'\^[0-9A-F]','',item[key])
                            case 'address':
                                with maxminddb.open_database(self.country_db) as reader:
                                    request = reader.get(item[key])
                                    country = []
                                    country.append(request["country"])
                                    for iso in country:
                                        item['country'] = QtWidgets.QTableWidgetItem(QtGui.QIcon(f"flags/{iso['iso_code']}.png"),None)
                                        #print(item['country'])
                            case 'room':
                                match item[key]:
                                    case 33:
                                        item[key] = "Standard"
                                    case 28:
                                        item[key] = "Casual"
                                    case 38:
                                        item[key] = "Custom"
                                    case 31:
                                        item[key] = "OLDC"
                            case _:
                                item[key] = str(item[key])

                #print(self.files_list)
                #print(self.players_list)

                # this is stupid
                self.tuples_list = []
                workaround_list = []
                for d in self.dict_list:
                    workaround_list.extend(d.values())

                self.tuples_list = [tuple(workaround_list[i:i + 19]) for i in range(0, len(workaround_list), 19)]               
            else:
                self.warn("Selenite Launcher can't connect to the Master Server.\nSome features may not be available.")
                self.online = False
        except:
            self.warn("Selenite Launcher can't connect to the Internet.\nSome features may not be available.")
            self.online = False

        #for i, d in enumerate(self.dict_list):
            # Get all items, move the last item to the beginning
        #    items = list(d.items())
        #    reordered_items = [items[-1]] + items[:-1]
            # Update dictionary in the list with reordered items
        #    data[i] = dict(reordered_items)
        #self.dict_list = reordered_items
        #print(self.dict_list)
    
    @QtCore.Slot()
    def create_connection(self):
        self.connection = sqlite3.connect(f"{(self.local_path)}/selenite.db")
        return self.connection

    @QtCore.Slot()
    def check_db_values(self):
        pass

    @QtCore.Slot()
    def load_data(self):
        self.cursor = self.create_connection().cursor()
        rowCount_sqlquery = "SELECT COUNT(*) FROM var_list"
        vars_sqlquery = "SELECT * FROM var_list"

        try:
            self.cursor.execute(vars_sqlquery)
        except:
            silent_remove(f'{(self.local_path)}/selenite.db')
            self.reset_data()
            self.cursor.execute(vars_sqlquery)
            
        self.results = self.cursor.fetchall()

        #results = [item[1] for item in results]
        colcnt = len(self.results[0])
        rowcnt = len(self.results)

        self.srb2dir = self.results[1][1]

        #print(self.results[1][1])

        # setting the base URL value
        self.baseUrl = self.results[2][1]

        self.useragent = {
            'User-Agent': self.results[3][1]
        }   

        self.country_db = self.results[4][1]

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

        if bin_dir == "":
            pass
        else:
            ver_cmd = bin_dir + " -dedicated +version +quit 2>&1 | grep -oP 'Sonic Robo Blast 2 v\\K[0-9]+\\.[0-9]+\\.[0-9]+'"
            ver_str = (subprocess.check_output(ver_cmd, shell=True, text=True)).strip()
        
        self.p.start("flatpak", ["run", "org.srb2.SRB2", "-connect", f"{ip}:{port}"])
        
        self.Var_list = [
            ("binpath", f"{bin_dir}"),
            ("dir", f"{srb2_dir}"),
            ("json", "https://ms.srb2.org/list.json"),
            ("ua", f"Sonic Robo Blast 2/v{ver_str}"),
            ("cdb", "dbip-country-lite-2024-10.mmdb"),
        ]

        self.cursor.executemany("Insert into var_list values (?,?)", self.Var_list)

        self.connection.commit()
        self.connection.close

def flatpak_check():
    if os.path.isdir('/var/lib/flatpak/app/org.srb2.SRB2'):
        return True
    else:
        return False

def native_check():
    if os.path.isfile('/usr/bin/srb2'):
        return True
    else:
        return False

def silent_remove(filename):
    try:
        os.remove(filename)
    except OSError as e:
        if e.errno != errno.ENOENT:  # errno.ENOENT = no such file or directory
            raise  # re-raise exception if a different error occurred

if __name__ == "__main__":
    app = QtWidgets.QApplication([])

    widget = MainWindow()
    widget.resize(900, 600)
    widget.show()

    sys.exit(app.exec())