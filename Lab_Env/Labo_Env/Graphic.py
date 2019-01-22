
# Matplotlib :
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

plt.ion()


class HorizontalDraggableLine:
    Lock = None

    def __init__(self, parent=None, y=0, Axis=None):

        self.parent = parent
        self.press = None
        self.background = None
        self.y = y
        self.line = Axis.axhline(y)
        self.line.set_linewidth(.2)
        self.connect()

    def connect(self):

        'connect to all the events we need'

        self.cidpress1 = self.line.figure.canvas.mpl_connect('button_press_event', self.on_press)
        self.cidrelease1 = self.line.figure.canvas.mpl_connect('button_release_event', self.on_release)
        self.cidmotion1 = self.line.figure.canvas.mpl_connect('motion_notify_event', self.on_motion)

    def on_press(self, event):

        if event.inaxes != self.line.axes: return
        if self.Lock is not None: return
        contains, attrd = self.line.contains(event)
        if contains != True: return
        self.press = (self.line.get_xydata()), event.xdata, event.ydata
        self.Lock = self

        canvas = self.line.figure.canvas
        axes = self.line.axes
        self.line.set_animated(True)

        canvas.draw()
        self.background = canvas.copy_from_bbox(self.line.axes.bbox)
        axes.draw_artist(self.line)

        canvas.blit(axes.bbox)

    def on_release(self, event):

        if self.Lock is not self: return

        self.press = None
        self.Lock = None

        self.line.set_animated(False)

        self.background = None
        self.line.figure.canvas.draw()

        self.y = self.line.get_ydata()

    def on_motion(self, event):
        if self.Lock is not self: return
        if event.inaxes != self.line.axes: return
        array, xpress, ypress = self.press
        y0 = array[0][0]
        dy = event.ydata - ypress
        self.line.set_ydata(y0 + dy)

        canvas = self.line.figure.canvas
        axes = self.line.axes
        canvas.restore_region(self.background)

        axes.draw_artist(self.line)
        self.y = self.line.get_ydata()

        canvas.blit(axes.bbox)

    def disconnect(self):

        self.cidpress1 = self.line.figure.canvas.mpl_disconnect('button_press_event', self.on_press)
        self.cidrelease1 = self.line.figure.canvas.mpl_disconnect('button_release_event', self.on_release)
        self.cidmotion1 = self.line.figure.canvas.mpl_disconnect('motion_notify_event', self.on_motion)


class VerticalDraggableLine:

    Lock = None

    def __init__(self, parent=None, x=30, axes=None):

        self.parent = parent
        self.press = None
        self.background = None
        self.x = x
        self.line = axes.axvline(x)
        self.connect()
        if len(self.parent.line_list) == 1:
            self.BOX = axes.axvspan(self.parent.line_list[0].x, self.x, alpha=0.15)

    def connect(self):

        'connect to all the events we need'

        self.cidpress1 = self.line.figure.canvas.mpl_connect('button_press_event', self.on_press)
        self.cidrelease1 = self.line.figure.canvas.mpl_connect('button_release_event', self.on_release)
        self.cidmotion1 = self.line.figure.canvas.mpl_connect('motion_notify_event', self.on_motion)

    def on_press(self, event):

        if event.inaxes != self.line.axes: return
        if self.Lock is not None: return
        contains, attrd = self.line.contains(event)
        if contains != True: return
        self.press = (self.line.get_xydata()), event.xdata, event.ydata
        self.Lock = self

        canvas = self.line.figure.canvas
        axes = self.line.axes
        self.line.set_animated(True)
        if self == self.parent.line_list[1]:
            self.BOX.set_animated(True)
        else:
            self.parent.line_list[1].BOX.set_animated(True)

        canvas.draw()
        self.background = canvas.copy_from_bbox(self.line.axes.bbox)
        axes.draw_artist(self.line)

        canvas.blit(axes.bbox)

    def on_release(self, event):

        if self.Lock is not self: return

        self.press = None
        self.Lock = None

        self.line.set_animated(False)
        if self == self.parent.line_list[1]:
            self.BOX.set_animated(False)
        else:
            self.parent.line_list[1].BOX.set_animated(False)

        self.background = None
        self.line.figure.canvas.draw()

        self.x = self.line.get_xdata()

    def on_motion(self, event):
        if self.Lock is not self: return
        if event.inaxes != self.line.axes: return
        array, xpress, ypress = self.press
        x0 = array[0][0]
        dx = event.xdata - xpress
        self.line.set_xdata(x0 + dx)

        canvas = self.line.figure.canvas
        axes = self.line.axes
        canvas.restore_region(self.background)

        axes.draw_artist(self.line)
        if self == self.parent.line_list[1]:
            axes.draw_artist(self.BOX)
        else:
            self.parent.line_list[1].BOX.set_animated(True)
            axes.draw_artist(self.parent.line_list[1].BOX)
        self.x = self.line.get_xdata()

        if self == self.parent.line_list[1]:
            xmin = self.parent.line_list[0].x
            width = self.x - self.parent.line_list[0].x
            array = [[xmin, 0], [xmin, 1], [xmin + width, 1], [xmin + width, 0], [xmin, 0]]
            self.BOX.set_xy(array)
        else:
            xmin = self.x
            width = self.parent.line_list[1].x - self.x
            array = [[xmin, 0], [xmin, 1], [xmin + width, 1], [xmin + width, 0], [xmin, 0]]
            self.parent.line_list[1].BOX.set_xy(array)

        canvas.blit(axes.bbox)

    def disconnect(self):

        self.cidpress1 = self.line.figure.canvas.mpl_disconnect('button_press_event', self.on_press)
        self.cidrelease1 = self.line.figure.canvas.mpl_disconnect('button_release_event', self.on_release)
        self.cidmotion1 = self.line.figure.canvas.mpl_disconnect('motion_notify_event', self.on_motion)


class GraphicFrame:

    def __init__(self, parent, axis_name=['', ''], figsize=[1, 1]):
        # axis_name is a string tuple of the x and y axis in that order
        # figsize is a list of two component the first one is the x and the other one is the y axis
        self.parent = parent
        self.Fig = Figure(dpi=100, figsize=figsize)
        self.axes = self.Fig.add_axes([0.1, 0.1, 0.87, 0.87])
        self.axes.set_aspect('auto', adjustable='box')
        self.axes.set_adjustable('box')
        self.Line, = self.axes.plot([], [])
        self.axes.tick_params(axis='both', which='major', labelsize=8)
        self.axes.grid()
        self.axes.set_xlabel(axis_name[0])
        self.axes.set_ylabel(axis_name[1])
        self.canvas = FigureCanvasTkAgg(self.Fig, parent)
        self.canvas.show()
        self.canvas.get_tk_widget().pack(expand=True, fill='both')
        toolbar = NavigationToolbar2TkAgg(self.canvas, parent)
        toolbar.update()
        self.canvas._tkcanvas.pack()

    def change_dimensions(self, event):
        width = event.width/self.Fig.get_dpi()
        height = event.height/self.Fig.get_dpi()
        self.Fig.set_size_inches(w=width, h=height)

    def update_graph(self):
        self.Fig.canvas.draw()
        self.Fig.canvas.flush_events()


class SubGraphFrame:

    def __init__(self, parent, axis_name=['', ''], figsize=[1, 1]):
        # axis_name is a string tuple of the x and y axis in that order
        # figsize is a list of two component the first one is the x and the other one is the y axis
        self.parent = parent
        self.Fig = Figure(dpi=100, figsize=figsize)
        self.axes = self.Fig.add_axes([0.1, 0.1, 0.87, 0.87])
        self.axes.set_aspect('auto', adjustable='box')
        self.axes.set_adjustable('box')
        self.Line, = self.axes.plot([], [])
        self.axes.tick_params(axis='both', which='major', labelsize=8)
        self.axes.grid()
        self.axes.set_xlabel(axis_name[0])
        self.axes.set_ylabel(axis_name[1])
        self.canvas = FigureCanvasTkAgg(self.Fig, parent)
        self.canvas.show()
        self.canvas.get_tk_widget().pack(expand=True, fill='both')
        toolbar = NavigationToolbar2TkAgg(self.canvas, parent)
        toolbar.update()
        self.canvas._tkcanvas.pack()

    def change_dimensions(self, event):
        width = event.width/self.Fig.get_dpi()
        height = event.height/self.Fig.get_dpi()
        self.Fig.set_size_inches(w=width, h=height)

    def update_graph(self):
        self.Fig.canvas.draw()
        self.Fig.canvas.flush_events()
