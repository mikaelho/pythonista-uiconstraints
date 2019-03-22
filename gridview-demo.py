from ui import *
from anchor import *

def style(view):
  view.background_color='white'
  view.border_color = 'black'
  view.border_width = 1
  view.text_color = 'black'
  view.tint_color = 'black'
  
def create_card(title, packing, count):
  card = View()
  style(card)
  label = Label(
    text=title,
    font=('Apple SD Gothic Neo', 12),
    alignment=ALIGN_CENTER)
  card.add_subview(label)
  label.dock.fit()
  label.dock.top()
  gv = GridView(
    #count_y=1,
    pack_x=packing)
  style(gv)
  card.add_subview(gv)
  gv.dock.bottom()
  gv.at.top == label.at.bottom_padding
  for _ in range(7):
    v = View()
    style(v)
    gv.add_subview(v)
  return card
    
v = View()
    
demo = GridView(background_color='white')
v.add_subview(demo)
demo.dock.all(fit=Dock.SAFE)

cards = (
  ('CENTER', GridView.CENTER),
  ('FILL', GridView.FILL),
  ('START', GridView.START),
  ('END', GridView.END),
  ('SIDES', GridView.SIDES),
  ('SPREAD', GridView.SPREAD),
  ('START_SPREAD', GridView.START_SPREAD),
  ('END_SPREAD', GridView.END_SPREAD) 
)

for i, spec in enumerate(cards):
  demo.add_subview(create_card(spec[0], spec[1], i))

v.present()
