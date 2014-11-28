appstyle = """
* {
    font: 14pt "Segoe UI" ;
}

QToolButton {
    padding: 4px;
    color: #4f4f4f;
 }

QToolButton:hover {
    padding: 4px;
    background-color: rgb(211, 228, 255);
 }

QStatusBar {
    background: white;
    border: none;
}

QStatusBar::item {
            border: none;
}

QCheckBox {
    color: #4f4f4f;
}

QCheckBox::indicator {
     width: 40px;
     height: 40px;
 }

QLabel {
    color: #4f4f4f;
}

QLabel[projectlabel="true"] {
    background-color: rgba(255, 255, 255, 0);
}

QLabel[headerlabel="true"] {
	font: 75 17pt "Segoe UI";
}

QComboBox {
    border: 1px solid #d3d3d3;
}

QComboBox::drop-down {
    width: 30px;
}

QWidget QStackedWidget {
	background-color: white;
}

QScollArea, QScollArea * {
	background-color: white;
}

QFrame {
    background-color: rgb(255,255,255);
}


QFrame#infoframe {
    background-color: rgb(255,255,255, 220);
}

QListWidget:item:hover {
    background-color: #5b93c2;
}

QListWidget#layerList {
    font: 12pt "Segoe UI";
    background-color: rgb(149,150,145, 220);
}

QListWidget#layerList::item {
	color: white;
    border-bottom: 1px solid black;
	padding: 4px;
}

QListWidget[large="true"]::item {
    font: 12pt "Segoe UI";
	padding: 8px;
}

QListWidget#layerList::item::selected {
    background-color: #5b93c2;
}

QPushButton {
    border: 1px solid #e1e1e1;
    padding: 6px;
    color: #4f4f4f;
}

QPushButton:checked  {
    border: 3px solid rgb(137, 175, 255);
    background-color: rgb(211, 228, 255);
}

QPushButton:hover {
    background-color: rgb(211, 228, 255);
 }

QToolButton[action="true"] {
    border: 1px solid #e1e1e1;
    padding: 6px;
    color: #4f4f4f;
}

QWidget#featureformarea {
    background-color: white;
}

QWidget#helpframe {
	font: 20px "Segoe UI" ;
    background-color: rgb(255,255,255, 220);
}

QDialog {
	color: #4f4f4f;
	font: 12pt "Segoe UI" ;
    background-color: rgb(255, 255, 255);
}

QPushButton#deleteButton {
	background-color: rgb(255, 134, 125);
    color: white;
	font: 75 17pt "Segoe UI";
}

QLabel#headerlabel {
	color: rgb(255, 134, 125);
	font: 75 17pt "Segoe UI";
}

QTreeWidget#synctree {
	font: 20pt "Segoe UI";
}

QTreeWidget#synctree::item {
    padding-top: 4px;
}
"""

menubarstyle = """
QToolBar#menutoolbar {
    font: 14px "Segoe UI" ;
	background-color: rgb(85,85,85);
    padding: 0px;
}

QToolButton {
	color: rgb(221,221,219);
}

QToolButton:hover {
	color: rgb(0,0,0);
}

QToolButton:checked {
	color: rgb(91,147,194);
	padding-right: 0px;
	background-color: rgb(240, 240, 240);
}
"""

featureform = """
* {
    font: 14pt "Segoe UI" ;
}

QPushButton {
    border: 1px solid rgb(137, 175, 255);
	background-color: rgb(203, 203, 203, 50);
    padding: 6px;
    color: #4f4f4f;
}

QPushButton:checked  {
    border: 3px solid rgb(137, 175, 255);
    background-color: rgb(211, 228, 255);
}

QPushButton:hover {
    background-color: rgb(211, 228, 255);
}

QToolButton {
    border: 1px solid #e1e1e1;
    padding: 6px;
    color: #4f4f4f;
}

QToolButton:checked  {
    border: 3px solid rgb(137, 175, 255);
    background-color: rgb(211, 228, 255);
}
"""

