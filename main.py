import machine
import ssd1306
import config
import network
import utime as time
import urequests
import ujson
import gc
import math
import icons
import usocket

class Display:
	"""Class for controlling the oled i2c display"""
	def __init__(self, sda, scl):
		self.sda = sda
		self.scl = scl
		#setup and blank screen
		self.i2c = machine.I2C(scl=machine.Pin(scl), sda=machine.Pin(sda))
		self.oled = ssd1306.SSD1306_I2C(128, 32, self.i2c)
		self.clear()

	def show_text(self,str_in, column=0, row=0):
		self.oled.text(str_in,column * 8,row  *8,1)
		self.oled.show()

	def show_text_pixel(self,str_in, x=0, y=0):
		self.oled.text(str_in,x,y,1)
		self.oled.show()

	def clear(self):
		self.oled.fill(0)
		self.oled.show()

	def clear_text_row(self, y_pos):
		for y in range(0, 8):
			self.oled.hline(0, (y_pos * 8) + y, 16 * 8, False)
		self.oled.show()

	def show_bit_image(self,image, x_pos, y_pos, size_x, size_y, inv=False):
		x = 0
		y = 0
		for data in image:
			for a in range(0, 31):
				if (data & 1<<a):
					self.oled.pixel(x_pos + x, y_pos + y, not inv)
				x = x + 1
				if x == size_x:
					x = 0
					y = y + 1

class Weather():
	"""docstring for Weather"""
	def __init__(self, location, openweather_id):
		self.location = location
		self.openweather_id = openweather_id
		self.morning_temp = "0"
		self.day_temp = "0"
		self.evening_temp = "0"
		self.wind = "0"
		self.cloud = "0"
		self.current_weather = "none"
		self.text_too_long = False
		self.scroll_position = 0

	def update(self):
		data = urequests.get("http://api.openweathermap.org/data/2.5/forecast/daily?q="+self.location+"&units=metric&appid="+self.openweather_id+"&cnt=1").json()
		if data['cod'] is "200":
			self.current_weather = data['list'][0]['weather'][0]['description']
			if len(self.current_weather) > 16:
				self.text_too_long = True
			else:
				self.text_too_long = False
			self.current_weather = self.current_weather[0].upper() + self.current_weather[1:]
			self.morning_temp = str(round(data['list'][0]['temp']['morn']))
			self.day_temp = str(round(data['list'][0]['temp']['day']))
			self.evening_temp = str(round(data['list'][0]['temp']['eve']))
			self.wind = str(round(data['list'][0]['speed']))
			self.clouds = str(data['list'][0]['clouds'])
			data = None
			gc.collect()
			return True
		else:
			data = None
			gc.collect()
			disp.clear()
			disp.show_text("Error",0,0)
			disp.show_text("Location",0,1)
			disp.show_text("Unkown",0,2)
			return False

	def display(self):
		disp.clear()
		offset = math.floor((16-len(self.current_weather))/2)
		if offset < 0:
			offset = 0
		disp.show_text(self.current_weather,offset,0)

		disp.show_bit_image(icons.morning,0,2*8-2,9,9)
		disp.show_text_pixel(self.morning_temp,1*8+1,2*8)
		offset = len(self.morning_temp)*8
		disp.show_bit_image(icons.degree,1*8+1+offset,2*8,4,8)

		disp.show_bit_image(icons.day,5*8,2*8-3,9,9)
		disp.show_text_pixel(self.day_temp,6*8+1,2*8)
		offset = len(self.day_temp)*8
		disp.show_bit_image(icons.degree,6*8+1+offset,2*8,4,8)

		disp.show_bit_image(icons.evening, 10*8,2*8-2,7,9)
		disp.show_text_pixel(self.evening_temp,11*8+1,2*8)
		offset = len(self.evening_temp)*8
		disp.show_bit_image(icons.degree,11*8+1+offset,2*8,4,8)

		disp.show_bit_image(icons.cloud,0,3*8,15,8)
		disp.show_text(self.clouds+"%",2,3)

		disp.show_bit_image(icons.wind,9*8-1,3*8,16,8)
		disp.show_text(self.wind+"m/s",11,3)

	def scroll_description_text(self):
		disp.clear_text_row(0)
		self.scroll_position = (self.scroll_position + 1) % len(self.current_weather)
		disp.show_text(self.current_weather[self.scroll_position:self.scroll_position+16],0,0)


class Web_server():
	__content = """\
	HTTP/1.0 200 OK


	<html>
	<body bgcolor="#3366cc">
	<form action="/u">
	Wifi SSID:<br>
	<input type="text" name="id"><br>
	Wifi Password:<br>
	<input type="text" name="pass"><br>
	Location:<br>
	<input type="text" name="lo"><br>
	<input type="submit">
	</form>
	</body>
	</html>
	"""
	def __init__(self):
		self.server = usocket.socket()
		self.addr = usocket.getaddrinfo('0.0.0.0', 80)[0][-1]
		self.server.settimeout(0)
		self.server.bind(self.addr)
		self.server.listen(1)


	def poll(self):
		try:
			client, in_addr = self.server.accept()
			self.handle(client)
			client.close()
		except:
			pass

	def handle(self, client):
		values = ["","",""]
		req = str(client.recv(1024))
		if "/u?" in req:
			config_data = req.split(" ")[1]
			config_data = config_data[3:]
			config_data = config_data.split("&")
			for conf in config_data:
				if conf.split("=")[0] is "id":
					values[0]=conf.split("=")[1]
				elif conf.split("=")[0] is "pass":
					values[1]=conf.split("=")[1]
				elif conf.split("=")[0] is "lo":
					values[2]=conf.split("=")[1]
			self.write_setting(values)
			client.send("Updated, Rebooting")
			client.close()
			machine.reset()
		elif "/dev" in req:
			import webrepl
			webrepl.start()
			disp.clear()
			disp.show_text('DEV MODE')
			client.send("Dev mode on, connect via webrepl")
			client.close()
			exit()
		else:
			client.send(self.__content)

	def write_setting(self, values):
		f = open("config.py","w")
		f.write("SSID = \""+values[0]+"\"\n")
		f.write("PASSW = \""+values[1]+"\"\n")
		f.write("LOCATION = \""+values[2]+"\"\n")
		f.close()


def wifi_setup_mode():
	ap = network.WLAN(network.AP_IF)
	ap.active(True)
	ap.config(essid='ESP-weather',authmode=network.AUTH_OPEN)
	network_data = ap.ifconfig()
	disp.clear()
	disp.show_text('Setup mode')
	disp.show_text('SSID:ESP-weather',0,2)
	disp.show_text('ip: '+network_data[0],0,3)

def connect_wifi():
	sta_if = network.WLAN(network.STA_IF)
	if not sta_if.isconnected():
		disp.clear()
		disp.show_text('connecting...')
		sta_if.active(True)
		sta_if.connect(config.SSID, config.PASSW)
		a=0
		while not sta_if.isconnected() and a <= 1000:
			a=a+1
			time.sleep_ms(10)
		if sta_if.isconnected():
			ap = network.WLAN(network.AP_IF)
			ap.active(False)
			print('network config:', sta_if.ifconfig())
			disp.clear()
			disp.show_text("connected to",0,0,)
			disp.show_text(config.SSID,0,1)
			disp.show_text("ip:",0,2)
			network_data = sta_if.ifconfig()
			disp.show_text(network_data[0],0,3)
			time.sleep(3)
			return True
		else:
			sta_if.active(False)
			wifi_setup_mode()
			return False

def ISR_time(t):
	global minutes
	global seconds
	seconds = seconds + 1
	if seconds >= 59:
		minutes = minutes + 1
		seconds = 0

minutes = 0
seconds = 0
disp = Display(0, 2)
if connect_wifi():
	weather = Weather(config.LOCATION,config.OPENWEATHER_ID)
	if weather.update():
		weather.display()

web_server =Web_server()

tim = machine.Timer(-1)
tim.init(period=1000, mode=machine.Timer.PERIODIC, callback=ISR_time)

old_seconds = seconds

while True:
	web_server.poll()
	if weather.text_too_long == True and old_seconds != seconds:
		weather.scroll_description_text()
		old_seconds = seconds
	if minutes >= 60:
		minutes = 0
		print("update")
		if weather.update():
			weather.display()
