"""
Contains the style data to style the Qt app in our Roam style.
NOTE: This module might need some tweaks in future to make it a bit easier to
      understand and better
"""
from qgis.PyQt.QtWidgets import QDesktopWidget
from string import Template


# TODO Look at better widget scaling for Qt5 for high DPI screen
# https://doc.qt.io/qt-5/highdpi.html

def screen_szie():
    widget = QDesktopWidget()
    rec = widget.availableGeometry(widget.primaryScreen())
    return rec.width(), rec.height()


def font():
    width, height = screen_szie()
    if width == 1024 and height == 728:
        return 'font: 9pt "Segoe UI" ;'
    else:
        return 'font: 14pt "Segoe UI" ;'


def iconsize():
    iconsize = 48
    width, height = screen_szie()
    if width == 1024 and height == 728:
        iconsize = 24
    return iconsize


def appstyle():
    return Template("""
    * {

        $FONT
    }
    
    QToolButton#discard {
        qproperty-icon: url(":/widgets/cancel");
        background-color: rgb(255, 134, 125);
        color: white;
        font: 75 17pt "Segoe UI";
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
        $FONT
    }
    
    QTreeView::item {
        margin-left: 0px;
        margin-top: 5px;
        margin-bottom: 5px;
    }
    
    QListView::item {
        margin-left: 0px;
        margin-top: 10px;
        margin-bottom: 10px;
    }

    QTreeView::indicator {
        width: 30px;
        height: 30px;
    }
    
    QTreeView::indicator:checked {
        image: url(:/icons/resources/images/qcheckbox-checked.svg);
    }
    
    QTreeView::indicator:unchecked {
        image: url(:/icons/resources/images/qcheckbox-unchecked.svg);
    }

    QStatusBar::item {
        border: none;
    }

    QCheckBox {
        color: #4f4f4f;
    }
    
    QCheckBox::indicator, QRadioButton::indicator, QListView::indicator {
        width: 40px;
        height: 40px;
    }
    
    QListView::indicator:checked {
        image: url(:/icons/resources/images/qcheckbox-checked.svg);
    }
    
    QListView::indicator:unchecked {
        image: url(:/icons/resources/images/qcheckbox-unchecked.svg);
    }
    
    QCheckBox::indicator:checked {
        image: url(:/icons/resources/images/qcheckbox-checked.svg);
    }
    
    QCheckBox::indicator:unchecked {
        image: url(:/icons/resources/images/qcheckbox-unchecked.svg);
    }
    
    QRadioButton::indicator:checked {
        image: url(:/icons/resources/images/qradio-checked.svg);
    }
    
    QRadioButton::indicator:unchecked {
        image: url(:/icons/resources/images/qradio-unchecked.svg);
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

    /* INFO */
    QFrame[level="0"] {
        border: 5px solid #b9cfe4;
    }

    /* WARNING */
    QFrame[level="1"] {
        border: 5px solid #e0aa00;
    }

    /* CRITICAL */
    QFrame[level="2"] {
        border: 5px solid #9b3d3d;
    }

    /* SUCCESS */
    QFrame[level="3"] {
        border: 5px solid green;
    }

    QFrame#infoframe {
        background-color: rgb(255,255,255, 220);
    }

    QListWidget:item:hover {
        background-color: #5b93c2;
    }

    QListView#layerList {
    }
    
    QListView#layerList::item:hover {
        color: white;
        background-color: #5b93c2;
    }
    
    QListView#layerList::item:selected {
        color: white;
        background-color: #5b93c2;
    }

    QListWidget[large="true"]::item {
        font: 12pt "Segoe UI";
        padding: 8px;
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

    QScrollBar:vertical {
        border: 2px solid grey;
        background: rgba(80, 80, 80, 20);
        width: 40px;
        margin: 22px 0 22px 0;
    }
    QScrollBar::handle:vertical {
        background: #678fb2;
        min-height: 20px;
    }
    QScrollBar::add-line:vertical {
        border: 2px solid grey;
        
        background: rgba(80, 80, 80, 20);
        height: 20px;
        subcontrol-position: bottom;
        subcontrol-origin: margin;
    }

    QScrollBar::sub-line:vertical {
        border: 2px solid grey;
        background: rgba(80, 80, 80, 20);
        height: 20px;
        subcontrol-position: top;
        subcontrol-origin: margin;
    }

    QTabWidget {
        border: none;
    }


    /* Style the tab using the tab sub-control. Note that
        it reads QTabBar _not_ QTabWidget */
    QTabBar::tab {
        background: white;
        border: 2px solid #C4C4C3;
        border-bottom-color: #C2C7CB; /* same as the pane color */
        padding: 2ex;
    }

    QTabBar::tab:selected, QTabBar::tab:hover {
        background: #5B93C2;
        color: white;
    }

    QTabBar::tab:selected {
        border-color: #5B93C2;
        border-bottom-color: #C2C7CB; /* same as pane color */
    }

    QTabBar::tab:!selected {
        margin-top: 2ex; /* make non-selected tabs look smaller */
    }

    """).substitute(FONT=font())


def menubarstyle():
    return Template("""
    QToolBar#menutoolbar {
        $FONT
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
    """).substitute(FONT=font())


def featureform():
    return Template("""
    * {
        $FONT 
    }

    QLabel[projectlabel="true"] {
        background-color: rgba(255, 255, 255, 0);
    }

    QLabel[headerlabel="true"] {
        $FONT
    }

    QHeaderView {
    }

    QHeaderView::section {
        background: 1px solid rgb(137, 175, 255);
        background-color: rgb(203, 203, 203, 50);
        color: #777;
        border: 1px solid rgb(137, 175, 255);
        padding: 0 0 2px 3px
    }

    QPushButton {
        border: 1px solid rgb(137, 175, 255);
        background-color: rgb(203, 203, 203, 50);
        padding: 6px;
        color: #4f4f4f;
    }

    QTabWidget {
        border: none;
    }


    /* Style the tab using the tab sub-control. Note that
        it reads QTabBar _not_ QTabWidget */
    QTabBar::tab {
        background: white;
        border: 2px solid #C4C4C3;
        border-bottom-color: #C2C7CB; /* same as the pane color */
        padding: 2ex;
    }

    QTabBar::tab:selected, QTabBar::tab:hover {
        background: #5B93C2;
        color: white;
    }

    QTabBar::tab:selected {
        border-color: #5B93C2;
        border-bottom-color: #C2C7CB; /* same as pane color */
    }

    QTabBar::tab:!selected {
        margin-top: 2ex; /* make non-selected tabs look smaller */
    }

    QScrollBar:vertical {
        border: 2px solid grey;
        background: rgba(80, 80, 80, 20);
        width: 40px;
        margin: 22px 0 22px 0;
    }
    QScrollBar::handle:vertical {
        background: #678fb2;
        min-height: 20px;
    }
    QScrollBar::add-line:vertical {
        border: 2px solid grey;
        background: rgba(80, 80, 80, 20);
        height: 20px;
        subcontrol-position: bottom;
        subcontrol-origin: margin;
    }

    QScrollBar::sub-line:vertical {
        border: 2px solid grey;
        background: rgba(80, 80, 80, 20);
        height: 20px;
        subcontrol-position: top;
        subcontrol-origin: margin;
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
    """).substitute(FONT=font())
