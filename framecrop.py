import sys
import os
import rawpy
import imageio

from PyQt5 import QtCore, QtGui, QtWidgets
import numpy as np

import cv2

class OnlyInt(QtGui.QIntValidator):
    def __init__(self):
        super().__init__()
    def setup(self):
        self.setRange(0, 999999)
        return self

class LeftToolBox(QtWidgets.QVBoxLayout):
    def __init__(self):
        self.idx = 0
        self.len = 0
        super().__init__()

    def updateIdx(self, i, n):
        self.idx = i
        self.len = n
        self.imgidxtext.setText(str(self.idx+1) + " / " + str(self.len))
    
    def setupUI(self):
        self.setObjectName("leftform")
        self.setGeometry(QtCore.QRect(0, 0, 250, 600))

        self.settings = QtWidgets.QFormLayout()
        self.settings.setAlignment(QtCore.Qt.AlignTop)

        self.outwidth = QtWidgets.QLineEdit()
        self.outwidth.setValidator(OnlyInt.setup(OnlyInt()))
        self.outwidth.setText("640")
        self.settings.addRow("Width: ", self.outwidth)
        self.outheight = QtWidgets.QLineEdit()
        self.outheight.setValidator(OnlyInt.setup(OnlyInt()))
        self.outheight.setText("480")
        self.settings.addRow("Height:",self.outheight)

        self.nav = QtWidgets.QFormLayout()
        self.nav.setAlignment(QtCore.Qt.AlignTop)

        self.imgidxtext = QtWidgets.QLabel()
        self.imgidxtext.setText(str(self.idx) + " / " + str(self.len))
        self.nav.addRow(self.imgidxtext)

        self.sliderLabel = QtWidgets.QLabel()
        self.sliderLabel.setText("Image Zoom")
        self.nav.addRow(self.sliderLabel)
        self.slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.slider.setPageStep(0)
        self.slider.setMinimum(0)
        self.slider.setMaximum(200)
        self.slider.setValue(1)
        self.slider.setTickPosition(QtWidgets.QSlider.TicksBelow)
        self.slider.setTickInterval(25)
        self.nav.addRow(self.slider)

        self.prev = QtWidgets.QPushButton()
        self.prev.setText("Prev")
        self.next = QtWidgets.QPushButton()
        self.next.setText("Next")
        self.nav.addRow(self.prev, self.next)
        self.resetCrop = QtWidgets.QPushButton()
        self.resetCrop.setText("Reset Crop")
        self.checkClickNext = QtWidgets.QCheckBox()
        self.checkClickNext.setText("Click -> Next")
        self.checkClickNext.setCheckState(2)
        self.nav.addRow(self.resetCrop, self.checkClickNext)

        self.gallery = QtWidgets.QFormLayout()
        self.nav.setAlignment(QtCore.Qt.AlignTop)

        self.addLayout(self.settings,0)
        self.addLayout(self.nav, 0)
        self.addLayout(self.gallery, 0)
        self.addStretch(1)

class PhotoWidget(QtWidgets.QLabel):

    def __init__(self):
        self.pixmapImg = 0
        self.pixmapShow = 0
        self.baserect = 0
        self.cropscale = 1.0
        self.ratio = 1.0

        self.pMME = 0
        self.pMPE = 0
        self.pMWE = 0

        super().__init__()

    def resetCropscale(self):
        self.cropscale = 1.0

    def redisplayPixmap(self, pmap):
        self.setPixmap(pmap)
        self.pixmapShow = pmap

    def displayPixmap(self, pixmap):
        # using filepath scale image to window size and display it, record ratio of scaling
        self.pixmapImg = pixmap.copy()
        newPixmapShow = self.pixmapImg.copy()
        newPixmapShow = newPixmapShow.scaled (self.width(), self.height(), QtCore.Qt.KeepAspectRatio)
        self.ratio = newPixmapShow.width() / self.pixmapImg.width()
        self.redisplayPixmap(newPixmapShow)

    def updateCropBox(self, bw, bh, color = QtGui.QColor("green")):
        # add cropping box to photo, photo is scaled to recorded ratio
        if (self.pixmapImg):
            pixmapNew = self.pixmapImg.copy()
            if pixmapNew:
                painter = QtGui.QPainter(pixmapNew)

                # draw base resolution box
                painter.setPen(QtGui.QPen(QtGui.QColor("grey"), 5.0, QtCore.Qt.PenStyle.DashDotLine))
                self.baserect = QtCore.QRect(0, 0, int(bw), int(bh))
                curpos = QtGui.QCursor.pos()
                transcurpos = self.mapFromGlobal(curpos) / self.ratio
                scaledrect = QtCore.QRect(self.baserect.topLeft(), self.baserect.bottomRight())
                scaledrect.moveCenter(transcurpos)
                painter.drawRect(scaledrect)
                
                # draw crop bound box
                painter.setPen(QtGui.QPen(color, 10.0, QtCore.Qt.PenStyle.DashLine))
                self.baserect = QtCore.QRect(0, 0, int(bw), int(bh))
                scaledrect = QtCore.QRect(self.baserect.topLeft()*self.cropscale, self.baserect.bottomRight()*self.cropscale)
                scaledrect.moveCenter(transcurpos)
                painter.drawRect(scaledrect)
                
                # draw crosshair
                painter.setPen(QtGui.QPen(QtGui.QColor("grey"), 5.0, QtCore.Qt.PenStyle.DashDotLine))
                p1 = (scaledrect.topLeft() + scaledrect.bottomLeft())/2
                p2 = (scaledrect.topRight() + scaledrect.bottomRight())/2
                painter.drawLine(p1, p2)
                p1 = (scaledrect.topLeft() + scaledrect.topRight())/2
                p2 = (scaledrect.bottomLeft() + scaledrect.bottomRight())/2
                painter.drawLine(p1, p2)

                self.baserect = scaledrect
                self.pixmapShow = pixmapNew.scaled (round(pixmapNew.width()*self.ratio), round(pixmapNew.height()*self.ratio), QtCore.Qt.KeepAspectRatio)
                painter.end()
            self.redisplayPixmap(self.pixmapShow)

    def saveCrop(self, bw, bh, fn):
        # crop is extracted and resized to dimension then saved
        # TODO: fill mode of extending past borders
        if self.baserect:
            fileName = "out/" + str(fn) + ".png"
            if not os.path.exists("out"):
                os.makedirs("out")

            # copy self.pixmapImg to canvas with border first

            w = self.pixmapImg.rect().width()
            h = self.pixmapImg.rect().height()

            pixmapTrans = QtGui.QPixmap(w*3, h*3)
            pixmapTrans.fill(QtGui.QColor(QtGui.qRgba64(0, 0, 0, 0)))
            targRect = QtCore.QRect(w, h, w, h)

            painter = QtGui.QPainter(pixmapTrans)
            painter.drawPixmap(targRect, self.pixmapImg, self.pixmapImg.rect())
            painter.end()

            newRect = self.baserect
            newRect.moveTopLeft(newRect.topLeft() + QtCore.QPoint(w, h))

            ax, ay = np.max([w, newRect.topLeft().x()]), np.max([h, newRect.topLeft().y()])
            bx, by = np.min([2*w, newRect.bottomRight().x()]), np.min([2*h, newRect.bottomRight().y()])
            nbw, nbh = bx-ax, by-ay
            print (ax-w, ay-h, bx-w, by-h)
            #pixmapCropped = pixmapTrans.copy(newRect)
            pixmapCropped = pixmapTrans.copy(ax, ay, nbw, nbh)
            # pixmapCropped = pixmapCropped.scaled(bw, bh) # TODO better scaling?
            pixmapCropped.save(fileName, "PNG")

            # reopen file to scale with opencv
            img = cv2.imread(fileName)
            resized = cv2.resize(img, (nbw, nbh))
            cv2.imwrite(fileName, resized)

    def setMousePressEvent(self, newpMPE):
        self.pMPE = newpMPE

    def mousePressEvent(self, event):
        curpos = self.mapFromGlobal(QtGui.QCursor.pos())
        if self.pixmapShow and self.pixmapShow.rect().intersects(QtCore.QRect(curpos, curpos)):
            if (self.pMPE):
                self.pMPE(event)
        return super().mousePressEvent(event)
    
    def setMouseMoveEvent(self, newpMME):
        self.pMME = newpMME
    
    def mouseMoveEvent(self, event):
        if self.pMME:
            self.pMME(event)
        return super().mouseMoveEvent(event)
    
    def setMouseWheelEvent(self, newpMWE):
        self.pMWE = newpMWE
    
    def wheelEvent(self, event):
        if self.pMWE:
            self.pMWE(event)
        return super().wheelEvent(event)

class uiMainWindow(QtCore.QObject):
    curImgIdx = -1

    def __init__(self):
        super(uiMainWindow,self).__init__()
        self.selectedFiles = 0

        self.photo = PhotoWidget()
        self.photo.setGeometry(QtCore.QRect(0, 0, 1250, 900))
        self.photo.setAlignment(QtCore.Qt.AlignTop)
        self.photo.setText("")
        self.photo.setScaledContents(False)
        self.photo.setObjectName("photo")
        self.photo.setMouseTracking(True)
        self.photo.setMouseMoveEvent(self.photoMouseMoveEvent)
        self.photo.setMousePressEvent(self.photoMousePressEvent)
        self.photo.setMouseWheelEvent(self.photoMouseWheelEvent)
    
    def photoMousePressEvent(self, event):
        if event.buttons() == QtCore.Qt.LeftButton:
            self.updateCropBox(QtGui.QColor("red"))
            self.saveCrop()
        elif event.buttons() == QtCore.Qt.RightButton:
            self.nextImg()

    def photoMouseMoveEvent(self, event):
        if event.buttons() == QtCore.Qt.NoButton:
            self.updateCropBox()

    def photoMouseWheelEvent(self, event):
        ControlState = QtWidgets.QApplication.keyboardModifiers() == QtCore.Qt.ControlModifier
        if ControlState == False:
            adj = (event.angleDelta().y() / 120) * 0.1
            self.photo.cropscale += -adj
            self.photo.cropscale = max(1.0, self.photo.cropscale)
            self.updateCropBox()
        elif ControlState == True:
            # TODO: set crop angle
            self.updateCropBox()

    def setStatusLabel(self, text):
        self.statusLabel.setText(text)

    def getPixmapFromIdx(self, idx):
        imgPath = self.selectedFiles[idx]
        pixmapImg = None
        if (len(imgPath) >= 4 and (imgPath[-4:].lower() == ".cr2")):
            # process raw photo to pixmap
            with rawpy.imread(imgPath) as raw:
                nparrRGB = raw.postprocess()
                h, w, c = nparrRGB.shape
                bytesPerLine = 3 * w
                pixmapImg = QtGui.QImage(nparrRGB.data, w, h, bytesPerLine, QtGui.QImage.Format_RGB888)
                pixmapImg = QtGui.QPixmap(pixmapImg)
        else:
            pixmapImg = QtGui.QPixmap(imgPath)
        return pixmapImg

    def displayMainImg(self):
        idx = self.curImgIdx
        if (self.selectedFiles and idx >= 0 and idx <= len(self.selectedFiles)):
            pixmapImg = self.getPixmapFromIdx(idx)
            self.photo.displayPixmap(pixmapImg)
            self.leftForm.slider.setValue(round(self.photo.ratio * 100))

    def resetCropscale(self):
        self.photo.resetCropscale()
        self.updateCropBox()

    def updateCropBox(self, color = QtGui.QColor("green")):
        bw = int(self.leftForm.outwidth.text())
        bh = int(self.leftForm.outheight.text())
        self.photo.updateCropBox(bw, bh, color)

    def saveCrop(self, fn = 0):
        bw = int(self.leftForm.outwidth.text())
        bh = int(self.leftForm.outheight.text())
        if fn == 0:
            fn = self.outname.text()
            self.outname.setText(str(int(self.outname.text())+1))
        self.photo.saveCrop(bw, bh, fn)
        if self.leftForm.checkClickNext.isChecked():
            self.nextImg()
        
    def setupUi(self, MainWindow):
        self.mainWindow = MainWindow
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1600, 1024)

        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        MainWindow.setCentralWidget(self.centralwidget)

        self.centralLayout = QtWidgets.QHBoxLayout(self.centralwidget)
        self.centralLayout.setObjectName("centrallayout")
        self.centralwidget.setLayout(self.centralLayout)

        self.leftForm = LeftToolBox()
        self.leftForm.setupUI()
        self.leftForm.slider.sliderMoved.connect(self.changeZoom)
        self.leftForm.prev.clicked.connect(self.prevImg)
        self.leftForm.next.clicked.connect(self.nextImg)
        self.leftForm.resetCrop.clicked.connect(self.resetCropscale)

        self.centralLayout.addLayout(self.leftForm, stretch=0)
        self.centralLayout.addWidget(self.photo, stretch=1)
        self.centralLayout.addStretch(1)

        ## MENU BAR
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setObjectName("menubar")
        self.menubar.setGeometry(QtCore.QRect(0, 0, 1600, 21))
        fmenu = self.menubar.addMenu('File')
        action = fmenu.addAction('Select files')
        action.triggered.connect(self.select_photos)
        MainWindow.setMenuBar(self.menubar)
        ## MENU DEBUG
        action = self.menubar.addAction('Select files')
        action.triggered.connect(self.select_photos)

        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        self.statusbar.setGeometry(QtCore.QRect(0, 0, 1600, 21))
        MainWindow.setStatusBar(self.statusbar)

        self.outname = QtWidgets.QLineEdit()
        self.outname.setObjectName("outname")
        self.outname.setValidator(OnlyInt.setup(OnlyInt()))
        self.outname.setText("0")
        self.statusbar.addWidget(self.outname)

        self.statusLabel = QtWidgets.QLabel()
        self.statusLabel.setObjectName("statusLabel")
        self.setStatusLabel("test")
        self.statusbar.addWidget(self.statusLabel)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)


    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        
        # self.displayImg("imgs/dog.jpg")
        # self.cat.setText(_translate("MainWindow", "CAT"))
        # self.dog.setText(_translate("MainWindow", "DOG"))
    
    def updateGalleryIdx(self):
        idx = self.curImgIdx
        return

    def updateGallery(self):
        self.updateGalleryIdx()
        return

    def select_photos(self):
        dialogDirImg = QtWidgets.QFileDialog(None)
        dialogDirImg.setFileMode(QtWidgets.QFileDialog.ExistingFiles)
        dialogDirImg.setNameFilters(["Images (*.png *.xpm *.jpg *.cr2)", "Any (*)"])
        if dialogDirImg.exec():
            self.selectedFiles = dialogDirImg.selectedFiles()
            if self.selectedFiles:
                print (self.selectedFiles)
                self.curImgIdx = 0
                self.displayMainImg()
                self.leftForm.updateIdx(self.curImgIdx, len(self.selectedFiles))
                self.updateGallery()

    def prevImg(self):
        if self.curImgIdx > 0:
            self.curImgIdx -= 1
            self.displayMainImg()
            self.leftForm.updateIdx(self.curImgIdx, len(self.selectedFiles))
            self.updateGalleryIdx()
    def nextImg(self):
        if (self.selectedFiles and self.curImgIdx + 1 < len(self.selectedFiles)):
            self.curImgIdx += 1
            self.displayMainImg()
            self.leftForm.updateIdx(self.curImgIdx, len(self.selectedFiles))
            self.updateGalleryIdx()

    def changeZoom(self):
        self.photo.ratio = self.leftForm.slider.value() / 100.0
        self.updateCropBox()
        
        self.mainWindow.resize(self.mainWindow.sizeHint())


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = uiMainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())