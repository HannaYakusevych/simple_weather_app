import sys
import os
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, pyqtSignal, QObject, QRunnable, pyqtSlot, QThreadPool
from PyQt5.QtGui import *
from urllib.parse import urlencode
from urllib.request import urlopen
import requests
import json

# Test key, number of calls is limited
OPENWEATHERMAP_API_KEY = '31c510803ceaeadb5c7d5bc07d5e7bbb'

class WeatherServiceSignals(QObject):
    finished = pyqtSignal()
    error = pyqtSignal(str)
    result = pyqtSignal(dict, QPixmap)

class WeatherService(QRunnable):
    signals = WeatherServiceSignals()
    is_interrupted = False

    def __init__(self, location):
        super(WeatherService, self).__init__()
        self.location = location

    @pyqtSlot()
    def run(self):
        try:
            params = dict(
                q=self.location.encode('cp1251'),
                appid=OPENWEATHERMAP_API_KEY
            )

            # Current weather request
            url = 'http://api.openweathermap.org/data/2.5/weather?%s&units=metric&lang=ru' % urlencode(params)
            r = requests.get(url)
            weather = json.loads(r.text)

            # Check if we had a failure
            if weather['cod'] != 200:
                raise Exception("Не получилось найти данные. Проверьте введенное название, или попробуйте ввести другой город")

            # Download an icon
            url = 'http://openweathermap.org/img/wn/%s@2x.png' % weather['weather'][0]['icon']

            pixmap = QPixmap()
            with urlopen(url) as url:
                data = url.read()
                pixmap.loadFromData(data)

            self.signals.result.emit(weather, pixmap)

        except Exception as e:
            self.signals.error.emit(str(e))

        self.signals.finished.emit()

class WeatherWindow(QMainWindow):

    def __init__(self, *args, **kwargs):
        super(WeatherWindow, self).__init__(*args, **kwargs)
        self.threadpool = QThreadPool()
        self.setupUi()



    def setupUi(self):
        # App title
        self.setWindowTitle("WeatherApp")

        # App size - for the first version it is easier to make it not resizable
        self.setFixedSize(430, 230)

        # Create textbox description
        self.label = QLabel(self)
        self.label.setText('Введите название вашего города\nна английском языке')
        self.label.move(20, 16)
        self.label.resize(300, 30)

        # Create textbox
        self.textbox = QLineEdit(self)
        self.textbox.move(20, 54)
        self.textbox.resize(280, 26)

        # Create a button in the window
        self.button = QPushButton('Применить', self)
        self.button.move(316, 54)
        # self.button.resize(80, 20)

        # connect button to function on_click
        self.button.clicked.connect(self.on_click)

        # add weather description
        self.weatherLabel = QLabel(self)
        self.weatherLabel.move(20, 90)
        self.weatherLabel.resize(200, 20)

        # add weather icon
        self.icon = QLabel(self)
        self.icon.move(20, 115)
        self.icon.resize(100, 100)

        # temperature label
        self.temperatureLabel = QLabel(self)
        self.temperatureLabel.move(130, 115)
        self.temperatureLabel.resize(150, 100)
        self.temperatureLabel.setFont(QFont('Arial', 30))

        # pressure label
        self.pressureLabel = QLabel(self)
        self.pressureLabel.move(250, 85)
        self.pressureLabel.resize(190, 120)

        # humidity label
        self.humidityLabel = QLabel(self)
        self.humidityLabel.move(250, 105)
        self.humidityLabel.resize(190, 120)

        # wind speed label
        self.windLabel = QLabel(self)
        self.windLabel.move(250, 125)
        self.windLabel.resize(190, 120)

        self.show()

    @pyqtSlot()
    def on_click(self):
        text = self.textbox.text()
        if not text:
            self.alert("Название города не может быть пустым")
            return

        if not self.isEnglish(text):
            self.alert("Название должно быть написано на английском языке")
            return

        worker = WeatherService(text)
        worker.signals.result.connect(self.weather_result)
        worker.signals.error.connect(self.alert)
        self.threadpool.start(worker)


    def weather_result(self, weather, pixmap):
        self.weatherLabel.setText("%s" % weather['weather'][0]['description'].capitalize())

        self.icon.setAutoFillBackground(True)
        pal = QPalette()
        pal.setColor(QPalette.Background, QColor(99, 205, 218))
        self.icon.setPalette(pal);
        self.icon.setPixmap(pixmap)

        self.temperatureLabel.setText("%.1f °C" % weather['main']['temp'])
        self.pressureLabel.setText("Давление: %d гПа" % weather['main']['pressure'])
        self.humidityLabel.setText("Влажность: %d%%" % weather['main']['humidity'])
        self.windLabel.setText("Скорость ветра: %.1f м/с" % weather['wind']['speed'])

    def alert(self, message):
        alert = QMessageBox.warning(self, "Ошибка", message)

    def isEnglish(self, s):
        try:
            s.encode(encoding='utf-8').decode('ascii')
        except UnicodeDecodeError:
            return False
        else:
            return True


if __name__ == '__main__':
    app = QApplication(sys.argv)

    window = WeatherWindow()
    app.exec_()
