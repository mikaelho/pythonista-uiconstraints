# pythonista-uiconstraints

Python wrapper for Apple UI view layout constraints.

## Why constraints?

Constraints are used to determine how views are laid out in your UI. They are an alternative to the `x`, `y`, `frame` method used in Pythonista by default. You have to pick one or the other for an individual view, as Apple does not make them interoperable.

You can create pretty much all the same layouts and achieve the same level of dynamic behavior just using Pythonista's regular `frame`, `flex` attribute and the `layout` method. The reason to consider constraints is that they, and the convenience methods in this wrapper, provide perhaps a more human way of expressing the desired layout. You can use one-liners for "keep this view below that other view, no matter what happens", or "this view takes over the top half of the screen, with margins", without fiddling with pixel calculations or creating several ui.Views just for the layout.

## Basic usage

Here is an example of constraining view1 to be always positioned below view2, with the standard margin:

    from uiconstraints import Constrain
    
    Constrain(view1).top == Constrain(view2).bottom_padding
    
To make it a bit more succint, you might alias the class:

    from uiconstraints import Constrain as C
    
    C(view1).top == C(view2).bottom_padding
    
In practice, you usually need to set more than one constraint per view, so it makes sense to use separate variables, for readability and ease of typing:

    button_c = Constrain(button)
    textfield_c = Constrain(textfield)
    
    button_c.leading == textfield_c.trailing_padding
    
Constraints can use the following attributes:

*     `left, right, top, bottom, width, height`
*     `leading, trailing`
	*     Same as `left` and `right` for left-to-right languages, but automatically reversed for right-to-left languages.
*     `center_x, center_y`
*     `last_baseline, first_baseline`
*     `left_margin, right_margin, top_margin, bottom_margin, leading_margin, trailing_margin`
	* Use these when you want to leave a standard margin between the view and the edge of its superview (inside margin).
*     `left_padding, right_padding, top_padding, bottom_padding, leading_padding, trailing_padding`
	* Use these when you want to leave a standard margin between the view and the view next to it (outside margin).

While these constraints are easy to create, you need several for each view, and that can get tedious very quickly. Thus the wrapper provides several convenience functions to set several constraints at once. All these start with `dock_`, and place the view in the indicated area:

* `dock_all, dock_center, dock_horizontal, dock_vertical, dock_horizontal_between, dock_vertical_between, dock_top, dock_bottom, dock_leading, dock_trailing, dock_top_leading, dock_top_trailing, dock_bottom_leading, dock_bottom_trailing`

All of these methods have two optional arguments:

* `fit` - can have one of three values:
	* `Constrain.TIGHT` - no additional margins
	* `Constrain.MARGIN` - standard margins on all connected sides
	* `Constrain.SAFE` - margins avoiding the unsafe areas, e.g. top and bottom in portrait orientation on iPhone X
* `constant` - additional offset to be applied on all connected sides

Default fit is `Constrain.MARGIN`. You can change this for all the convenience methods by setting `Constrain.default_fit` before using the functions.

## Example

Putting together all the tools mentioned in the previous example, here is how you set up a UI shown in the picture above:



Note that this implementation wraps the constraint _factory_ class, [NSLayoutConstraint](https://developer.apple.com/documentation/uikit/nslayoutconstraint) - after the constraints have been created, they are regular Apple UI code.

## Anatomy of a constraint


