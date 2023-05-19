import sys
import os
import rawpy
import time

from pathlib import Path

from PyQt6 import QtCore, QtGui, QtWidgets
import numpy as np

import cv2

RUN_FREE = False
SIDEBARWIDTH = 225
SIDEOFFSET = 50

class OnlyInt(QtGui.QIntValidator):
    def __init__(self):
        super().__init__()
    def setup(self):
        self.setRange(0, 999999)
        return self
    
class QSAPhotoGallery(QtWidgets.QScrollArea):
    def __init__(self):
        self.selectedFiles = []
        self.pTII = None
        super().__init__()

    def setupUI(self, objname = "photogallery"):
        self.setGeometry(QtCore.QRect(0, 0, 250, 600))
        
        self.galleryW = QtWidgets.QWidget()
        self.gallery = QtWidgets.QFormLayout()
        self.gallery.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)

        self.galleryW.setLayout(self.gallery)

        self.setWidget(self.galleryW)
        self.setWidgetResizable(True)
        self.setFixedWidth(SIDEBARWIDTH-SIDEOFFSET)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOn) 
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

    def setImgIdxCB(self, func):
        self.pTII = func

    def getThumpPixmapFromPath(self, path):
        imgPath = path
        pixmapImg = None

        if (len(imgPath) >= 4 and (imgPath[-4:].lower() == ".cr2")):
            with rawpy.imread(imgPath) as raw:
                try:
                    thumb = raw.extract_thumb()
                except rawpy.LibRawNoThumbnailError:
                    print('no thumbnail found')
                except rawpy.LibRawUnsupportedThumbnailError:
                    print('unsupported thumbnail')
                else:
                    if thumb.format == rawpy.ThumbFormat.JPEG:
                        decoded = cv2.imdecode(np.frombuffer(thumb.data, np.uint8), -1)
                        height, width, channel = decoded.shape
                        bytesPerLine = 3 * width
                        qImg = QtGui.QImage(decoded.data, width, height, bytesPerLine, QtGui.QImage.Format.Format_BGR888)
                        pixmapImg = QtGui.QPixmap.fromImage(qImg)
                    elif thumb.format == rawpy.ThumbFormat.BITMAP:
                        pixmapImg = thumb.data
                        print ("bitmap") # NOT SURE IF WORK
        else:
            pixmapImg = QtGui.QPixmap(imgPath)
        return pixmapImg

    def setGallery(self, selectedFiles):
        
        while self.gallery.rowCount() > 1:
            self.gallery.removeRow(self.gallery.rowCount()-1)

        headlabel = QtWidgets.QLabel()
        headlabel.setText("Selected photos:")
        self.gallery.addRow(headlabel)

        self.selectedFiles = selectedFiles
        self.selectImg = [None] * len(selectedFiles)
        for idx, filePath in enumerate(selectedFiles):
            
            # draw divider line if not first item
            if idx > 0:
                line = QtWidgets.QFrame()
                line.setFrameShape(QtWidgets.QFrame.Shape.HLine)
                self.gallery.addRow(line)

            photo = PhotoWidget()
            photo.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
            photo.setText("")
            photo.setScaledContents(True)
            fname = Path(filePath).name
            photo.setObjectName("photo" + fname)
            thumbPixmap = self.getThumpPixmapFromPath(filePath)
            height, width = thumbPixmap.rect().height(), thumbPixmap.rect().width()
            scale = np.min([(SIDEBARWIDTH-2*SIDEOFFSET)/width, SIDEBARWIDTH/2/height])
            nh = int(height * scale)
            nw = int(width * scale)
            photo.setMinimumSize(nw, nh)
            photo.setMaximumSize(nw, nh)
            photo.setPixmap(thumbPixmap)
            self.gallery.addRow(photo)

            self.selectImg[idx] = QtWidgets.QPushButton()
            self.selectImg[idx].setObjectName("imgsel"+str(idx))
            self.selectImg[idx].setText(fname)
            self.selectImg[idx].clicked.connect(lambda state, i=idx: self.pTII(i))
            self.gallery.addRow(self.selectImg[idx])
    

class LeftToolBox(QtWidgets.QVBoxLayout):
    def __init__(self):
        self.idx = 0
        self.len = 0
        super().__init__()

    def updateIdx(self, i, n):
        self.idx = i
        self.len = n
        self.imgidxtext.setText(str(self.idx+1) + " / " + str(self.len))

    def setXY(self,x, y):
        self.outwidth.setText(str(x))
        self.outheight.setText(str(y))

    def setGallery(self, selectedFiles):
        self.gallery.setGallery(selectedFiles)
    
    def setGalleryImgIdxCB(self, func):
        self.gallery.setImgIdxCB(func)
    
    def setupUI(self):
        self.setObjectName("leftform")
        self.setGeometry(QtCore.QRect(0, 0, 250, 600))

        self.settings = QtWidgets.QFormLayout()
        self.settings.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)

        self.r0 = QtWidgets.QRadioButton("Occlusal") # 10:8
        self.r0.setChecked(1)
        self.r0.clicked.connect(lambda:self.setXY(500,400))
        self.settings.addRow(self.r0)
        self.r1 = QtWidgets.QRadioButton("Frontal/Buccal") # 16:9
        self.r1.clicked.connect(lambda:self.setXY(480,270))
        self.settings.addRow(self.r1)
        self.r2 = QtWidgets.QRadioButton("Profile") # 5:7
        self.r2.clicked.connect(lambda:self.setXY(350,490))
        self.settings.addRow(self.r2)

        self.outwidth = QtWidgets.QLineEdit()
        self.outwidth.setValidator(OnlyInt.setup(OnlyInt()))
        self.outwidth.setText("500")
        self.settings.addRow("Width: ", self.outwidth)
        self.outheight = QtWidgets.QLineEdit()
        self.outheight.setValidator(OnlyInt.setup(OnlyInt()))
        self.outheight.setText("400")
        self.settings.addRow("Height:",self.outheight)

        self.nav = QtWidgets.QFormLayout()
        self.nav.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)

        self.imgidxtext = QtWidgets.QLabel()
        self.imgidxtext.setText(str(self.idx) + " / " + str(self.len))
        self.checkClickNext = QtWidgets.QCheckBox()
        self.checkClickNext.setText("Click -> Next")
        self.checkClickNext.setCheckState(QtCore.Qt.CheckState.Unchecked)
        self.nav.addRow(self.imgidxtext, self.checkClickNext)

        self.prev = QtWidgets.QPushButton()
        self.prev.setText("Prev")
        self.next = QtWidgets.QPushButton()
        self.next.setText("Next")
        self.nav.addRow(self.prev, self.next)
        self.resetImg = QtWidgets.QPushButton()
        self.resetImg.setText("Reset")
        self.nav.addRow(self.resetImg)
        
        self.sliderLabel = QtWidgets.QLabel()
        self.sliderLabel.setText("Image Zoom")
        self.nav.addRow(self.sliderLabel)
        self.slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.slider.setPageStep(0)
        self.slider.setMinimum(0)
        self.slider.setMaximum(200)
        self.slider.setValue(1)
        self.slider.setTickPosition(QtWidgets.QSlider.TickPosition.TicksBelow)
        self.slider.setTickInterval(25)
        self.nav.addRow(self.slider)

        self.cw = QtWidgets.QPushButton()
        self.cw.setText("CW")
        self.ccw = QtWidgets.QPushButton()
        self.ccw.setText("CCW")
        self.nav.addRow(self.ccw, self.cw)

        self.mirrorvert = QtWidgets.QPushButton()
        self.mirrorvert.setText("Mirror -")
        self.mirrorhori = QtWidgets.QPushButton()
        self.mirrorhori.setText("Mirror |")
        self.nav.addRow(self.mirrorvert, self.mirrorhori)

        self.galleryForm = QtWidgets.QFormLayout()
        self.galleryForm.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)

        self.gallery = QSAPhotoGallery()
        self.gallery.setupUI()
        self.galleryForm.addRow(self.gallery)

        self.addLayout(self.settings,0)
        self.addLayout(self.nav, 0)
        self.addLayout(self.galleryForm, 1)

class RightToolBox(QtWidgets.QVBoxLayout):
    # TODO: add delete button

    hxItems = {}

    def __init__(self):
        self.photos = []
        super().__init__()
    
    def setupUI(self):
        self.setObjectName("rightform")
        self.setGeometry(QtCore.QRect(0, 0, 250, 600))
        
        self.historyW = QtWidgets.QWidget()
        self.history = QtWidgets.QFormLayout()
        self.history.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)

        self.text = QtWidgets.QLabel()
        self.text.setText("History:")
        self.history.addRow(self.text)
        self.historyW.setLayout(self.history)

        self.scrollArea = QtWidgets.QScrollArea()
        self.scrollArea.setWidget(self.historyW)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setFixedWidth(SIDEBARWIDTH)
        self.scrollArea.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOn) 
        self.scrollArea.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        self.addWidget(self.scrollArea)

    def addEntry(self, img, fname):
        photo = PhotoWidget()
        photo.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
        photo.setText("")
        photo.setScaledContents(True)
        photo.setObjectName("photo" + str(len(self.photos)))
        height, width, channel = img.shape
        scale = (SIDEBARWIDTH-SIDEOFFSET)/width
        nh = int(scale * height)
        photo.setMinimumSize(SIDEBARWIDTH-SIDEOFFSET, nh)
        photo.setMaximumSize(SIDEBARWIDTH-SIDEOFFSET, nh)
        bytesPerLine = 3 * width
        qImg = QtGui.QImage(img.data, width, height, bytesPerLine, QtGui.QImage.Format.Format_BGR888)
        img = QtGui.QPixmap.fromImage(qImg)
        photo.setPixmap(img)
        #photo.setGeometry(QtCore.QRect(0, 0, width, height))
        self.photos.append(photo)
        self.history.insertRow(1, photo)

        self.text = QtWidgets.QLabel()
        self.text.setText(fname)

        deleteImg = QtWidgets.QPushButton()
        deleteImg.setObjectName("delimg"+fname)
        deleteImg.setText("Delete")
        deleteImg.clicked.connect(lambda: self.delFile(fname))
        self.history.insertRow(2, self.text, deleteImg)
        self.hxItems[fname] = [photo, self.text, deleteImg]

    def delFile(self, fname):
        return
        

class PhotoWidget(QtWidgets.QLabel):

    def __init__(self):
        self.basePixmapImg = 0
        self.pixmapImg = 0
        self.pixmapShow = 0
        self.baserect = 0
        self.cropscale = 1.0
        self.ratio = 1.0
        self.rotAngle = -1e-6
        self.transform = QtGui.QTransform()

        self.pMME = 0
        self.pMPE = 0
        self.pMWE = 0

        super().__init__()

    def resetImg(self):
        self.cropscale = 1.0
        self.rotAngle = -1e-6
        self.transform = QtGui.QTransform()

    def redisplayPixmap(self, pmap):
        self.setPixmap(pmap)
        self.pixmapShow = pmap

    def displayPixmap(self, pixmap):
        # load new pixmap, using filepath scale image to window size and display it, record ratio of scaling
        self.transform = QtGui.QTransform() # reset transform
        self.pixmapImg = pixmap.copy()
        self.basePixmapImg = pixmap.copy()
        newPixmapShow = self.pixmapImg.copy()
        if (self.width() < self.pixmapImg.width() or self.height() < self.pixmapImg.height()):
            newPixmapShow = newPixmapShow.scaled (self.width(), self.height(), QtCore.Qt.AspectRatioMode.KeepAspectRatio)
        self.ratio = newPixmapShow.width() / self.pixmapImg.width()
        self.redisplayPixmap(newPixmapShow)

    def updateCropBox(self, bw, bh, color = QtGui.QColor("green")):
        # add cropping box to photo, photo is scaled to recorded ratio
        if (self.pixmapImg):
            pixmapNew = self.pixmapImg.copy()
            pixmapNew = pixmapNew.transformed(self.transform)
            if pixmapNew:
                painter = QtGui.QPainter(pixmapNew)

                # draw base resolution box
                painter.setPen(QtGui.QPen(QtGui.QColor("grey"), 5.0, QtCore.Qt.PenStyle.DashDotLine))
                self.baserect = QtCore.QRect(0, 0, int(bw), int(bh))
                curpos = QtGui.QCursor.pos()
                transcurpos = self.mapFromGlobal(curpos) / self.ratio

                transform = QtGui.QTransform()
                transform.translate(transcurpos.x(), transcurpos.y())
                transform.rotate(self.rotAngle)
                transform.translate(-bw/2, -bh/2)

                transformedPolygon = transform.mapToPolygon(self.baserect)
                painter.drawPolygon(transformedPolygon)
                
                # draw crop bound box
                painter.setPen(QtGui.QPen(color, 10.0, QtCore.Qt.PenStyle.DashLine))
                # transform cropping box
                transform = QtGui.QTransform()
                transform.translate(transcurpos.x(), transcurpos.y())
                transform.scale(self.cropscale, self.cropscale)
                transform.rotate(self.rotAngle)
                transform.translate(-bw/2, -bh/2)
                transformedPolygon = transform.mapToPolygon(self.baserect)
                painter.drawPolygon(transformedPolygon)
                
                # draw crosshair
                painter.setPen(QtGui.QPen(QtGui.QColor("grey"), 5.0, QtCore.Qt.PenStyle.DashDotLine))
                p1 = transform.map((self.baserect.topLeft() + self.baserect.bottomLeft())/2)
                p2 = transform.map((self.baserect.topRight() + self.baserect.bottomRight())/2)
                painter.drawLine(p1, p2)
                p1 = transform.map((self.baserect.topLeft() + self.baserect.topRight())/2)
                p2 = transform.map((self.baserect.bottomLeft() + self.baserect.bottomRight())/2)
                painter.drawLine(p1, p2)

                self.baserect = transformedPolygon
                self.pixmapShow = pixmapNew.scaled (round(pixmapNew.width()*self.ratio), round(pixmapNew.height()*self.ratio), QtCore.Qt.AspectRatioMode.KeepAspectRatio)
                painter.end()
            self.redisplayPixmap(self.pixmapShow)
    
    def rotateCV2Image(self, image, angle):
        image_center = tuple(np.array(image.shape[1::-1]) / 2)
        rot_mat = cv2.getRotationMatrix2D(image_center, angle, 1.0)
        result = cv2.warpAffine(image, rot_mat, image.shape[1::-1], flags=cv2.INTER_LINEAR)
        return result

    def convertQPixmapToMat(self, pixmap):
        '''  Converts a QImage into an opencv MAT format  '''
        incomingImage = pixmap.toImage()
        incomingImage = incomingImage.convertToFormat(QtGui.QImage.Format.Format_RGBX8888)

        width = incomingImage.width()
        height = incomingImage.height()

        ptr = incomingImage.bits()
        ptr.setsize(incomingImage.sizeInBytes())

        arr = np.array(ptr, copy=True).reshape(height, width, 4)
        arr = cv2.cvtColor(arr, cv2.COLOR_BGRA2RGB)
        return arr
        arr = np.array(ptr).reshape(height, width, 4)  #  Copies the data
        return arr

    def saveCrop(self, bw, bh, fn, otype=".jpg", compressLvl=80):
        ''' Saves selected crop, takes auguments width/height, output file name, output file type, compression level [0-100]'''
        # crop is extracted and resized to dimension then saved
        # Rect crop: https://jdhao.github.io/2019/02/23/crop_rotated_rectangle_opencv/
        # TODO: add save format
        if self.baserect:
            fileName = "out/" + str(fn) + otype
            if not os.path.exists("out"):
                os.makedirs("out")

            # convert to CV2 Mat
            transformedPixmapImg = self.pixmapImg.transformed(self.transform)
            img = self.convertQPixmapToMat(transformedPixmapImg)

            a,b,c,d = self.baserect.point(0), self.baserect.point(1), self.baserect.point(2), self.baserect.point(3)
            def limitPt(pt, small, big):
                pt.setX(np.min([np.max([pt.x(), small]), big]))
                pt.setY(np.min([np.max([pt.y(), small]), big]))
                return pt
            rectPt = np.array([ [[a.x(), a.y()]], [[b.x(), b.y()]], [[c.x(), c.y()]], [[d.x(), d.y()]] ])
            rect = cv2.minAreaRect(rectPt)
            print("shape of rect: {}".format(rect))

            box = cv2.boxPoints(rect)
            box = np.int0(box)

            print("bounding box: {}".format(box))
            cv2.drawContours(img, [box], 0, (0, 0, 255), 2)

            # get width and height of the detected rectangle
            width = int(rect[1][0])
            height = int(rect[1][1])
            
            src_pts = box.astype("float32")
            # coordinate of the points in box points after the rectangle has been
            # straightened
            dst_pts = np.array([[0, height-1],
                                [0, 0],
                                [width-1, 0],
                                [width-1, height-1]], dtype="float32")

            # the perspective transformation matrix
            M = cv2.getPerspectiveTransform(src_pts, dst_pts)

            # directly warp the rotated rectangle to get the straightened rectangle
            warped = cv2.warpPerspective(img, M, (width, height))
            if self.rotAngle <= 0:
                warped = cv2.rotate(warped, cv2.ROTATE_90_CLOCKWISE)

            fmulti = 1
            if RUN_FREE:
                fmulti = 0.1
            nmulti = 200/bw
            nbw, nbh = int(nmulti * bw *fmulti), int(nmulti * bh * fmulti)

            thumbImg = cv2.resize(warped, (nbw, nbh))
            #cv2.imshow("Cropped", thumbImg)
            cv2.imwrite(fileName, warped, [cv2.IMWRITE_JPEG_QUALITY, compressLvl])

            return thumbImg

            def addBlackBorder():
                pixmapTrans = QtGui.QPixmap(w*3, h*3)
                pixmapTrans.fill(QtGui.QColor(QtGui.qRgba64(0, 0, 0, 0)))
                targRect = QtCore.QRect(w, h, w, h)

                painter = QtGui.QPainter(pixmapTrans)
                painter.drawPixmap(targRect, transformedPixmapImg, transformedPixmapImg.rect())
                painter.end()

            def scaling():
                # reopen file to scale with opencv
                img = cv2.imread(fileName)
                resized = cv2.resize(img, (bw, bh))
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
    
    def transformImg(self, transform):
        self.transform *= transform

class uiMainWindow(QtCore.QObject):
    curImgIdx = -1

    def __init__(self):
        super(uiMainWindow,self).__init__()
        self.selectedFiles = 0

        self.photo = PhotoWidget()
        self.photo.setGeometry(QtCore.QRect(0, 0, 1250, 900))
        self.photo.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
        self.photo.setText("")
        self.photo.setScaledContents(False)
        self.photo.setObjectName("photo")
        self.photo.setMouseTracking(True)
        self.photo.setMouseMoveEvent(self.photoMouseMoveEvent)
        self.photo.setMousePressEvent(self.photoMousePressEvent)
        self.photo.setMouseWheelEvent(self.photoMouseWheelEvent)
    
    def photoMousePressEvent(self, event):
        if event.buttons() == QtCore.Qt.MouseButton.LeftButton:
            self.updateCropBox(QtGui.QColor("red"))
            thumbImg, fname = self.saveCrop()
            self.rightForm.addEntry(thumbImg, fname)
        elif event.buttons() == QtCore.Qt.MouseButton.RightButton:
            self.nextImg()

    def photoMouseMoveEvent(self, event):
        if event.buttons() == QtCore.Qt.MouseButton.NoButton:
            self.updateCropBox()

    def photoMouseWheelEvent(self, event):
        ControlState = QtWidgets.QApplication.keyboardModifiers() == QtCore.Qt.KeyboardModifier.ControlModifier
        adj = (event.angleDelta().y() / 120) * 0.1
        if ControlState == False:
            self.photo.cropscale += -adj
            self.photo.cropscale = max(1.0, self.photo.cropscale)
            self.updateCropBox()
        elif ControlState == True:
            # TODO: set crop angle
            self.photo.rotAngle += adj * 16
            self.photo.rotAngle = min(40, self.photo.rotAngle)
            self.photo.rotAngle = max(-40, self.photo.rotAngle)
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
                pixmapImg = QtGui.QImage(nparrRGB.data, w, h, bytesPerLine, QtGui.QImage.Format.Format_RGB888)
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

    def resetImg(self):
        self.photo.resetImg()
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
        thumbImg = self.photo.saveCrop(bw, bh, fn)
        if self.leftForm.checkClickNext.isChecked():
            self.nextImg()
        return thumbImg, fn
        #time.sleep(np.random.rand()*1 + np.random.rand()*1 + np.random.rand()*1 + np.random.rand()*1 + np.random.rand()*1 + np.random.rand()*1)

    def setupUi(self, MainWindow):
        self.mainWindow = MainWindow
        MainWindow.setObjectName("mainwindow")
        MainWindow.resize(1600, 900)

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
        self.leftForm.resetImg.clicked.connect(self.resetImg)
        self.leftForm.ccw.clicked.connect(self.rotImgCCW)
        self.leftForm.cw.clicked.connect(self.rotImgCW)
        self.leftForm.mirrorvert.clicked.connect(self.mirrorImgV)
        self.leftForm.mirrorhori.clicked.connect(self.mirrorImgH)
        self.leftForm.setGalleryImgIdxCB(self.toImgIdx)

        self.rightForm = RightToolBox()
        self.rightForm.setupUI()
        self.rightForm.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight)

        self.centralLayout.addLayout(self.leftForm, stretch=0)
        self.centralLayout.addWidget(self.photo, stretch=1)
        self.centralLayout.addLayout(self.rightForm, stretch=0)
        #self.centralLayout.addStretch(1)


        ## MENU BAR
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setObjectName("menubar")
        self.menubar.setGeometry(QtCore.QRect(0, 0, 1600, 21))
        fmenu = self.menubar.addMenu('File')
        action = fmenu.addAction('Select files')
        action.triggered.connect(self.selectPhotos)
        MainWindow.setMenuBar(self.menubar)
        ## MENU DEBUG
        action = self.menubar.addAction('Select files')
        action.triggered.connect(self.selectPhotos)

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
        self.setStatusLabel("Scroll wheel with and without control to control crop, left click to crop, right click for next. Email Tony - quansa.sun@gmail.com for troubleshooting.")
        self.statusbar.addWidget(self.statusLabel)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)



    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle("TS fast image cropper")
        
        # self.displayImg("imgs/dog.jpg")
        # self.cat.setText(_translate("MainWindow", "CAT"))
        # self.dog.setText(_translate("MainWindow", "DOG"))
    
    def updateGalleryIdx(self):
        idx = self.curImgIdx
        return

    def updateGallery(self):
        self.updateGalleryIdx()
        return

    def selectPhotos(self):
        dialogDirImg = QtWidgets.QFileDialog(None)
        dialogDirImg.setFileMode(QtWidgets.QFileDialog.FileMode.ExistingFiles)
        dialogDirImg.setNameFilters(["Images (*.png *.xpm *.jpg *.cr2)", "Any (*)"])
        if dialogDirImg.exec():
            self.selectedFiles = dialogDirImg.selectedFiles()
            if self.selectedFiles:
                print (self.selectedFiles)
                self.curImgIdx = 0
                self.displayMainImg()
                self.leftForm.updateIdx(self.curImgIdx, len(self.selectedFiles))
                self.updateGallery()
                self.leftForm.setGallery(self.selectedFiles)

    def debugPhoto(self):
        self.selectedFiles = ["C:/Users/quans/OneDrive/Documents/code/framecrop/dataset/img1.jpg"]
        self.curImgIdx = 0
        self.displayMainImg()
        self.leftForm.updateIdx(self.curImgIdx, len(self.selectedFiles))
        self.updateGallery()

    def toImgIdx(self, idx):
        if (self.curImgIdx < 0 or self.curImgIdx >= len(self.selectedFiles)):
            return
        self.curImgIdx = idx
        #print(idx)
        self.displayMainImg()
        self.leftForm.updateIdx(self.curImgIdx, len(self.selectedFiles))
        self.updateGalleryIdx()

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
        MWSizeHint = self.mainWindow.sizeHint()
        if (self.mainWindow.width() > 1400 or self.mainWindow.height() > 900):
            self.mainWindow.resize(MWSizeHint)

    def rotImgCCW(self):
        transform = QtGui.QTransform()
        transform.rotate(-90)
        self.photo.transformImg(transform)
        self.updateCropBox()
    
    def rotImgCW(self):
        transform = QtGui.QTransform()
        transform.rotate(90)
        self.photo.transformImg(transform)
        self.updateCropBox()
    
    def mirrorImgV(self):
        transform = QtGui.QTransform()
        transform.scale(1, -1)
        self.photo.transformImg(transform)
        self.updateCropBox()
    
    def mirrorImgH(self):
        transform = QtGui.QTransform()
        transform.scale(-1, 1)
        self.photo.transformImg(transform)
        self.updateCropBox()

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = uiMainWindow()
    ui.setupUi(MainWindow)
    #ui.debugPhoto()
    MainWindow.show()
    sys.exit(app.exec())