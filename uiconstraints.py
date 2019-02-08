#coding: utf-8
from objc_util import *
import ui, console
from types import SimpleNamespace
from copy import copy
import random, math
from collections import defaultdict

NSLayoutConstraint = ObjCClass('NSLayoutConstraint')
UILayoutGuide = ObjCClass('UILayoutGuide')
UIDevice = ObjCClass('UIDevice')

class Constrain:
  
  def __init__(self, view, priority=1000):
    '''Initialize a constraint manager for a view with the given priority.'''
    
    self.view = view
    self.attribute = None
    self.operator = 0
    self.other_view = None
    self.other_attribute = 0
    self.multiplier = 1
    self._constant = 0
    self._priority = priority
    self.objc_constraint = None
    
  @property
  def constant(self):
    '''Constant part of the constraint equation:
      `target.attribute == source.attribute * multiplier + constant`.
    This is the only part of the equation that can be changed
    after the constraint has been created.'''
    return self._constant
    
  @constant.setter
  def constant(self, value):
    self._constant = value
    if self.objc_constraint:
      self.objc_constraint.setConstant_(value)
    
  def __str__(self):
    operators = ['<=', '==', '>=']
    
    view = self.view.name if self.view.name else type(self.view).__name__
    
    attribute = Constrain.characteristics[self.attribute][3]
    
    operator = operators[self.operator + 1]
    
    other_view = self.other_view.name if \
    self.other_view and self.other_view.name\
    else type(self.other_view).__name__
    
    other_attribute = Constrain.characteristics[self.other_attribute][3]
    
    return (f'{view}.{attribute} {operator} '
    f'{other_view}.{other_attribute} '
    f'* {self.multiplier} + {self.constant}')
    
  # CONSTRAINT OPERATORS
    
  def __mul__(self, other):
    self.multiplier *= other
    return self
    
  def __truediv__(self, other):
    self.multiplier *= 1/other
    return self
    
  def __add__(self, other):
    self._constant += other
    return self
    
  def __sub__(self, other):
    self._constant -= other
    return self
    
  def __le__(self, other):
    c = copy(self)
    c.operator = -1
    c._create_constraint(other)
    return c
    
  def __eq__(self, other):
    c = copy(self)
    c.operator = 0
    c._create_constraint(other)
    return c
    
  def __ge__(self, other):
    c = copy(self)
    c.operator = 1
    c._create_constraint(other)
    return c
    
  #docgen: Anchors
    
  @property
  def _no_attribute(self):
    c = copy(self)
    c.attribute = 0
    return c
    
  @property
  def left(self):
    'The left side of the object’s alignment rectangle.'
    c = copy(self)
    c.attribute = 1
    return c
    
  @property
  def right(self):
    'The right side of the object’s alignment rectangle.'
    c = copy(self)
    c.attribute = 2
    return c
    
  @property
  def top(self):
    'The top of the object’s alignment rectangle.'
    c = copy(self)
    c.attribute = 3
    return c
    
  @property
  def bottom(self):
    'The bottom of the object’s alignment rectangle.'
    c = copy(self)
    c.attribute = 4
    return c
    
  @property
  def leading(self):
    '''The leading edge of the object’s alignment rectangle.
    Same as `left` for left-to-right languages.'''
    c = copy(self)
    c.attribute = 5
    return c
    
  @property
  def trailing(self):
    '''The trailing edge of the object’s alignment rectangle.
    Same as `right` for left-to-right languages.'''
    c = copy(self)
    c.attribute = 6
    return c
    
  @property
  def width(self):
    c = copy(self)
    c.attribute = 7
    return c
    
  @property
  def height(self):
    c = copy(self)
    c.attribute = 8
    return c
    
  @property
  def center_x(self):
    c = copy(self)
    c.attribute = 9
    return c
    
  @property
  def center_y(self):
    c = copy(self)
    c.attribute = 10
    return c
    
  @property
  def last_baseline(self):
    c = copy(self)
    c.attribute = 11
    return c
    
  @property
  def first_baseline(self):
    c = copy(self)
    c.attribute = 12
    return c
    
  @property
  def left_margin(self):
    c = copy(self)
    c.attribute = 13
    return c
    
  @property
  def right_margin(self):
    c = copy(self)
    c.attribute = 14
    return c
    
  @property
  def top_margin(self):
    c = copy(self)
    c.attribute = 15
    return c
    
  @property
  def bottom_margin(self):
    c = copy(self)
    c.attribute = 16
    return c
    
  @property
  def leading_margin(self):
    c = copy(self)
    c.attribute = 17
    return c
    
  @property
  def trailing_margin(self):
    c = copy(self)
    c.attribute = 18
    return c
    
  @property
  def left_padding(self):
    c = copy(self)
    c.attribute = 1
    c._constant -= c.margin_inset().leading
    return c
    
  @property
  def right_padding(self):
    c = copy(self)
    c._constant += c.margin_inset().trailing
    c.attribute = 2
    return c
    
  @property
  def top_padding(self):
    c = copy(self)
    c.attribute = 3
    c._constant -= c.margin_inset().top
    return c
    
  @property
  def bottom_padding(self):
    c = copy(self)
    c.attribute = 4
    c._constant += c.margin_inset().bottom
    return c
    
  @property
  def leading_padding(self):
    c = copy(self)
    c.attribute = 5
    c._constant -= c.margin_inset().leading
    return c
    
  @property
  def trailing_padding(self):
    c = copy(self)
    c.attribute = 6
    c._constant += c.margin_inset().trailing
    return c
    
  #Section: CONSTRAINT MANIPULATION
    
  @property
  def priority(self):
    "Note: Cannot change priority between required and optional after present()."
    if self.objc_constraint:
      return objc_constraint.priority()
      
  @priority.setter
  def priority(self, value):
    if type(value) is not int or value < 0 or value > 1000:
      raise ValueError('priority must be an integer in the range [0, 1000]')
    if self.objc_constraint:
      previous_value = self.objc_constraint.priority()
      if self.view.on_screen and \
      ((value == 1000 and \
        previous_value != 1000) or \
      (value != 1000 and \
        previous_value == 1000)):
        raise ValueError(
          'Cannot change priority value between required (1000) and lower value')
      self.objc_constraint.setPriority_(value)
      
  @property
  def active(self):
    if self.objc_constraint:
      return self.objc_constraint.isActive()

  @classmethod
  def constraints_by_attribute(cls, view, attribute, active_only=True):
    constraints = getattr(view, 'layout_constraints', [])
    result = []
    for constraint in constraints:
      if active_only and not constraint.active:
        continue
      if attribute == cls.characteristics[constraint.attribute][0]:
        result.append(constraint)
    return result
        
  @classmethod
  def remove_constraints(cls, view):
    if hasattr(view, 'layout_constraints'):
      cls.remove(view.layout_constraints)
      
  @classmethod
  def remove(cls, *constraints):
    for constraint in constraints:
      if type(constraint) in (tuple, list):
        if len(constraint) == 0: return
        Constrain.remove(*(constraint.copy()))
      else:
        constraint.objc_constraint.setActive_(False)
        constraint.view.layout_constraints.remove(constraint)
    
  # LAYOUT GUIDES
    
  @property
  def safe_area(self):
    self.view = SimpleNamespace(
      objc_instance=self.view.objc_instance.safeAreaLayoutGuide(),
      name='Safe area',
      superview=self.view)
    return self
    
  @property
  def margins(self):
    self.view = SimpleNamespace(
      objc_instance=self.view.objc_instance.layoutMarginsGuide(),
      name='Margins',
      superview=self.view)
    return self
    
  @classmethod
  def create_guide(cls, view):
    class Guide(SimpleNamespace):
      @property
      def superview(self):
        if self.view:
          return self.view.superview
          
      @property
      def subviews(self):
        if self.view:
          return self.view.subviews
      
    guide = UILayoutGuide.new().autorelease()
    view.objc_instance.addLayoutGuide_(guide)
    return Guide(objc_instance=guide, view=view, name='LayoutGuide')

  def margin_inset(self):
    m = self.view.objc_instance.directionalLayoutMargins()
    return SimpleNamespace(bottom=m.a, leading=m.b, trailing=m.c, top=m.d)
    
  @property
  def superview(self):
    if self.view:
      return self.view.superview
      
  @property
  def subviews(self):
    if self.view:
      return self.view.subviews
    
  #docgen: Convenience layout functions
    
  extra_width_types = [ui.Label, ui.Button]
    
  def fit(self):
    'Set size constraints according to the views preferred size.'
    view = self.view
    size = view.objc_instance.sizeThatFits_((0,0))
    extra_width = 0
    if type(view) in self.extra_width_types:
      margins = self.margin_inset()
      extra_width = margins.leading + margins.trailing
    (Constrain(view).width == size.width + extra_width) #.priority = 1
    (Constrain(view).height == size.height) #.priority = 1
    return self
    
  TIGHT = 0
  MARGIN = 1
  SAFE = 2
  default_fit = MARGIN

  def _fit(self, fit):
    s = self.superview
    if fit == Constrain.TIGHT:
      return Constrain(s)
    elif fit == Constrain.MARGIN:
      return Constrain(s).margins
    elif fit == Constrain.SAFE:
      return Constrain(s).safe_area
    
  def dock_all(self, constant=0, fit=default_fit):
    'Dock the view on all sides.'
    view = self.view
    self.top == self._fit(fit).top + constant
    self.bottom == self._fit(fit).bottom - constant
    self.leading == self._fit(fit).leading + constant
    self.trailing == self._fit(fit).trailing - constant
    
  def dock_center(self, share=None):
    s = Constrain(self.superview)
    self.center_x == s.center_x
    self.center_y == s.center_y
    self._set_size(share)
  
  def dock_sides(self, share=None, constant=0, fit=default_fit):
    self.leading == self._fit(fit).leading + constant
    self.trailing == self._fit(fit).trailing - constant
    self._set_size(share)
    
  dock_horizontal = dock_sides
  
  def dock_horizontal_between(self, top_view, bottom_view, constant=0, fit=default_fit):
    self.dock_horizontal(constant=constant, fit=fit)
    
    top_c = Constrain(top_view)
    bottom_c = Constrain(bottom_view)
    if fit == Constrain.TIGHT:
      self.top == top_c.bottom + constant
      self.bottom == bottom_c.top + constant
    else:
      self.top == top_c.bottom_padding + constant
      self.bottom == bottom_c.top_padding + constant
    
  def dock_vertical(self, constant=0, fit=default_fit):
    self.top == self._fit(fit).top + constant
    self.bottom == self._fit(fit).bottom - constant
    
  def dock_vertical_between(self, leading_view, trailing_view, constant=0, fit=default_fit):
    self.dock_vertical(constant, fit)
    if fit == Constrain.TIGHT:
      self.leading == Constrain(leading_view).trailing + constant
      self.trailing == Constrain(trailing_view).leading + constant
    elif fit == Constrain.MARGIN:
      self.leading == Constrain(leading_view).trailing_padding + constant
      self.trailing == Constrain(trailing_view).leading_padding + constant
    
  def _set_size(self, share):
    if share is not None:
      share_x, share_y = share if type(share) in (list, tuple) else (share, share)
      s = Constrain(self.superview)
      self.width == s.width * share_x
      self.height == s.height * share_y
    
  def dock_top(self, share=None, constant=0, fit=default_fit):
    self.top == self._fit(fit).top + constant
    self.leading == self._fit(fit).leading + constant
    self.trailing == self._fit(fit).trailing - constant
    if share is not None:
      
      self.height == Constrain(self.superview).height * share
  
  def dock_bottom(self, share=None, constant=0, fit=default_fit):
    self.bottom == self._fit(fit).bottom - constant
    self.leading == self._fit(fit).leading + constant
    self.trailing == self._fit(fit).trailing - constant
    if share is not None:
      
      self.height == Constrain(self.superview).height * share
    
  def dock_leading(self, share=None, constant=0, fit=default_fit):
    self.leading == self._fit(fit).leading + constant
    self.top == self._fit(fit).top + constant
    self.bottom == self._fit(fit).bottom - constant
    if share is not None:
      
      self.width == Constrain(self.superview).width * share
    
  def dock_trailing(self, share=None, constant=0, fit=default_fit):
    self.trailing == self._fit(fit).trailing - constant
    self.top == self._fit(fit).top + constant
    self.bottom == self._fit(fit).bottom - constant
    if share is not None:
      
      self.width == Constrain(self.superview).width * share
    
  def dock_top_leading(self, share=None, constant=0, fit=default_fit):
    self.top == self._fit(fit).top + constant
    self.leading == self._fit(fit).leading + constant
    self._set_size(share)
    
  def dock_top_trailing(self, share=None, constant=0, fit=default_fit):
    self.top == self._fit(fit).top + constant
    self.trailing == self._fit(fit).trailing - constant
    self._set_size(share)
    
  def dock_bottom_leading(self, share=None, constant=0, fit=default_fit):
    self.bottom == self._fit(fit).bottom - constant
    self.leading == self._fit(fit).leading + constant
    self._set_size(share)

  def dock_bottom_trailing(self, share=None, constant=0, fit=default_fit):
    self.bottom == self._fit(fit).bottom - constant
    self.trailing == self._fit(fit).trailing - constant
    self._set_size(share)
    
  # INTERNALS
    
  position = 0
  size = 1
  horizontal = 0
  vertical = 1
  na = -1
  absolute = 0
  relative = 1
        
  characteristics = {
    0: (_no_attribute, size, na, 'no_attribute'),
    1: (left, position, horizontal, 'left', absolute),
    2: (right, position, horizontal, 'right', absolute),
    3: (top, position,vertical, 'top', na),
    4: (bottom, position, vertical, 'bottom', na),
    5: (leading, position, horizontal, 'leading', relative),
    6: (trailing, position, horizontal, 'trailing', relative),
    7: (width, size, horizontal, 'width', na),
    8: (height, size, vertical, 'height', na),
    9: (center_x, position, horizontal, 'center_x', na),
    10: (center_y, position, vertical, 'center_y', na),
    11: (last_baseline, position, vertical, 'last_baseline', na),
    12: (first_baseline, position, vertical, 'first_baseline', na),
    13: (left_margin, position, horizontal, 'left_margin', absolute),
    14: (right_margin, position, horizontal, 'right_margin', absolute),
    15: (top_margin, position, vertical, 'top_margin', absolute),
    16: (bottom_margin, position, vertical, 'bottom_margin', absolute),
    17: (leading_margin, position, horizontal, 'leading_margin', relative),
    18: (trailing_margin, position, horizontal, 'trailing_margin', relative)
  }
    
  @on_main_thread
  def _create_constraint(self, other):
    if isinstance(other, Constrain):
      self.other_view = other.view
      self.other_attribute = other.attribute
      self.constant = other.constant
      self.multiplier = other.multiplier
    elif isinstance(other, (int, float)):
      self.constant = other
    else:
      raise TypeError(
        f'Cannot use object of type {str(type(other))} in a constraint comparison: ' + 
        str(self))
    
    a = Constrain.characteristics[self.attribute]
    b = Constrain.characteristics[self.other_attribute]
    
    if a[1] == Constrain.position and (
      self.multiplier == 0 or
      self.other_view == None or 
      self.other_attribute == 0):
      raise AttributeError(
        'Location constraints cannot relate to a constant only: ' + str(self))
    
    if a[1] != b[1]:
      raise AttributeError(
        'Constraint cannot relate location and size attributes: ' + str(self))
      
    if a[1] == b[1] == Constrain.position and a[2] != b[2]:
      raise AttributeError(
        'Constraint cannot relate horizontal and vertical location attributes: '\
        + str(self))
        
    if (a[4] == Constrain.relative and b[4] == Constrain.absolute) or \
    (a[4] == Constrain.absolute and b[4] == Constrain.relative):
      raise AttributeError(
        'Constraint cannot relate absolute and relative edge attributes: '\
        + str(self))
    
    try:
      view_first_seen = \
      self.view.objc_instance.translatesAutoresizingMaskIntoConstraints()
    except AttributeError:
      view_first_seen = False
    if view_first_seen: 
      self.view.objc_instance.setTranslatesAutoresizingMaskIntoConstraints_(False)
      #C._set_defaults(self.view)
      #if type(self.view) in C.autofit_types:
      #self.size_to_fit()
      
    layout_constraints = getattr(self.view, 'layout_constraints', [])
    layout_constraints.append(self)
    self.view.layout_constraints = layout_constraints
    
    self.objc_constraint = NSLayoutConstraint.\
    PG_constraintWithItem_attribute_relatedBy_toItem_attribute_multiplier_constant_priority_(
      self.view.objc_instance,
      self.attribute,
      self.operator,
      None if not self.other_view else self.other_view.objc_instance,
      self.other_attribute,
      self.multiplier,
      self.constant,
      self._priority
    )
    
    self.objc_constraint.setActive_(True)
    
  #docgen: Device information
  
  @classmethod
  def horizontal_size_class(cls):
    return 'constrained' if cls.is_phone() and cls.is_portrait() else 'regular'
    
    # This does not currently work on
    # iPhone X iOS 12.1.3:
    #return ['constrained', 'regular'][UIApplication.sharedApplication().\
    #keyWindow().traitCollection().\
    #horizontalSizeClass() - 1]
    
  @classmethod
  def vertical_size_class(cls):
    return ['constrained', 'regular'][UIApplication.sharedApplication().\
    keyWindow().traitCollection().\
    verticalSizeClass() - 1]
  
  @classmethod
  def is_portrait(cls):
    "Returns true if the device thinks it is in portrait orientation."
    w, h = ui.get_screen_size()
    return w < h
  
  @classmethod
  def is_landscape(cls):
    "Returns true if the device thinks it is in landscape orientation."
    w, h = ui.get_screen_size()
    return w > h
  
  @classmethod
  def is_phone(cls):
    "Returns true if the device is a phone-type device."
    return UIApplication.sharedApplication().keyWindow().traitCollection().\
    userInterfaceIdiom() == 0
    
  @classmethod
  def is_pad(cls):
    "Returns true if the device is a pad-type device."
    return UIApplication.sharedApplication().keyWindow().traitCollection().\
    userInterfaceIdiom() == 1
    
  @classmethod
  def is_width_constrained(cls):
    '''Returns true if the display is relatively narrow in the current orientation
    (e.g. phone in the portrait orientation).'''
    return cls.horizontal_size_class() == 'constrained'
    
  @classmethod
  def is_width_regular(cls):
    '''Returns true if the display is relatively wide in the current orientation
    (e.g. phone in the landscape orientation, or an iPad in any orientation).'''
    return cls.horizontal_size_class() == 'regular'
    
  @classmethod
  def is_height_constrained(cls):
    '''Returns true if the display is relatively small in the vertical direction
    (e.g. phone in the landscape orientation).'''
    return cls.vertical_size_class() == 'constrained'
    
  @classmethod
  def is_height_regular(cls):
    '''Returns true if the display is relatively tall in the current orientation
    (e.g. phone held in the portrait orientation, or an iPad in any orientation).'''
    return cls.vertical_size_class() == 'regular'


  class GridView(View):
    'Places subviews as squares that optimally fill the available space.'
    
    def __init__(self, place=Constrain.dock_center, **kwargs):
      super().__init__(**kwargs)
      self.place = place
    
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
      self.place(self_c)
      
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
    

  class DiagnosticOverlay(ui.View):
    
    class ConnectorOverlay(ui.View):
      
      def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.touch_enabled = False
      
      def draw(self):
        for (marker, other_marker, color) in self.superview.connectors:
          pos1 = marker.center
          pos2 = other_marker.center
          path = ui.Path()
          path.move_to(pos1.x, pos1.y)
          path.line_to(pos2.x, pos2.y)
          ui.set_color(color)
          path.stroke()
          
          
    class AnchorMarker(ui.View):
      
      def __init__(self, color, constraint_str, **kwargs):
        super().__init__(**kwargs)
        self.background_color = color
        self.border_width = 1
        self.border_color = 'white'
        self.text = constraint_str
        
      def touch_ended(self, touch):
        console.alert(self.text)
        
    
    def __init__(self, root, start=None, **kwargs):
      self.start = start or root
      super().__init__(
        frame=root.bounds, flex='WH', 
        background_color=(1,1,1,0.7), 
        **kwargs)
      root.add_subview(self)
      self.connectors = []
      self.add_overlay(start or root)
      self.add_subview(type(self).ConnectorOverlay(frame=self.bounds, flex='WH'))
      
    def collect_views(self, view):
      if type(view) is SimpleNamespace:
        return []
      local_list = [view] if hasattr(view, 'layout_constraints') else []
      for subview in view.subviews:
        if hasattr(subview, 'layout_constraints'):
          local_list += self.collect_views(subview)
      return local_list
      
    def add_overlay(self, first_view):
      ''' Displays the active constraints for first_view and all of its subviews
      as an overlay on the current UI.'''
      cls = Constrain
      palette = []
      process_queue = self.collect_views(first_view)
      for view in process_queue:

        if len(palette) == 0:
          palette = cls.DiagnosticOverlay._marker_palette.copy()
          random.shuffle(palette)
        colors = palette.pop()
        for constraint in view.layout_constraints:
          a = cls.characteristics[constraint.attribute][3]
          color = colors[cls.DiagnosticOverlay._color_per_attribute[a]]
          marker = cls.DiagnosticOverlay.AnchorMarker(
            color,
            str(constraint))
          self.add_subview(marker)
          self._place_anchor_marker(
            constraint.view, 
            constraint.attribute,
            color, marker)
          if constraint.other_view is not None:
            other_marker = cls.DiagnosticOverlay.AnchorMarker(
              color,
              str(constraint))
            self.add_subview(other_marker)
            self._place_anchor_marker(
              constraint.other_view, 
              constraint.other_attribute, 
              color, other_marker)
            
            self.connectors.append((marker, other_marker, color))
     
    def _place_anchor_marker(self, view, attribute, color, marker): #, other_marker=None):
      if view is None: return 
      cls = Constrain
      thickness = 5
      share = 0.75
      marker_size = 20
      a = cls.characteristics[attribute][3]
      marker_c = cls(marker)
      view_c = cls(view)
      #if other_marker:
      #  other_marker_c = cls(other_marker)
        
      if a == 'left':
        marker_c.center_x == view_c.left
        #if not other_marker:
        marker_c.center_y == view_c.center_y
        #else:
        #  marker_c.center_y == other_marker_c.center_y
        marker_c.width == thickness
        marker_c.height == marker_size
      elif a == 'right':
        marker_c.center_x == view_c.right
        marker_c.center_y == view_c.center_y
        #if not other_marker:
        marker_c.center_y == view_c.center_y
        #else:
        #  marker_c.center_y == other_marker_c.center_y
        marker_c.width == thickness
        marker_c.height == view_c.height * share
      elif a == 'top':
        marker_c.center_x == view_c.center_x
        marker_c.center_y == view_c.top
        marker_c.height == thickness
        marker_c.width == view_c.width * share
      elif a == 'bottom':
        marker_c.center_x == view_c.center_x
        marker_c.center_y == view_c.bottom
        marker_c.height == thickness
        marker_c.width == view_c.width * share
      elif a == 'leading':
        marker_c.center_x == view_c.leading
        marker_c.center_y == view_c.center_y
        marker_c.width == thickness
        marker_c.height == view_c.height * share
      elif a == 'trailing':
        marker_c.center_x == view_c.trailing
        marker_c.center_y == view_c.center_y
        marker_c.width == thickness
        marker_c.height == view_c.height * share
      elif a == 'width':
        marker_c.center_x == view_c.center_x
        marker_c.center_y == view_c.center_y
        marker_c.height == thickness
        marker_c.width == view_c.width
      elif a == 'height':
        marker_c.center_x == view_c.center_x
        marker_c.center_y == view_c.center_y
        marker_c.width == thickness
        marker_c.height == view_c.height
      elif a == 'center_x':
        marker_c.center_x == view_c.center_x
        marker_c.center_y == view_c.center_y
        marker_c.width == thickness
        marker_c.height == view_c.height * share
      elif a == 'center_y':
        marker_c.center_x == view_c.center_x
        marker_c.center_y == view_c.center_y
        marker_c.height == thickness
        marker_c.width == view_c.width * share
      elif a == 'last_baseline':
        marker_c.center_x == view_c.center_x
        marker_c.center_y == view_c.last_baseline
        marker_c.height == thickness
        marker_c.width == view_c.width * share
      elif a == 'first_baseline':
        marker_c.center_x == view_c.center_x
        marker_c.center_y == view_c.first_baseline
        marker_c.height == thickness
        marker_c.width == view_c.width * share
      elif a == 'left_margin':
        marker_c.center_x == view_c.left_margin
        marker_c.center_y == view_c.center_y
        marker_c.width == thickness
        marker_c.height == view_c.height * share
      elif a == 'right_margin':
        marker_c.center_x == view_c.right_margin
        marker_c.center_y == view_c.center_y
        marker_c.width == thickness
        marker_c.height == view_c.height * share
      elif a == 'top_margin':
        marker_c.center_x == view_c.center_x
        marker_c.center_y == view_c.top_margin
        marker_c.height == thickness
        marker_c.width == view_c.width * share
      elif a == 'bottom_margin':
        marker_c.center_x == view_c.center_x
        marker_c.center_y == view_c.bottom_margin
        marker_c.height == thickness
        marker_c.width == view_c.width * share
      elif a == 'leading_margin':
        marker_c.center_x == view_c.leading_margin
        marker_c.center_y == view_c.center_y
        marker_c.width == thickness
        marker_c.height == view_c.height * share
      elif a == 'trailing_margin':
        marker_c.center_x == view_c.trailing_margin
        marker_c.center_y == view_c.center_y
        marker_c.width == thickness
        marker_c.height == view_c.height * share
      
    _marker_palette = [
      ['#2196F3', '#1976D2', '#EF5350'],
      ['#03A9F4', '#039BE5', '#FFC107'],
      ['#03A9F4', '#64B5F6', '#FF80AB'],
      ['#00BCD4', '#4DD0E1', '#FDD835'],
      ['#00BCD4', '#00ACC1', '#FFA726'],
      ['#3F51B5', '#5C6BC0', '#FFC107'],
      ['#673AB7', '#512DA8', '#2196F3'],
      ['#9C27B0', '#BA68C8', '#FFCA28'],
      ['#673AB7', '#9575CD', '#2196F3'],
      ['#F44336', '#FF5252', '#FFA726'],
      ['#F44336', '#E53935', '#FDD835'],
      ['#E91E63', '#F06292', '#42A5F5'],
      ['#FF5722', '#FF6E40', '#FBC02D'],
      ['#FF5722', '#E64A19', '#3F51B5'],
      ['#FF9800', '#FB8C00', '#F44336'],
      ['#FF9800', '#FFB74D', '#29B6F6'],
      ['#FFC107', '#FFA000', '#26C6DA'],
      ['#FFC107', '#FFD54F', '#4FC3F7'],
      ['#CDDC39', '#C0CA33', '#009688'],
      ['#8BC34A', '#9CCC65', '#FF8A65'],
      ['#CDDC39', '#689F38', '#FFD740'],
      ['#4CAF50', '#66BB6A', '#FFC107'],
      ['#009688', '#00897B', '#4DD0E1'],
      ['#009688', '#80CBC4', '#FDD835'],
      ['#607D8B', '#455A64', '#FDD835'],
      ['#607D8B', '#37474F', '#F06292'],
      ['#9E9E9E', '#757575', '#42A5F5'],
      ['#9E9E9E', '#BDBDBD', '#FF7043'],
      ['#795548', '#A1887F', '#FFCA28'],
      ['#795548', '#5D4037', '#4CAF50'],
    ]
    
    _edges = 0
    _baselines = 0
    _size = 1
    
    _color_per_attribute = {
      'left': _edges,
      'right': _edges,
      'top': _edges,
      'bottom': _edges,
      'leading': _edges,
      'trailing': _edges,
      'width': _size,
      'height': _size,
      'center_x': _baselines,
      'center_y': _baselines,
      'last_baseline': _baselines,
      'first_baseline': _baselines,
      'left_margin': _edges,
      'right_margin': _edges,
      'top_margin': _edges,
      'bottom_margin': _edges,
      'leading_margin': _edges,
      'trailing_margin': _edges,
    }
      

if __name__ == '__main__':
  
  import ui
  import scripter
  
  class LayoutDemo(ui.View):
    
    def __init__(self, **kwargs):
      super().__init__(**kwargs)
      self.previous_size_class = None
      self.active_constraints = []
      self.create_ui()
    
    def layout(self):
      if Constrain.is_width_constrained():
        self.main_leading.constant = 0
      else:
        self.main_leading.constant = 300
    
    def style(self, view):
      view.background_color='white'
      view.border_color = 'black'
      view.border_width = 1
      view.text_color = 'black'
      view.tint_color = 'black'
      
    def create_ui(self):    
      self.style(self)
      
      main_frame = ui.View(name='Main frame')
      self.add_subview(main_frame)
      
      side_panel = ui.Label(
        name='Side panel',
        text='Side navigation panel', 
        alignment=ui.ALIGN_CENTER)
      self.style(side_panel)
      self.add_subview(side_panel)
      
      main_frame_c = Constrain(main_frame)
      side_panel_c = Constrain(side_panel)
      main_frame_c.dock_trailing(fit=Constrain.SAFE)
      self.main_leading = main_frame_c.leading == Constrain(self).safe_area.leading
      side_panel_c.dock_leading(fit=Constrain.SAFE)
      #print(Constrain.is_width_regular())
      side_panel_c.width == 300
      side_panel_c.height == main_frame_c.height
      
      side_panel_c.trailing == main_frame_c.leading
      
      search_field = ui.TextField(name='Searchfield', placeholder='Search path')
      main_frame.add_subview(search_field)
      self.style(search_field)
      
      search_button = ui.Button(name='Search', title='Search')
      main_frame.add_subview(search_button)
      self.style(search_button)
      
      result_area = ui.Label(text='Main results display area', alignment=ui.ALIGN_CENTER)
      main_frame.add_subview(result_area)
      self.style(result_area)
      
      done_button = ui.Button(name='Done', title='Done')
      main_frame.add_subview(done_button)
      self.style(done_button)
      
      def done(sender):
        root.close()
      done_button.action = done
      
      cancel_button = ui.Button(name='Cancel', title='Cancel')
      main_frame.add_subview(cancel_button)
      self.style(cancel_button)
      
      search_field_c = Constrain(search_field)
      search_button_c = Constrain(search_button).fit()
      done_button_c = Constrain(done_button).fit()
      cancel_button_c = Constrain(cancel_button).fit()
      result_area_c = Constrain(result_area)
      
      search_field_c.dock_top_leading()
      search_button_c.dock_top_trailing()
      search_field_c.trailing == search_button_c.leading_padding
      search_field_c.height == search_button_c.height
      
      done_button_c.dock_bottom_trailing()
      cancel_button_c.trailing == done_button_c.leading_padding
      cancel_button_c.top == done_button_c.top
      result_area_c.dock_horizontal_between(search_button, done_button)
      
      #d = Constrain.DiagnosticOverlay(self, search_field)
  
  root = LayoutDemo()
  root.present('full_screen', hide_title_bar=True, animated=False)
  
  '''
  guide = C.create_guide(root)
  C(guide).left_margin == C(root).left

  C(textfield).leading == C(guide).leading
  gap = (C(button).left == C(textfield).right + C.margin_inset(button).leading)
  C(button).trailing == C(guide).trailing
  C(textfield).top == C(guide).top

  C(textfield).bottom == C(guide).bottom
  C(button).center_y == C(textfield).center_y
  C(button).height == C(button).width

  C(guide).leading == C(root).margins.leading
  C(guide).trailing == C(root).margins.trailing
  C(guide).center_y == C(root).center_y
  C(guide).height == 30
  '''
  
  '''
  @scripter.script
  def constant_to(constraint, value, **kwargs):
    scripter.slide_value(constraint, 'constant', value, **kwargs)
  #constant_to(gap, 100, ease_func=scripter.ease_in_out)
  '''
