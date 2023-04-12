import tkinter as tk


class ToolTip(object):
    """Create the mouse-hover info boxes.

    See https://stackoverflow.com/questions/3221956/how-do-i-display-tooltips-in-tkinter
    """

    def __init__(self, widget: tk.Widget):
        """ToolTip Constructor.

        Take a reference to the documented widget.

        Parameters
        ----------
        widget : tk.Widget
            Widget documented by the ToolTip instance.
        """
        self.widget = widget
        self.tipwindow = None
        self.id = None
        self.x = self.y = 0

    def showtip(self, text: str) -> None:
        """Display text in tooltip window.

        Parameters
        ----------
        text : str
            Text to show in the window.
        """
        self.text = text
        if self.tipwindow or not self.text:
            return
        x, y, _, cy = self.widget.bbox()
        x = x + self.widget.winfo_rootx() + 57
        y = y + cy + self.widget.winfo_rooty() + 27
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry("+%d+%d" % (x, y))
        label = tk.Label(
            tw,
            text=self.text,
            justify=tk.LEFT,
            background="#ffffe0",
            relief=tk.SOLID,
            borderwidth=1,
            font=("tahoma", "8", "normal"),
        )
        label.pack(ipadx=1)

    def hidetip(self) -> None:
        """Hide the tooltip window."""
        tw = self.tipwindow
        self.tipwindow = None
        if tw:
            tw.destroy()

    @classmethod
    def create(cls, widget: tk.Widget, text: str) -> None:
        """Create and attach a ToolTip to a given widget.

        A ToolTip object is created. It holds a reference to the Widget
        and binds "mouse enter" and "mouse leave" events to ad hoc ToolTip methods.

        Parameters
        ----------
        widget : tk.Widget
            The widget documented by the ToolTip instance.
        text : str
            The text to be shown in the window.
        """
        toolTip = cls(widget)

        def enter(_: tk.Event) -> None:
            """Define a callback for "on mouse enter" event."""
            toolTip.showtip(text)

        def leave(_: tk.Event) -> None:
            """Define a callback for "on mouse leave" event."""
            toolTip.hidetip()

        widget.bind("<Enter>", enter)
        widget.bind("<Leave>", leave)
