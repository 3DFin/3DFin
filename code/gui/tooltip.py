import tkinter as tk


class ToolTip(object):
    """
    This class allows to create the mouse-hover info boxes
    see https://stackoverflow.com/questions/3221956/how-do-i-display-tooltips-in-tkinter
    """

    def __init__(self, widget: tk.Widget):
        """
        Constructor

            Parameters:
                widget (tk.Widget): the widget documented by the ToolTip instance
        """
        self.widget = widget
        self.tipwindow = None
        self.id = None
        self.x = self.y = 0

    def showtip(self, text):
        """
        Display text in tooltip window

            Parameters:
                text (str): The text to show in the window
        """
        self.text = text
        if self.tipwindow or not self.text:
            return
        x, y, _, cy = self.widget.bbox("insert")
        x = x + self.widget.winfo_rootx() + 57
        y = y + cy + self.widget.winfo_rooty() + 27
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(1)
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

    def hidetip(self):
        """Hide the tooltip window"""
        tw = self.tipwindow
        self.tipwindow = None
        if tw:
            tw.destroy()

    @classmethod
    def create(cls, widget: tk.Widget, text: str):
        """
        Attach a ToolTip to a given widget by creating a ToolTip object that hold
        a reference to the Widget and by binding mouse enter and mouse leave event
        to ad hoc ToolTip methods.

            Parameters:
                Widget (tk.Widget): the widget documented by the ToolTip instance
                text: The text to show in the window
        """
        toolTip = cls(widget)

        def enter(event):
            """callback for enter event"""
            toolTip.showtip(text)

        def leave(event):
            """callback fro leave event"""
            toolTip.hidetip()

        widget.bind("<Enter>", enter)
        widget.bind("<Leave>", leave)
