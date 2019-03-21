#coding: utf-8
import objc_util
import ui
import inspect, gc, types, sys, random, math
from types import SimpleNamespace
from copy import copy
from collections import defaultdict
from functools import partial

NSLayoutConstraint = objc_util.ObjCClass('NSLayoutConstraint')
UILayoutGuide = objc_util.ObjCClass('UILayoutGuide')
UIDevice = objc_util.ObjCClass('UIDevice')
UIViewPropertyAnimator = objc_util.ObjCClass('UIViewPropertyAnimator')

def prop(func):
  'Combined getter/setter property'
  return property(func, func)

class At:
  
  standard = 8
  
  def __init__(self, view, priority=1000):
    '''Initialize a constraint manager for a view with the given priority.'''
    
    self.view = view
    self.attribute = 0
    self.attribute_name = 'na'
    self.attribute_type = 'NNN'
    self.operator = 0
    self.other_view = None
    self.other_attribute = 0
    self.other_attribute_name = 'na'
    self.other_attribute_type = 'NNN'
    self.multiplier = 1
    self.description = None
    self._constant = 0
    self._priority = priority
    
  @property
  def objc_constraint(self):
    if self.description is None:
      return None
    return find_constraint(self.view, self.description)
    
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
    
  def __str__(self):
    #return str(self.objc_constraint)
    
    operators = ['<=', '==', '>=']
    
    view = self.view.name if self.view.name else type(self.view).__name__
    
    operator = operators[self.operator + 1]
    
    other_view = self.other_view.name if \
    self.other_view and self.other_view.name\
    else (type(self.other_view).__name__ if self.other_view is not None else '')
    
    other_attribute_str = '' if self.other_attribute == 0 else f'.{self.other_attribute_name} '
    
    multiplier_str = f'* {self.multiplier} ' if self.multiplier != 1 else ''
    
    constant_str = ''
    if self.constant < 0:
      constant_str = f'- {abs(self.constant)}'
    elif self.constant > 0:
      constant_str = f'+ {self.constant}'
    
    return (f'{view}.{self.attribute_name} {operator} '
    f'{other_view}{other_attribute_str}'
    f'{multiplier_str}{constant_str}')
    
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
    #c = copy(self)
    self.operator = 0
    self._create_constraint(other)
    return self
  
  def __ge__(self, other):
    c = copy(self)
    c.operator = 1
    c._create_constraint(other)
    return c
  
  def _get(prop, attribute, name, type_str):
    '''Property creator for constraint
    attributes'''
    p = property(
      lambda self:
        partial(prop, self, attribute, name, type_str)(),
      lambda self, value:
        partial(prop, self, attribute, name, type_str, value)()
    )
    return p
    
  def _prop(self, attribute, name, type_str, *values):
    '''Combined getter/setter for
    constraint attributes.
    Effectively makes using assignment ('=')
    and equality comparison ('==') equal.'''
    
    if type(self.view) is Guide:
      if attribute > 10:
        raise AttributeError(
          f"Cannot use attribute '{name}' with a layout guide")
          
    c = copy(self)
    c.attribute = attribute
    c.attribute_name = name
    c.attribute_type = type_str
    return (c == values[0]) if len(values) else c
    
  # Attribute properties - numbers are
  # Apple NSLayoutConstraint constants
  
  # Magical code contains three letters:
  #   1. Position/Size
  #   2. Horizontal/Vertical/NA
  #   3. Absolute/Relative/NA
  # These are used to check constraint
  # compatibility
  left = _get(_prop, 1, 'left', 'PHA')
  right = _get(_prop, 2, 'right', 'PHA')
  top = _get(_prop, 3, 'top', 'PVN')
  bottom = _get(_prop, 4, 'bottom', 'PVN')
  leading = _get(_prop, 5, 'leading', 'PHR')
  trailing = _get(_prop, 6, 'trailing', 'PHR')
  width = _get(_prop, 7, 'width', 'SNN')
  height = _get(_prop, 8, 'height', 'SNN')
  center_x = _get(_prop, 9, 'center_x', 'PHN')
  center_y = _get(_prop, 10, 'center_y', 'PVN')
  last_baseline = _get(_prop, 11, 'last_baseline', 'PVN')
  first_baseline = _get(_prop, 12, 'first_baseline', 'PVN')
  left_margin = _get(_prop, 13, 'left_margin', 'PHA')
  right_margin = _get(_prop, 14, 'right_margin', 'PHA')
  top_margin = _get(_prop, 15, 'top_margin', 'PVN')
  bottom_margin = _get(_prop, 16, 'bottom_margin', 'PVN')
  leading_margin = _get(_prop, 17, 'leading_margin', 'PHR')
  trailing_margin = _get(_prop, 18, 'trailing_margin', 'PHR')

  # Padding attributes have different
  # property setup because of the additional
  # constant needed
    
  @prop
  def left_padding(self, *values):
    c = copy(self)
    c = c.left
    c._constant -= c.margin_inset().leading
    return (c == values[0]) if len(values) else c
    
  @prop
  def right_padding(self, *values):
    c = copy(self)
    c = c.right
    c._constant += c.margin_inset().trailing
    return (c == values[0]) if len(values) else c
    
  @prop
  def top_padding(self, *values):
    c = copy(self)
    c = c.top
    c._constant -= c.margin_inset().top
    return (c == values[0]) if len(values) else c
    
  @prop
  def bottom_padding(self, *values):
    c = copy(self)
    c = c.bottom
    c._constant += c.margin_inset().bottom
    return (c == values[0]) if len(values) else c
    
  @prop
  def leading_padding(self, *values):
    c = copy(self)
    c = c.leading
    c._constant -= c.margin_inset().leading
    return (c == values[0]) if len(values) else c
    
  @prop
  def trailing_padding(self, *values):
    c = copy(self)
    c = c.trailing
    c._constant += c.margin_inset().trailing
    return (c == values[0]) if len(values) else c
    
  def margin_inset(self):
    return SimpleNamespace(
      bottom=At.standard, 
      leading=At.standard, 
      trailing=At.standard,
      top=At.standard)

  @property
  def safe_area(self):
    return At(view=SimpleNamespace(
      objc_instance=self.view.objc_instance.safeAreaLayoutGuide(),
      name='Safe area',
      superview=self.view))
    
  @property
  def margins(self):
    return At(view=SimpleNamespace(
      objc_instance=self.view.objc_instance.layoutMarginsGuide(),
      name='Margins',
      superview=self.view))

  @objc_util.on_main_thread
  def _create_constraint(self, other):
    if isinstance(other, At):
      self.other_view = other.view
      self.other_attribute = other.attribute
      self.other_attribute_name = other.attribute_name
      self.other_attribute_type = other.attribute_type
      self.constant = other.constant
      self.multiplier = other.multiplier
    elif isinstance(other, (int, float)):
      self.constant = other
    else:
      raise TypeError(
        f'Cannot use object of type {str(type(other))} in a constraint comparison: ' + 
        str(other))
    
    for i in range(3):
      t = self.attribute_type
      ot = self.other_attribute_type
      if t[i] == 'N' or ot[i] == 'N':
        continue
      if t[i] != ot[i]:
        raise TypeError(f'Incompatible attributes in constraint: {str(self)}')
    
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

    objc_constraint = NSLayoutConstraint.\
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
    
    objc_constraint.setActive_(True)
    self.description = str(objc_constraint._deallocSafeDescription())
      
  def priority(self, *value):
    '''
    Without value, returns the current priority of the constraint.
    With value, sets the constraint to a priority expressed as an integer
    between 0 and 1000, where 1000 means a required constraint, and values 0-999
    optional constraints.
    
    For example:
      
        view.at.priority(500).width == 300
    
    Note:
      You cannot change priority between required and optional after present(),
      but you can change between different optional priority levels.
    '''
    if len(value) == 0:
      return objc_constraint.priority() if self.objc_constraint else None
    value = value[0]
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
    return self
    
  @property
  def is_ambiguous(self):
    '''Returns true if the constraints for this view are not disambiguous 
    (position and size are not defined in a way that can be resolved by the
    system.)'''
    return self.view.objc_instance.hasAmbiguousLayout()
    
  def exercise_ambiguity(self):
    self.view.objc_instance.exerciseAmbiguityInLayout()
    
    
class Dock:
  '''Dock methods are focused on connecting different sides of the view to its 
  superview.'''
  
  def __init__(self, view):
    self.view = view
    
  @property
  def superview(self):
    if self.view:
      return self.view.superview
      
  @property
  def subviews(self):
    if self.view:
      return self.view.subviews
    
  extra_width_types = [ui.Label, ui.Button]
    
  @objc_util.on_main_thread
  def fit(self):
    'Set size constraints according to the views preferred size.'
    view = self.view
    size = view.objc_instance.sizeThatFits_((0,0))
    extra_width = 0
    if type(view) in self.extra_width_types:
      margins = self.view.at.margin_inset()
      extra_width = margins.leading + margins.trailing
    self.view.at.width == size.width + extra_width
    self.view.at.height == size.height
    return view
    
  TIGHT = 0
  MARGIN = 1
  SAFE = 2
  default_fit = MARGIN

  def _fit(self, fit):
    s = self.superview
    if fit == Dock.TIGHT:
      return s.at
    elif fit == Dock.MARGIN:
      return s.at.margins
    elif fit == Dock.SAFE:
      return s.at.safe_area
    
  def all(self, constant=0, fit=default_fit):
    'Dock the view on all sides.'
    view = self.view
    sf = self._fit(fit)
    view.at.top == self._fit(fit).top + constant
    view.at.bottom == self._fit(fit).bottom - constant
    view.at.leading == self._fit(fit).leading + constant

    view.at.trailing == self._fit(fit).trailing - constant
    
  def center(self, share=None):
    view = self.view
    s = enable(self.superview)
    view.at.center_x == s.at.center_x
    view.at.center_y == s.at.center_y
    self._set_size(share)
  
  def sides(self, share=None, constant=0, fit=default_fit):
    view = self.view
    view.at.leading == self._fit(fit).leading + constant
    view.at.trailing == self._fit(fit).trailing - constant
    self._set_size(share)
    
  horizontal = sides
  
  def horizontal_between(self, top_view, bottom_view, constant=0, fit=default_fit):
    at = self.view.at
    enable(top_view, bottom_view)
    self.horizontal(constant=constant, fit=fit)
    if fit == Dock.TIGHT:
      at.top == top_view.at.bottom + constant
      at.bottom == top_view.at.top + constant
    else:
      at.top == top_view.at.bottom_padding + constant
      at.bottom == bottom_view.at.top_padding + constant
    
  def vertical(self, constant=0, fit=default_fit):
    at = self.view.at
    at.top == self._fit(fit).top + constant
    at.bottom == self._fit(fit).bottom - constant
    
  def vertical_between(self, leading_view, trailing_view, constant=0, 
  fit=default_fit):
    at = self.view.at
    enable(leading_view, trailing_view)
    self.vertical(constant, fit)
    if fit == Constrain.TIGHT:
      at.leading == leading_view.at.trailing + constant
      at.trailing == trailing_view.at.leading + constant
    elif fit == Constrain.MARGIN:
      at.leading == leading_view.at.trailing_padding + constant
      at.trailing == trailing_view.at.leading_padding + constant
    
  def _set_size(self, share):
    if share is not None:
      share_x, share_y = share if type(share) in (list, tuple) else (share, share)
      at = self.view.at
      s = enable(self.superview)
      at.width == s.width * share_x
      at.height == s.height * share_y
    
  def top(self, share=None, constant=0, fit=default_fit):
    at = self.view.at
    at.top == self._fit(fit).top + constant
    at.leading == self._fit(fit).leading + constant
    at.trailing == self._fit(fit).trailing - constant
    if share is not None:
      
      at.height == enable(self.superview).at.height * share
  
  def bottom(self, share=None, constant=0, fit=default_fit):
    at = self.view.at
    at.bottom == self._fit(fit).bottom - constant
    at.leading == self._fit(fit).leading + constant
    at.trailing == self._fit(fit).trailing - constant
    if share is not None:
      
      at.height == enable(self.superview).at.height * share
    
  def leading(self, share=None, constant=0, fit=default_fit):
    at = self.view.at
    at.leading == self._fit(fit).leading + constant
    at.top == self._fit(fit).top + constant
    at.bottom == self._fit(fit).bottom - constant
    if share is not None:
      
      at.width == enable(self.superview).at.width * share
    
  def trailing(self, share=None, constant=0, fit=default_fit):
    at = self.view.at
    at.trailing == self._fit(fit).trailing - constant
    at.top == self._fit(fit).top + constant
    at.bottom == self._fit(fit).bottom - constant
    if share is not None:
      
      at.width == enable(self.superview).at.width * share
    
  def top_leading(self, share=None, constant=0, fit=default_fit):
    at = self.view.at
    at.top == self._fit(fit).top + constant
    at.leading == self._fit(fit).leading + constant
    self._set_size(share)
    
  def top_trailing(self, share=None, constant=0, fit=default_fit):
    at = self.view.at
    at.top == self._fit(fit).top + constant
    at.trailing == self._fit(fit).trailing - constant
    self._set_size(share)
    
  def bottom_leading(self, share=None, constant=0, fit=default_fit):
    at = self.view.at
    at.bottom == self._fit(fit).bottom - constant
    at.leading == self._fit(fit).leading + constant
    self._set_size(share)

  def bottom_trailing(self, share=None, constant=0, fit=default_fit):
    at = self.view.at
    at.bottom == self._fit(fit).bottom - constant
    at.trailing == self._fit(fit).trailing - constant
    self._set_size(share)
    
class Align:
  '''Align methods are convenient for aligning same properties of views:
    
      view_a.align.top(view_b)
      
  They are especially convenient when you need to align several views at once:
    
      view_a.align.center_x(view_b, view_c)
  '''
  
  def __init__(self, view):
    self.view = view
    
  def _align(self, other_views):
    attribute_name = inspect.currentframe().f_back.f_code.co_name
    for other_view in other_views:
      enable(other_view)
      last_constraint = (
        getattr(self.view.at, attribute_name) == 
        getattr(other_view.at, attribute_name))
    return last_constraint
      
  def left(self, *others):
    return self._align(others)
  def right(self, *others):
    return self._align(others)
  def top(self, *others):
    return self._align(others)
  def bottom(self, *others):
    return self._align(others)
  def leading(self, *others):
    return self._align(others)
  def trailing(self, *others):
    return self._align(others)
  def width(self, *others):
    return self._align(others)
  def height(self, *others):
    return self._align(others)
  def center_x(self, *others):
    return self._align(others)
  def center_y(self, *others):
    return self._align(others)
  def last_baseline(self, *others):
    return self._align(others)
  def first_baseline(self, *others):
    return self._align(others)
  def left_margin(self, *others):
    return self._align(others)
  def right_margin(self, *others):
    return self._align(others)
  def top_margin(self, *others):
    return self._align(others)
  def bottom_margin(self, *others):
    return self._align(others)
  def leading_margin(self, *others):
    return self._align(others)
  def trailing_margin(self, *others):
    return self._align(others)
  def left_padding(self, *others):
    return self._align(others)
  def right_padding(self, *others):
    return self._align(others)
  def top_padding(self, *others):
    return self._align(others)
  def bottom_padding(self, *others):
    return self._align(others)
  def leading_padding(self, *others):
    return self._align(others)
  def trailing_padding(self, *others):
    return self._align(others)
    
  def size(self, *others):
    self.width(*others)
    return self.height(*others)
    
  def center(self, *others):
    self.center_x(*others)
    return self.center_y(*others)

    
class ConstraintView:
  
  @property
  def at(self):
    return At(self)

  @property
  def align(self):
    return Align(self)
    
  @property
  def dock(self):
    return Dock(self)


class Constrainer():

  def __new__(extender_subclass, *args, **kwargs):
    target_instance = extender_subclass._builtin_class(*args, **kwargs)
    target_instance.at = At(target_instance)
    target_instance.align = Align(target_instance)
    target_instance.dock = Dock(target_instance)
    return target_instance

# Generate enabled versions for all ui views
for key in ui.__dict__:
  value = getattr(ui, key, None)
  if type(value) is type and ui.View in value.mro():
    globals()[key] = type(key, (Constrainer,), {'_builtin_class': value})


def enable(*views):
  ''' All views must be enabled before constraints can be applied. It is safe
  to enable an already-enabled view.
  
  You can provide several views to be enabled. First view is returned.'''
  for view in views:
    assert hasattr(view, 'objc_instance')
    view.at = At(view)
    view.dock = Dock(view)
    view.align = Align(view)
  return views[0]
  
def fit(*views):
  ''' Convenience method to both enable and apply natural fit width and height
  constraints with one call. Useful mainly for Buttons and Labels.
  
  You can provide several views, first view is returned. '''
  for view in views:
    enable(view)
    view.dock.fit()
  return views[0]
 
@objc_util.on_main_thread 
def find_constraint(view, description):
  objc_view = view.objc_instance
  while view:
    for c in view.objc_instance.constraints():
      if str(c._deallocSafeDescription()) == description:
        return c
    view = view.superview
 
@objc_util.on_main_thread 
def find_constraints(view, first=True, second=False, active_only=True, filter=None):
  objc_view = view.objc_instance
  constraints = []
  if filter is None:
    filter = []
  elif type(filter) not in (tuple, list):
    filter = [filter]
  filter = [inspect.getclosurevars(filter_prop.fget).nonlocals['attribute'] for filter_prop in filter]
  while view:
    for c in view.objc_instance.constraints():
      if (
        (first and c.firstItem() == objc_view) or
        (second and c.secondItem() == objc_view)
      ) and (
        c.active() or not active_only
      ) and (
        len(filter) == 0 or c.firstAttribute() in filter
      ):
        constraints.append(c)
    view = view.superview
  return constraints
  
def remove_constraints(view, filter=None):
  if hasattr(view, 'layout_constraints'):
    for constraint in view.layout_constraints.copy():
      if filter is not None and constraint.attribute_name not in filter:
        print('skipping', constraint.attribute_name)
        continue
      remove_constraint(constraint)
    #remove_constraint(view.layout_constraints)
 
@objc_util.on_main_thread     
def remove_guides(view):
  ''' Removes all layout guides from a view. '''
  vo = view.objc_instance
  guides = view.objc_instance.layoutGuides()
  if type(guides) is list:
    for guide in vo.layoutGuides():
      vo.removeLayoutGuide_(guide)

@objc_util.on_main_thread      
def remove_guide(guide):
  ''' Remove the given guide from its owner. '''
  vo = guide.view.objc_instance
  vo.removeLayoutGuide_(guide.objc_instance)
  guide.view = None
  guide.objc_instance = None
      
def check_ambiguity(view, indent=0):
  '''Prints all views in the view hierarchy starting with the given view,
  marking the ones that have ambiguous layout . 
  Returns a list of ambiguous views.'''
  ambiguous_views = []
  layout = '- Frames'
  if view.objc_instance.translatesAutoresizingMaskIntoConstraints():
    layout = '- Constraints'
    if view.at.is_ambiguous:
      layout += ' AMBIGUOUS'
      ambiguous_views.append(view)
  view_name = view.name
  if view_name is None or len(view_name) == 0:
    view_name = str(view)
  print(' '*indent, view_name, layout)
  for subview in view.subviews:
    ambiguous_views += check_ambiguity(subview, indent+1)
  return ambiguous_views
      
class Guide(SimpleNamespace):
  
  @objc_util.on_main_thread
  def __init__(self, view):
    guide = UILayoutGuide.new().autorelease()
    view.objc_instance.addLayoutGuide_(guide)
    super().__init__(
      objc_instance=guide,
      view=view,
      name='LayoutGuide')
    enable(self)
  
  @property
  def superview(self):
    if self.view:
      return self.view.superview
      
  @property
  def subviews(self):
    if self.view:
      return self.view.subviews
        
  
class Dimensions:
  
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
    return objc_util.UIApplication.sharedApplication().keyWindow().traitCollection().\
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
    

class GridView(ui.View):
  'Places subviews as squares that fill the available space.'
  
  FILL = 'III'
  SPREAD = '___'
  CENTER = '_I_'
  START = 'II_'
  END = '_II'
  SIDES = 'I_I'
  START_SPREAD = 'I__'
  END_SPREAD = '__I'
  
  MARGIN = At.standard
  TIGHT = 0
  
  def __init__(self,
    pack_x=CENTER, pack_y=CENTER, pack=None,
    count_x=None, count_y=None,
    gap=MARGIN, **kwargs):
    '''By default, subviews are laid out in a grid as squares of optimal size and
    centered in the view.
    
    You can fix the amount of views in either dimension with the `count_x` or
    `count_y` parameter, or change the packing behaviour by providing
    the `pack` parameter with one of the following values:
      
      * `CENTER` - Clustered in the center (the default)
      * `SPREAD` - Distributed evenly
      * `FILL` - Fill the available space with only margins in between
        (no longer squares)
      * `LEADING, TRAILING` (`pack_x` only)
      * `TOP, BOTTOM` (`pack_y` only)
    '''
    
    super().__init__(**kwargs)

    if pack is not None:
      pack_x = pack_y = pack
    self.pack_x = pack_x
    self.pack_y = pack_y
    
    self.leading_free = pack_x[0] == '_'
    self.center_x_free = pack_x[1] == '_'
    self.trailing_free = pack_x[2] == '_'
    self.top_free = pack_y[0] == '_'
    self.center_y_free = pack_y[1] == '_'
    self.bottom_free = pack_y[2] == '_'

    self.count_x = count_x
    self.count_y = count_y
    
    self.gap = gap

    enable(self)

  def dimensions(self, count):
    if self.height == 0:
      return 1, count
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
  
  def layout(self):
    count = len(self.subviews)
    if count == 0: return

    count_x, count_y = self.count_x, self.count_y
    if count_x is None and count_y is None:
      count_x, count_y = self.dimensions(count)
    elif count_x is None:
      count_x = math.ceil(count/count_y)
    elif count_y is None:
      count_y = math.ceil(count/count_x)
    if count > count_x * count_y:
      raise ValueError(
        f'Fixed counts (x: {count_x}, y: {count_y}) not enough to display all views')
        
    borders = 2 * self.border_width
        
    dim_x = (self.width-borders-(count_x+1)*self.MARGIN)/count_x
    dim_y = (self.height-borders-(count_y+1)*self.MARGIN)/count_y
        
    dim = min(dim_x, dim_y)
      
    px = self.pack_x
    exp_pack_x = px[0] + px[1]*(count_x-1) + px[2]
    py = self.pack_y
    exp_pack_y = py[0] + py[1]*(count_y-1) + py[2]
    free_count_x = exp_pack_x.count('_')
    free_count_y = exp_pack_y.count('_')
    
    if free_count_x > 0:
      per_free_x = (
        self.width - 
        borders -
        count_x*dim -
        (count_x+1-free_count_x)*self.MARGIN)/free_count_x
    if free_count_y > 0:
      per_free_y = (
        self.height - 
        borders -
        count_y*dim -
        (count_y+1-free_count_y)*self.MARGIN)/free_count_y
              
    real_dim_x = dim_x if free_count_x == 0 else dim
    real_dim_y = dim_y if free_count_y == 0 else dim
              
    subviews = iter(self.subviews)
    y = self.border_width + (per_free_y if self.top_free else self.MARGIN)
    for row in range(count_y):
      x = self.border_width + (per_free_x if self.leading_free else self.MARGIN)
      for col in range(count_x):
        try:
          view = next(subviews)
        except StopIteration:
          break
        view.frame = (x, y, real_dim_x, real_dim_y)
        x += real_dim_x + (per_free_x if self.center_x_free else self.MARGIN)
      y += real_dim_y + (per_free_y if self.center_y_free else self.MARGIN)

    
class DiagnosticOverlay(ui.View):
  '''Shows constraints as markers on top of the UI.'''
  colors = (
    (('left', 'right', 'leading', 'trailing', 'top', 'bottom',
    'left_margin', 'right_margin', 'leading_margin', 'trailing_margin', 
    'top_margin', 'bottom_margin'), 'red'),
    (('width', 'height'), 'green'),
    (('center_x', 'center_y'), 'blue'),
    (('first_baseline', 'last_baseline'), 'purple')
  )
  
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
      import console
      console.alert(self.text)
      
  
  def __init__(self, root, start=None, attributes=[], **kwargs):
    self.start = start or root
    super().__init__(
      frame=root.bounds, flex='WH', 
      background_color=(1,1,1,0.7), 
      **kwargs)
    root.add_subview(self)
    self.connectors = []
    self.add_overlay(start or root, attributes)
    self.add_subview(type(self).ConnectorOverlay(frame=self.bounds, flex='WH'))
    
  def collect_views(self, view):
    if type(view) is SimpleNamespace:
      return []
    local_list = [view] if hasattr(view, 'layout_constraints') else []
    for subview in view.subviews:
      if hasattr(subview, 'layout_constraints'):
        local_list += self.collect_views(subview)
    return local_list
    
  def add_overlay(self, first_view, attributes):
    ''' Displays the active constraints for first_view and all of its subviews
    as an overlay on the current UI.
    
    If attribute is not an empty list, displays only constraints with a matching 
    target attribute.'''
    process_queue = self.collect_views(first_view)
    for view in process_queue:
      '''
      if len(palette) == 0:
        palette = cls.DiagnosticOverlay._marker_palette.copy()
        random.shuffle(palette)
      colors = palette.pop()
      '''
      for constraint in view.layout_constraints:
        if len(attributes) > 0 and constraint.attribute_name not in attributes:
          continue
        color = 'black'
        for item in self.colors:
          if constraint.attribute_name in item[0]:
            color = item[1]
            break
        marker = enable(DiagnosticOverlay.AnchorMarker(
          color,
          str(constraint)))
        self.add_subview(marker)
        self._place_anchor_marker(
          constraint.view, 
          constraint.attribute_name,
          color, marker)
        if constraint.other_view is not None and type(constraint.other_view) not in (SimpleNamespace, Guide):
          other_marker = enable(DiagnosticOverlay.AnchorMarker(
            color,
            str(constraint)))
          self.add_subview(other_marker)
          self._place_anchor_marker(
            constraint.other_view, 
            constraint.other_attribute_name, 
            color, other_marker)
          
          self.connectors.append((marker, other_marker, color))
   
  def _place_anchor_marker(self, view, a, color, marker):
    if view is None: return 
    thickness = 5
    share = 0.75
    marker_size = 20
    if a == 'left':
      marker.at.center_x == view.at.left
      marker.at.center_y == view.at.center_y
      marker.at.width == thickness
      marker.at.height == marker_size
    elif a == 'right':
      marker.at.center_x == view.at.right
      marker.at.center_y == view.at.center_y
      marker.at.center_y == view.at.center_y
      marker.at.width == thickness
      marker.at.height == view.at.height * share
    elif a == 'top':
      marker.at.center_x == view.at.center_x
      marker.at.center_y == view.at.top
      marker.at.height == thickness
      marker.at.width == view.at.width * share
    elif a == 'bottom':
      marker.at.center_x == view.at.center_x
      marker.at.center_y == view.at.bottom
      marker.at.height == thickness
      marker.at.width == view.at.width * share
    elif a == 'leading':
      marker.at.center_x == view.at.leading
      marker.at.center_y == view.at.center_y
      marker.at.width == thickness
      marker.at.height == view.at.height * share
    elif a == 'trailing':
      marker.at.center_x == view.at.trailing
      marker.at.center_y == view.at.center_y
      marker.at.width == thickness
      marker.at.height == view.at.height * share
    elif a == 'width':
      marker.at.center_x == view.at.center_x
      marker.at.center_y == view.at.center_y
      marker.at.height == thickness
      marker.at.width == view.at.width
    elif a == 'height':
      marker.at.center_x == view.at.center_x
      marker.at.center_y == view.at.center_y
      marker.at.width == thickness
      marker.at.height == view.at.height
    elif a == 'center_x':
      marker.at.center_x == view.at.center_x
      marker.at.center_y == view.at.center_y
      marker.at.width == thickness
      marker.at.height == view.at.height * share
    elif a == 'center_y':
      marker.at.center_x == view.at.center_x
      marker.at.center_y == view.at.center_y
      marker.at.height == thickness
      marker.at.width == view.at.width * share
    elif a == 'last_baseline':
      marker.at.center_x == view.at.center_x
      marker.at.center_y == view.at.last_baseline
      marker.at.height == thickness
      marker.at.width == view.at.width * share
    elif a == 'first_baseline':
      marker.at.center_x == view.at.center_x
      marker.at.center_y == view.at.first_baseline
      marker.at.height == thickness
      marker.at.width == view.at.width * share
    elif a == 'left_margin':
      marker.at.center_x == view.at.left_margin
      marker.at.center_y == view.at.center_y
      marker.at.width == thickness
      marker.at.height == view.at.height * share
    elif a == 'right_margin':
      marker.at.center_x == view.at.right_margin
      marker.at.center_y == view.at.center_y
      marker.at.width == thickness
      marker.at.height == view.at.height * share
    elif a == 'top_margin':
      marker.at.center_x == view.at.center_x
      marker.at.center_y == view.at.top_margin
      marker.at.height == thickness
      marker.at.width == view.at.width * share
    elif a == 'bottom_margin':
      marker.at.center_x == view.at.center_x
      marker.at.center_y == view.at.bottom_margin
      marker.at.height == thickness
      marker.at.width == view.at.width * share
    elif a == 'leading_margin':
      marker.at.center_x == view.at.leading_margin
      marker.at.center_y == view.at.center_y
      marker.at.width == thickness
      marker.at.height == view.at.height * share
    elif a == 'trailing_margin':
      marker.at.center_x == view.at.trailing_margin
      marker.at.center_y == view.at.center_y
      marker.at.width == thickness
      marker.at.height == view.at.height * share
  
if __name__ == '__main__':
  
  class LayoutDemo(ui.View):
    
    def __init__(self, **kwargs):
      super().__init__(**kwargs)
      self.previous_size_class = None
      self.active_constraints = []
      enable(self)
      self.create_ui()
    
    def layout(self):
      if Dimensions.is_width_constrained():
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
      
      main_frame = View(name='Main frame')
      self.add_subview(main_frame)
      
      side_panel = Label(
        name='Side panel',
        text='Side navigation panel', 
        alignment=ui.ALIGN_CENTER)
      self.style(side_panel)
      self.add_subview(side_panel)
      
      main_frame.dock.all(fit=Dock.SAFE)
      
      self.main_leading = main_frame.at.leading == self.at.safe_area.leading
      
      side_panel.dock.leading(fit=Dock.SAFE)
      side_panel.at.width == 300
      side_panel.align.height(main_frame)
      
      side_panel.at.trailing == main_frame.at.leading
      
      search_field = TextField(
        name='Searchfield', 
        placeholder='Search path')
      main_frame.add_subview(search_field)
      self.style(search_field)
      
      search_button = Button(
        name='Search', 
        title='Search').dock.fit()
      main_frame.add_subview(search_button)
      self.style(search_button)
      
      result_area = GridView(
        name='Result area', 
        pack=GridView.SPREAD)
      main_frame.add_subview(result_area)
      self.style(result_area)
      
      done_button = Button(
        name='Done', title='Done').dock.fit()
      main_frame.add_subview(done_button)
      self.style(done_button)
      
      def done(sender):
        root.close()
      done_button.action = done
      
      cancel_button = Button(
        name='Cancel',
        title='Cancel').dock.fit()
      main_frame.add_subview(cancel_button)
      self.style(cancel_button)

      search_field.dock.top_leading()
      search_button.dock.top_trailing()
      search_field.at.trailing == search_button.at.leading_padding
      search_field.align.height(search_button)
      
      done_button.dock.bottom_trailing()
      cancel_button.at.trailing == done_button.at.leading_padding
      cancel_button.align.top(done_button)
      result_area.dock.horizontal_between(
        search_button, done_button) 
        
      for _ in range(5):
        content_view = View()
        self.style(content_view)
        result_area.add_subview(content_view)
      
      #DiagnosticOverlay(self, 
      #start=result_area,
      #attributes=[])
      #check_ambiguity(self)

  root = LayoutDemo()
  root.present('full_screen', hide_title_bar=True, animated=False)

