from attendence import Ui_MainWindow
from PyQt5 import Qt
import sys, cv2, os
from PIL import Image
from PIL.ImageQt import ImageQt
import cfg
import imutils
from imutils import paths
import face_recognition
import pickle

a = Qt.QApplication(sys.argv)
class attendence(Qt.QWidget):
    def __init__(self):
        super(attendence, self).__init__()
        self.design = Ui_MainWindow()
        self.design.setupUi(self)
        self.graphicsScene = Qt.QGraphicsScene()
        self.fps = 24
        self.frame = 0
        self.path = ""
        self.runtimeData = cfg.runtimeData
        self.design.pushButton.clicked.connect(lambda: self.webcame())
        self.design.pushButton_2.clicked.connect(lambda: self.face_recognationprocess())
        self.design.radioButton.setChecked(True)
        self.design.pushButton_2.hide()
        self.design.radioButton.clicked.connect(lambda: self.disablevrb())
        self.design.radioButton_2.clicked.connect(lambda: self.disablevrb1())

    def disablevrb(self):
        self.design.pushButton_2.hide()
        self.design.pushButton.show()

    def disablevrb1(self):
        self.design.pushButton.hide()
        self.design.pushButton_2.show()

    def webcame(self):
        self.design.pushButton.setText("STOP REGISTRACTION")
        name = self.design.lineEdit.text()
        self.collectData(name)
        if len(self.design.lineEdit.text()) == 0:
            Qt.QMessageBox.about(self, "Info", "Enter Name")
        self.cap = cv2.VideoCapture(0)
        self.timerLive = Qt.QTimer()
        self.timerLive.timeout.connect(self.nextFrameSlot)
        self.timerLive.start(1000. / self.fps)

    def nextFrameSlot(self):
        ret, img = self.cap.read()
        img = imutils.rotate(img,90)
        self.frame = self.frame + 1
        if self.frame > 100:
            self.timerLive.stop()
            self.cap.release()
            self.graphicsScene.clear()
            cv2.destroyAllWindows()
            self.faceencoding()
        else:
            self.saveImage(img, self.frame)
            frame = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            frame = Image.fromarray(frame)
            frame = ImageQt(frame)
            self.pixmap = Qt.QPixmap.fromImage(frame)
            self.pixmap = self.pixmap.scaled(self.size(), Qt.Qt.KeepAspectRatio)
            self.graphicsPixmapItem = Qt.QGraphicsPixmapItem(self.pixmap)
            self.graphicsScene.addItem(self.graphicsPixmapItem)
            self.design.graphicsView.setScene(self.graphicsScene)
            self.design.graphicsView.fitInView(self.graphicsScene.sceneRect(), Qt.Qt.KeepAspectRatio)

    def collectData(self, name):
        if self.design.radioButton.isChecked():
            self.path = self.runtimeData + "/" + name
            os.system("mkdir -p " + self.path)

    def saveImage(self, image,frame):
        cv2.imwrite(self.path + "/" + str(frame)+".jpg",image)

    def faceencoding(self):
        dataset = "/home/dhanpal/myProject/attendSystem/runTime_Data"
        print("[INFO] quantifying faces...")
        imagePaths = list(paths.list_images(dataset))
        knownEncodings = []
        knownNames = []
        for (i, imagePath) in enumerate(imagePaths):
            print("[INFO] processing image {}/{}".format(i + 1, len(imagePaths)))
            name = imagePath.split(os.path.sep)[-2]
            image = cv2.imread(imagePath)
            image = cv2.resize(image, (100, 100))
            rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            boxes = face_recognition.face_locations(rgb, model="cnn")
            print(boxes)
            encodings = face_recognition.face_encodings(rgb, boxes)
            for encoding in encodings:
                knownEncodings.append(encoding)
                knownNames.append(name)
        print("[INFO] serializing encodings...")
        data = {"encodings": knownEncodings, "names": knownNames}
        f = open("encodings.pickle", "wb")
        f.write(pickle.dumps(data))
        f.close()

    def face_recognationprocess(self):
        self.time = 0
        print('face recognation called')
        encodings = "/home/dhanpal/myProject/attendSystem/encodings.pickle"
        print("[INFO] loading encodings...")
        self.data = pickle.loads(open(encodings, "rb").read())
        # self.cap = cv2.VideoCapture("/home/dhanpal/myProject/attendSystem/data/VID_20191007_122906.mp4")
        self.cap = cv2.VideoCapture(0)

        self.timerLive = Qt.QTimer()
        self.timerLive.timeout.connect(self.face_recognation)
        self.timerLive.start(1000. / self.fps)

    def face_recognation(self):
        name = ''
        ret, frame = self.cap.read()
        # frame = imutils.rotate(frame, 90)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        rgb = cv2.pyrDown(rgb)
        rgb = cv2.pyrDown(rgb)
        r = frame.shape[1] / float(rgb.shape[1])
        boxes = face_recognition.face_locations(rgb, model="cnn")
        encodings = face_recognition.face_encodings(rgb, boxes)
        names = []
        for encoding in encodings:
            matches = face_recognition.compare_faces(self.data["encodings"], encoding)
            name = "Unknown"
            if True in matches:
                matchedIdxs = [i for (i, b) in enumerate(matches) if b]
                counts = {}
                for i in matchedIdxs:
                    name = self.data["names"][i]
                    counts[name] = counts.get(name, 0) + 1
                name = max(counts, key=counts.get)
            names.append(name)
        for ((top, right, bottom, left), name) in zip(boxes, names):
            top = int(top * r)
            right = int(right * r)
            bottom = int(bottom * r)
            left = int(left * r)
            cv2.rectangle(frame, (left, top), (right, bottom),
                          (0, 255, 0), 2)
            y = top - 15 if top - 15 > 15 else top + 15
            cv2.putText(frame, name, (left, y), cv2.FONT_HERSHEY_SIMPLEX,0.75, (0, 255, 0), 2)
            frame = cv2.pyrUp(frame)
            frame = cv2.pyrUp(frame)
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            frame = Image.fromarray(frame)
            frame = ImageQt(frame)
            self.pixmap = Qt.QPixmap.fromImage(frame)
            self.pixmap = self.pixmap.scaled(self.size(), Qt.Qt.KeepAspectRatio)
            self.graphicsPixmapItem = Qt.QGraphicsPixmapItem(self.pixmap)
            self.graphicsScene.addItem(self.graphicsPixmapItem)
            self.design.graphicsView.setScene(self.graphicsScene)
            self.design.graphicsView.fitInView(self.graphicsScene.sceneRect(), Qt.Qt.KeepAspectRatio)
            self.time += 1

        if self.time >= 50 and name != "Unknown":
            self.graphicsScene.clear()
            self.timerLive.stop()
            Qt.QMessageBox.about(self, "Info", "Hi!! {} You can attend the lecture !!!".format(name))




App = attendence()
App.show()
sys.exit(a.exec_())
