#coding: utf-8

from dashboard_conf import *
import asyncui
from ui import *
from uiconstraints import Constrain as C

import math, sys, json
from collections import defaultdict

class GridView(View):
  
  def add_subview(self, subview):
    super().add_subview(subview)
    C(self).dock_all()
    self.layout()
  
  def layout(self):
    count = len(self.subviews)
    if count == 0: return
    for view in self.subviews:
      C.remove_constraints(view)
    subviews = iter(self.subviews)
    count_x, count_y = self.dimensions(count)
    dim = min(self.width/count_x, 
              self.height/count_y)
    self_c = C(C.create_guide(self))
    self_c.width == count_x * dim
    self_c.height == count_y * dim
    self_c.dock_center()
    
    cells = defaultdict(list)
    #self_c = C(self)
    for row in range(count_y):
      for col in range(count_x):
        try:
          cell = subviews.__next__()
        except StopIteration:
          break
        cell_c = C(cell)
        cells[row].append(cell_c)
        
        if row == 0 and col == 0:
          cell_c.width == dim
          cell_c.height == dim
        
        if row == 0:
          cell_c.top >= self_c.top_margin

        if row == count_y - 1:
          cell_c.bottom <= self_c.bottom_margin

        if col == 0:
          cell_c.leading >= self_c.leading_margin

        if col == count_x - 1:
          cell_c.trailing <= self_c.trailing_margin

        if row > 0 or col > 0:
          cell_c.width == cells[0][0].width
          cell_c.height == cells[0][0].height

        if col > 0:
          cell_c.leading >= cells[row][col - 1].trailing_padding

        if row > 0:
          cell_c.top >= cells[row - 1][col].bottom_padding

  def dimensions(self, count):
    ratio = self.width/self.height
    count_x = math.sqrt(count * self.width/self.height)
    count_y = math.sqrt(count * self.height/self.width)
    operations = (
      (math.floor, math.floor),
      (math.floor, math.ceil),
      (math.ceil, math.floor),
      (math.ceil, math.ceil)
    )
    best = None
    best_x = None
    best_y = None
    for oper in operations:
      cand_x = oper[0](count_x)
      cand_y = oper[1](count_y)
      diff = cand_x*cand_y - count
      if diff >= 0:
        if best is None or diff < best:
          best = diff
          best_x = cand_x
          best_y = cand_y         
    return (best_x, best_y)


class Dashboard(asyncui.AsyncUIView):
  
  def __init__(self, **kwargs):
    super().__init__(**kwargs)
    self.grid_view = GridView(
      frame=self.bounds,
      flex='WH')
    self.grid_view.touch_enabled = False
    self.add_subview(self.grid_view)
    C(self.grid_view).dock_all(fit=C.SAFE)
    self.touch_enabled = True
    self.create_cards()
    self.token = None
    
  def create_cards(self):
    self.temperature = self.create_card('Lämpötila °C')
    self.forecast = self.create_card('Ennuste °C')
    self.odometer = self.create_card('Matkamittari km')
    self.range = self.create_card('Kantama KM')
    self.power_available = self.create_card('Latausjohto')
    self.charge_level = self.create_card('Varaus')
    self.doors = self.create_card('Lukitus')
    self.heating = self.create_card('Lämmitys')
    
  def create_card(self, title, image=False):
    card = View(background_color='#6b95ff')
    self.grid_view.add_subview(card)
    card_c = C(card)
    title_view = Label(
      name='title',
      text=title.upper(),
      text_color='white',
      font=('Futura', 10))
    card.add_subview(title_view)
    title_view_c = C(title_view)
    title_view_c.dock_bottom_trailing()
    if image:
      content_view = ImageView(name='content', image=Image('iow:more_256'),
      hidden=True)
      share=.3
    else:
      content_view = Label(
        name='content', 
        text='...',
        text_color='white',
        font=('Futura', 32),
        alignment=ALIGN_CENTER,
        hidden=True)
      share=.9
      #C(content_view).fit()
    card.add_subview(content_view)
    content_c = C(content_view)
    content_c.center_x == card_c.center_x
    content_c.center_y == card_c.center_y * 1.25
    content_c.width == card_c.width * share
    '''
    placeholder = ImageView(
      name='placeholder', 
      image=Image('iow:more_256'))
    card.add_subview(placeholder)
    C(placeholder).dock_center(share=.3)
    '''
    return card
    
  def reveal(self, card, text=None, image=None):
    content = card['content']
    if text:
      content.text = text
    elif image:
      content.image = Image(image)
    content.hidden = False
    #card['placeholder'].hidden = True
    
  def touch_ended(self, touch):
    self.grid_view.add_subview(
      Label(
        text=str(len(self.grid_view.subviews)+1),
        background_color='#6b95ff',
        text_color='white',
        alignment=ALIGN_CENTER))
    
  icon_map = {
    'clear-day': 'iow:ios7_sunny_outline_256', 
    'clear-night': 'iow:ios7_moon_outline_256',
    'rain': 'iow:ios7_rainy_outline_256', 
    'snow': 'iow:ios7_rainy_256', 
    'sleet': 'iow:ios7_rainy_outline_256', 
    'wind': 'iow:ios7_rewind_outline_256', 
    'fog': 'iow:drag_256',
    'cloudy': 'iow:ios7_cloud_outline_256', 
    'partly-cloudy-day': 'iow:ios7_partlysunny_256',
    'partly-cloudy-night': 'iow:ios7_partlysunny_outline_256'
  }
    
  async def get_forecast(self):
    key = darksky_conf['api_key']
    latitude = darksky_conf['latitude']
    longitude = darksky_conf['longitude']
    url = f'https://api.darksky.net/forecast/{key}/{latitude},{longitude}?units=si'
    result = await self.get(url)
    data = json.loads(result)
    today = data['daily']['data'][0]
    low = round(today['apparentTemperatureLow'])
    high = round(today['apparentTemperatureHigh'])
    icon_name = today['icon']
    
    self.reveal(self.forecast, text=f'{low}/{high}')

    weather_icon = ImageView(
      name='icon', image=Image(self.icon_map.get(icon_name, 'iow:ios7_close_outline_256')),
      hidden=True)
    self.forecast.add_subview(weather_icon)
    C(weather_icon).dock_top_leading(share=.35)
    weather_icon.hidden = False
    
  async def get_car_data(self):
    if self.token is None:
      await self.carnet_logon()
    self.call_soon(self.get_status())
    self.call_soon(self.get_heat_related())
    self.call_soon(self.get_charge_data())
    
  # Fake the VW CarNet mobile app headers
  HEADERS = {
    'Accept': 'application/json',
    'X-App-Name': 'eRemote',
    'X-App-Version': '1.0.0',
    'User-Agent': 'okhttp/2.3.0'
  }

  async def carnet_logon(self):
    r = await self.post(
      'https://msg.volkswagen.de/fs-car/core/auth/v1/VW/DE/token',
      data = {
        'grant_type':'password',
        'username': CARNET_USERNAME,
        'password': CARNET_PASSWORD }, headers=self.HEADERS)
    responseData = json.loads(r)
    self.token = responseData.get("access_token")
    self.HEADERS["Authorization"] = "AudiAuth 1 " + self.token
    
  async def get_heat_related(self):
    r = await self.get(
      'https://msg.volkswagen.de/fs-car/bs/climatisation/v1/VW/DE/vehicles/' + VIN + '/climater',
      headers=self.HEADERS)
    responseData = json.loads(r)
    
    try:
      temperature = responseData.get("climater").get("status").get("temperatureStatusData").get("outdoorTemperature").get("content")
      temperature = str(temperature)[:3] + "." + str(temperature)[3:]
      temperature = float(temperature)-273
    except: temperature = 0
    self.reveal(self.temperature, str(round(temperature)))
    
    climate_heating_status = responseData.get("climater").get("status").get("climatisationStatusData").get("climatisationState").get("content")
    self.reveal(self.heating, str(climate_heating_status.upper()))
    
  async def get_status(self):
    r = await self.get(
      'https://msg.volkswagen.de/fs-car/bs/vsr/v1/VW/DE/vehicles/' + VIN + '/status',
      headers=self.HEADERS)
    responseData = json.loads(r)
    
    try:
      mileage = responseData.get("StoredVehicleDataResponse").get("vehicleData").get("data")[1].get("field")[0].get("value")
    except: mileage = 0
    self.reveal(self.odometer, str(mileage))
    
    try:
      doors = responseData.get("StoredVehicleDataResponse").get("vehicleData").get("data")[7].get("field")[0].get('textId')
    except: doors = 'Unknown'
    self.reveal(self.doors, 'OK' if doors == 'door_locked' else 'AUKI')
    
  async def get_charge_data(self):
    r = await self.get(
      'https://msg.volkswagen.de/fs-car/bs/batterycharge/v1/VW/DE/vehicles/' + VIN + '/charger',
      headers=self.HEADERS)
    responseData = json.loads(r)
    
    try:
      external_power_supply_state = responseData.get("charger").get("status").get("chargingStatusData").get("externalPowerSupplyState").get("content")
    except: external_power_supply_state = 'Unknown'
    self.reveal(self.power_available, 'OK' if external_power_supply_state == 'available' else 'IRTI')
    
    try:
      charge = responseData.get("charger").get("status").get("batteryStatusData").get("stateOfCharge").get("content")
    except: charge = 0
    self.reveal(self.charge_level, 
      str(charge)+'%')
      
    try:
      primary_engine_range = responseData.get("charger").get("status").get("cruisingRangeStatusData").get("primaryEngineRange").get("content")
    except: primary_engine_range = 0
    self.reveal(self.range, 
      str(primary_engine_range))
      
    
v = Dashboard(background_color='black')
v.present('full_screen', hide_title_bar=True)
v.call_soon(v.get_forecast())
v.call_soon(v.get_car_data())
v.start_loop()



