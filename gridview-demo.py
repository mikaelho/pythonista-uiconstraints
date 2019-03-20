from ui import *
from lightanchor import *

def style(view):
  view.background_color='white'
  view.border_color = 'black'
  view.border_width = 1
  view.text_color = 'black'
  view.tint_color = 'black'
  
def create_card(title, packing):
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

demo.add_subview(create_card('CENTER', GridView.CENTER))
demo.add_subview(create_card('FILL', GridView.FILL))
demo.add_subview(create_card('START', GridView.START))
demo.add_subview(create_card('END', GridView.END))
demo.add_subview(create_card('SIDES', GridView.SIDES))
demo.add_subview(create_card('SPREAD', GridView.SPREAD))
demo.add_subview(create_card('START_SPREAD', GridView.START_SPREAD))
demo.add_subview(create_card('END_SPREAD', GridView.END_SPREAD))

v.present()
