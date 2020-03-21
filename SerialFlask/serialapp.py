import time

from flask import Flask, render_template, Response, request

from serial import Serial, SerialException

import serial.tools.list_ports

import io

app = Flask(__name__)

SERIAL_PORT = '/dev/ttyUSB0'
SERIAL_RATE = 115200

sendData = ""

ser = Serial()

ser.baudrate = SERIAL_RATE

try:
	ser.port = SERIAL_PORT;
	ser.open()
except SerialException:
	sendData = "error"

interrupt = False

@app.route('/')
def index():
	return render_template('index.html')

@app.route('/ports')
def ports():

	def getPorts():
		while True:
			ports = serial.tools.list_ports.comports()
			portsCom = [port.device for port in ports]
			formatedData = ','.join([str(elem) for elem in portsCom])
			yield "data:" + formatedData + "\n\n"
			time.sleep(1)

	return Response(getPorts(), mimetype= 'text/event-stream')


@app.route('/data')
def data():

	def generate():
		global sendData

		while True:

			global sendData

			global interrupt

			if sendData != "error":
				try:
					if not interrupt:
						try:
							sendData = ser.readline().decode("ascii")
						except SerialException:
							sendData = "error"
					else:
						sendData = ""
						time.sleep(0.5)
				except UnicodeDecodeError:
					sendData = "unknownChar"
			elif sendData == "error":
				if not interrupt:
					time.sleep(1.5)
				else:
					sendData = ""

			yield "data:" + sendData + "\n\n"

	return Response(generate(), mimetype= 'text/event-stream')

@app.route('/receive', methods = ['POST'])
def my_form_post():
	text = request.json['input']

	text += "\n\n"

	global interrupt

	if not interrupt:
		ser.write(text.encode())

	print("Read " + text)
	return text

@app.route('/ctrlC', methods = ['POST'])
def ctrlC():
	global interrupt

	if not interrupt:
		ser.write(('\x03\n').encode())

	print("Control + C")
	return "ctrlC"

@app.route('/connect', methods = ['POST'])
def connect():
	text = request.json['selected']
	global sendData

	global interrupt

	interrupt = True

	try:
		if ser.is_open:
			ser.close()

		ser.port = text
		ser.open()
		sendData = "connected"
	except SerialException:
		try:
			if ser.is_open:
				ser.close()

			ser.port = text
			ser.open()
			sendData = "connected"
		except SerialException:
			sendData = "error"

	interrupt = False

	print("Connect Attempt " + text)
	return text

if __name__ == "__main__":
	app.run(port=80, host='0.0.0.0') #host='0.0.0.0',
