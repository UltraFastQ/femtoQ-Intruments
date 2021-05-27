"Common graphical uses in tkinter"
# Matplotlib :
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import make_axes_locatable
from matplotlib.animation import FuncAnimation
plt.ion()
# Numpy :
import numpy as np


def black_theme_graph():
    """Used to have darker theme in matplotlib pyplot"""
    plt.style.use('dark_background')


def default_theme_graph():
    """Used to have standard theme in matplotlib pyplot"""
    plt.style.use('classic')



class HorizontalDraggableLine:
    """
    This is a class to create an horizontal line that can be drag in
    a vertical fashion. Documentation of this part is not torough as it does
    not come from me. I took some part of another code and adapted it to this
    one.

    Attributes:
        parent : tkinter frame in which the matplotlib pyplot is gridded into.
        press : This attribute is a state of the draggable line it describe
        it's current state and determines if it's available to be moved around.
        background : ??
        y : This is the position on the y axis of the draggable line it is
        updated everytimes it is clicked on.
        line : This is an object from matplotlib. It consist in a straight line
        going from minus inf to inf. It inherite from the Axis class of
        matplotlib.
    """
    Lock = None

    def __init__(self, parent=None, y=0, Axis=None):
        """
        The constructor for the HorizontalDraggableLine Class.

        Parameters:
            parent : tkinter Frame object where the object is placed in.
            y : Initial position of your horizontal line on the y axis
            Axis : axis of your pyplot graphic that will contain this line.
        """
        self.parent = parent
        self.press = None
        self.background = None
        self.y = y
        self.line = Axis.axhline(y)
        self.line.set_linewidth(.2)
        # Start configuring the line to make it draggable
        self.connect()

    def connect(self):
        """
        This function connect all the events we need to control the line
        vertically

        """
        self.cidpress1 = self.line.figure.canvas.mpl_connect('button_press_event', self.on_press)
        self.cidrelease1 = self.line.figure.canvas.mpl_connect('button_release_event', self.on_release)
        self.cidmotion1 = self.line.figure.canvas.mpl_connect('motion_notify_event', self.on_motion)

    def on_press(self, event):
        """
        This function activate itself when there is a click on the line

        Parameters:
            event: An event is an object in tkinter that is created when you
            click on the screen. See the given documentation for the specifics.
            This parameter automaticly sent through when you click on the
            line.
        """
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
        """
        This function activate itself when you release the click on the line

        Parameters:
            event: An event is an object in tkinter that is created when you
            click on the screen. See the given documentation for the specifics.
            This parameter automaticly sent through when you click on the
            line.
        """
        if self.Lock is not self: return

        self.press = None
        self.Lock = None

        self.line.set_animated(False)

        self.background = None
        self.line.figure.canvas.draw()

        self.y = self.line.get_ydata()

    def on_motion(self, event):
        """
        This function activate itself once you have clicked a line and you move
        it around.

        Parameters:
            event: An event is an object in tkinter that is created when you
            click on the screen. See the given documentation for the specifics.
            This parameter automaticly sent through when you click on the
            line.
        """
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
        """
        This function if my understanding is right is to disconnect all of the
        function above from the line. Once you call this it wont be possible to
        control the line anymore.
        """
        self.cidpress1 = self.line.figure.canvas.mpl_disconnect('button_press_event', self.on_press)
        self.cidrelease1 = self.line.figure.canvas.mpl_disconnect('button_release_event', self.on_release)
        self.cidmotion1 = self.line.figure.canvas.mpl_disconnect('motion_notify_event', self.on_motion)


class VerticalDraggableLine:
    """
    This is a class to create an vertical line that can be drag in
    a vertical fashion. Documentation of this part is not torough as it does
    not come from me. I took some part of another code and adapted it to this
    one.

    Attributes:
        parent : tkinter frame in which the matplotlib pyplot is gridded into.
        press : This attribute is a state of the draggable line it describe
        it's current state and determines if it's available to be moved around.
        background : ??
        x : This is the position on the y axis of the draggable line it is
        updated everytimes it is clicked on.
        line : This is an object from matplotlib. It consist in a straight line
        going from minus inf to inf. It inherite from the Axis class of
        matplotlib.
    """
    Lock = None

    def __init__(self, parent=None, x=30, axes=None):
        """
        The constructor for the HorizontalDraggableLine Class.

        Parameters:
            parent : tkinter Frame object where the object is placed in.
            y : Initial position of your horizontal line on the y axis
            Axis : axis of your pyplot graphic that will contain this line.
        """

        self.parent = parent
        self.press = None
        self.background = None
        self.x = x
        self.line = axes.axvline(x)
        self.connect()
        if len(self.parent.line_list) == 1:
            self.BOX = axes.axvspan(self.parent.line_list[0].x, self.x, alpha=0.15)

    def connect(self):
        """
        This function connect all the events we need to control the line
        vertically

        """
        self.cidpress1 = self.line.figure.canvas.mpl_connect('button_press_event', self.on_press)
        self.cidrelease1 = self.line.figure.canvas.mpl_connect('button_release_event', self.on_release)
        self.cidmotion1 = self.line.figure.canvas.mpl_connect('motion_notify_event', self.on_motion)

    def on_press(self, event):
        """
        This function activate itself when there is a click on the line

        Parameters:
            event: An event is an object in tkinter that is created when you
            click on the screen. See the given documentation for the specifics.
            This parameter automaticly sent through when you click on the
            line.
        """
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
        """
        This function activate itself when you release the click on the line

        Parameters:
            event: An event is an object in tkinter that is created when you
            click on the screen. See the given documentation for the specifics.
            This parameter automaticly sent through when you click on the
            line.
        """

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
        """
        This function activate itself once you have clicked a line and you move
        it around.

        Parameters:
            event: An event is an object in tkinter that is created when you
            click on the screen. See the given documentation for the specifics.
            This parameter automaticly sent through when you click on the
            line.
        """
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
        """
        This function if my understanding is right is to disconnect all of the
        function above from the line. Once you call this it wont be possible to
        control the line anymore.
        """
        self.cidpress1 = self.line.figure.canvas.mpl_disconnect('button_press_event', self.on_press)
        self.cidrelease1 = self.line.figure.canvas.mpl_disconnect('button_release_event', self.on_release)
        self.cidmotion1 = self.line.figure.canvas.mpl_disconnect('motion_notify_event', self.on_motion)


class GraphicFrame:
    """
    This is a class to create a matplotlib graphic using a non-pyplot format.
    It consist in a simplification of the normally hard implementation of the
    figure into a tkinter frame.

    Attributes:
        parent : tkinter frame in which the graphic is placed in.
        Fig : Figure object of the matplotlib class analogue to pyplot.figure
        axes : Matplotlib Axis object created to plot data
        Line : Matplotlib Line object created to update data in the given axis
        canvas : Matplotlib object that generates the 'drawing' in a tkinter
        frame it is mainly used to update the graphic in real time.
        toolbar : Matplotlib toolbar normally under any pyplot graph.
    """
    def __init__(self, parent, axis_name=['', ''], figsize=[1, 1]):
        """
        The constructor for the GraphicFrame Class.

        Parameters:
            parent : tkinter Frame object where the object is placed in.
            axis_name : This is a list of two strings that will be respectivly
            the x and y axis name. (Should be Latex friendly)
            figsize : This is the initial figure size (The figure size is
            automaticly updated when the window is changed in size)
        """
        self.parent = parent
        self.Fig = Figure(dpi=100, figsize=figsize)
        # Adjusting the axis in the figure and setting up necessary parameters
        # for naming the axis
        self.axes = self.Fig.add_axes([0.1, 0.1, 0.87, 0.87])
        self.axes.set_aspect('auto', adjustable='box')
        self.axes.set_adjustable('box')
        self.Line, = self.axes.plot([], [])
        self.axes.tick_params(axis='both', which='major', labelsize=8)
        self.axes.grid()
        self.axes.set_xlabel(r'' + axis_name[0])
        self.axes.set_ylabel(r'' + axis_name[1])
        #Creating toolbar for convinience reason and canvas to host the figure
        self.canvas = FigureCanvasTkAgg(self.Fig, parent)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(expand=True, fill='both')
        self.toolbar = NavigationToolbar2Tk(self.canvas, parent)
        self.toolbar.update()
        self.canvas._tkcanvas.pack()

    def change_dimensions(self, event):
        """
        This function is a way to update the size of the figure when you change
        the size of your window automaticly it takes the width of your parent
        and the dpi of your figure to update the height and width.

        How to set it up : Your_Frame.bind('<Configure>', Your_Graph.change_dimensions)

        Parameters:
            event: An event is an object in tkinter that is created when you
            click on the screen. See the given documentation for the specifics.
            This parameter automaticly sent through when you click on the
            line.
        """
        width = event.width/self.Fig.get_dpi()
        height = event.height/self.Fig.get_dpi()
        self.Fig.set_size_inches(w=width, h=height)

    def update_graph(self):
        """
        This function is a compilation of two line to update the figure canvas
        so it update the values displayed whitout recreating the figure in the
        tkinter frame.

        """
        self.Fig.canvas.draw()
        self.Fig.canvas.flush_events()

    def destroy_graph(self):
        """
        This function is a compilation of two line to destroy a graph ie if
        you want to replace it or just get rid of it. It does not destroy the
        class itself so creating the canvas and the toolbar would make it
        appear the same way it was before.

        """
        self.canvas.get_tk_widget().destroy()
        self.toolbar.destroy()

    def log_scale(self):
        """
        This function is changing the y axis to make it a logarithmic scale.
        """
        self.axes.set_yscale('log')
        self.update_graph()

    def lin_scale(self):
        """
        This function is changing/reverting the y axis back to a linear scale.
        """
        self.axes.set_yscale('linear')
        self.update_graph()

class SubGraphFrame:
    """
    This is a class to create a matplotlib graphic using a non-pyplot format.
    It consist in a simplification of the normally hard implementation of the
    figure with subplots into a tkinter frame.

    Attributes:
        parent : tkinter frame in which the graphic is placed in.
        Fig : Figure object of the matplotlib class analogue to pyplot.figure
        axes : Matplotlib Axis object created to plot data
        Line : Matplotlib Line object created to update data in the given axis
        graph : GraphicFrame class like list of object that have the same
        propreties of the given class.
        canvas : Matplotlib object that generates the 'drawing' in a tkinter
        frame it is mainly used to update the graphic in real time.
        toolbar : Matplotlib toolbar normally under any pyplot graph.

    TODO :
        This section lacks the availability to place graph in a specific
        fashion ie 2 column and 1 row for exemple. A new iteration should
        include such feature. It could include the position of the subplot
        in the dictionnary for exemple.
    """

    def __init__(self, parent, figsize=[1, 1], subplots=None):
        """
        The constructor for the SubGraphFrame Class. This class allow to
        superpose graphic vertically in one tkinter frame.

        Parameters:
            parent : tkinter Frame object where the object is placed in.
            figsize : This is the initial figure size (The figure size is
            automaticly updated when the window is changed in size)
            subplots : This parameter is a dictionnary that contains the title
            as the key, a list of axis name of that graph key and each elements
            represents a subplot. ie {'Graph1': ['axes_x', 'axes_y'],
            'Graph2'...}

        """

        class Graph:
            """
            This is a sub-class to create GraphicFrame like interaction to
            minimize difference between SubGraphFrame and GraphicFrame
            attributes in the code.

            Attributes:
                Fig : Figure object of the matplotlib class analogue to pyplot.figure
                axes : Matplotlib Axis object created to plot data
                Line : Matplotlib Line object created to update data in the given axis
            """
            def __init__(self, fig, axes, line):
                """
                The constructor for the GraphicFrame Class.

                Parameters:
                    fig : tkinter Frame object where the object is placed in.
                    axis_name : This is a list of two strings that will be respectivly
                    the x and y axis name. (Should be Latex friendly)
                    figsize : This is the initial figure size (The figure size is
                    automaticly updated when the window is changed in size)
                """
                self.Fig = fig
                self.axes = axes
                self.Line = line

            def change_dimensions(self, event):
                """
                This function is a way to update the size of the figure when you change
                the size of your window automaticly it takes the width of your parent
                and the dpi of your figure to update the height and width.

                How to set it up : Your_Frame.bind('<Configure>', Your_Graph.change_dimensions)

                Parameters:
                    event: An event is an object in tkinter that is created when you
                    click on the screen. See the given documentation for the specifics.
                    This parameter automaticly sent through when you click on the
                    line.
                """
                width = event.width/self.Fig.get_dpi()
                height = event.height/self.Fig.get_dpi()
                self.Fig.set_size_inches(w=width, h=height)

            def update_graph(self):
                """
                This function is a compilation of two line to update the figure canvas
                so it update the values displayed whitout recreating the figure in the
                tkinter frame.

                """
                self.Fig.canvas.draw()
                self.Fig.canvas.flush_events()

            def log_scale(self):
                """
                This function is changing the y axis to make it a logarithmic scale.
                """
                self.axes.set_yscale('log')
                self.update_graph()

            def lin_scale(self):
                """
                This function is changing/reverting the y axis back to a linear scale.
                """
                self.axes.set_yscale('linear')
                self.update_graph()

        if not subplots:
            return
        # Setting up the figure size to input the subplots structure
        self.parent = parent
        self.Fig = Figure(dpi=100, figsize=figsize)
        self.graph = []
        nbr_subplots = len(subplots)
        # Enumerating all of the dictionnary elements and placing them one over
        # the other with the given axis name, and title.
        for i, sub_plot in enumerate(subplots):
            # add_subplot generate a vertically stacked subplots
            axes = self.Fig.add_subplot(nbr_subplots, 1, i+1)
            axes.set_aspect('auto', adjustable='box')
            axes.set_adjustable('box')
            # Creating Line object in each subplot
            Line, = axes.plot([], [])
            axes.tick_params(axis='both', which='major', labelsize=8)
            axes.grid()
            # Setting up the labels
            axes.set_xlabel(subplots[sub_plot][0])
            axes.set_ylabel(subplots[sub_plot][1])
            axes.set_title(sub_plot)
            # Creating the graph List that contain all of the Graph sub-class
            # object for interaction and data update
            self.graph.append(Graph(self.Fig, axes, Line))

        # This might need some adjustment as it places the axis at the right
        # place to see the graphics properly.
        self.Fig.subplots_adjust(left=0.0625, right=0.9875, bottom=0.075, top=0.9625, hspace=0.25)
        # Canvas and toolbar handling for the stacked graph
        self.canvas = FigureCanvasTkAgg(self.Fig, parent)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(expand=True, fill='both')
        self.toolbar = NavigationToolbar2Tk(self.canvas, parent)
        self.toolbar.update()
        self.canvas._tkcanvas.pack()
        for graph in self.graph:
            graph.canvas = self.canvas
            graph.toolbar = self.toolbar

    def destroy_graph(self):
        """
        This function is a compilation of two line to destroy a graph ie if
        you want to replace it or just get rid of it. It does not destroy the
        clas itself so creating the canvas and the toolbar would make it
        appear the same way it was before.

        """
        self.canvas.get_tk_widget().destroy()
        self.toolbar.destroy()


class UyeGraphFrame:
    """
    This is a class to create a matplotlib graphic using a non-pyplot format.
    It consist in a simplification of the normally hard implementation of the
    figure into a tkinter frame.

    Attributes:
        parent : tkinter frame in which the graphic is placed in.
        Fig : Figure object of the matplotlib class analogue to pyplot.figure
        axes : Matplotlib Axis object created to plot data
        Line : Matplotlib Line object created to update data in the given axis
        canvas : Matplotlib object that generates the 'drawing' in a tkinter
        frame it is mainly used to update the graphic in real time.
        toolbar : Matplotlib toolbar normally under any pyplot graph.

    TODO :
        This section is far from finished the updatable feature is still not
        working for this part. I am currently using imshow to try and update it
        but this is as far as it goes. Implementation and function remains the
        same as GraphicFrame for now.
    """

    def __init__(self, parent, axis_name=['', ''], figsize=[1, 1]):
        # axis_name is a string tuple of the x and y axis in that order
        # figsize is a list of two component the first one is the x and the other one is the y axis
        self.parent = parent
        self.Fig = Figure(dpi=100, figsize=figsize)
        self.axes = self.Fig.add_axes([0.002, 0.1, 0.87, 0.87])
        self.data = np.zeros((1000,1000))
        self.im = self.axes.imshow(self.data, vmin=0, vmax=1,
                                  origin='lower')
        self.axes.tick_params(axis='both', which='major', labelsize=8)
        self.axes.set_xlabel(r'' + axis_name[0])
        self.axes.set_ylabel(r'' + axis_name[1])
        cbar = self.Fig.colorbar(self.im, ax=self.axes,
                                 location='left', shrink=0.6)
        # Create Image on top and right of the graph
        divider = make_axes_locatable(self.axes)
        self.maxx = divider.append_axes('top', 1, pad=0, sharex=self.axes)
        self.maxy = divider.append_axes('right', 1, pad=0, sharey=self.axes)
        # Invisible label
        self.maxx.xaxis.set_tick_params(labelbottom=False)
        self.maxy.yaxis.set_tick_params(labelleft=False)
        self.maxx.set_ylim(0-1e-1, 1+1e-1)
        self.maxy.set_xlim(0-1e-1, 1+1e-1)
        self.maxlx, = self.maxx.plot(np.max(self.data, axis=0))
        self.maxly, = self.maxy.plot(np.max(self.data, axis=1),
                                np.arange(0,self.data.shape[1],1))
        self.canvas = FigureCanvasTkAgg(self.Fig, parent)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(expand=True, fill='both')
        self.toolbar = NavigationToolbar2Tk(self.canvas, parent)
        self.toolbar.update()
        self.canvas._tkcanvas.pack()

    def change_data(self,i,blit=False):
        if blit:
            axbackground = self.Fig.canvas.copy_from_bbox(self.axes.bbox)
            axxbackground = self.Fig.canvas.copy_from_bbox(self.maxx.bbox)
            axybackground = self.Fig.canvas.copy_from_bbox(self.maxy.bbox)

        self.data[i,i] = 1*np.abs(500-i)/500
        self.im.set_data(self.data)
        self.maxlx.set_ydata(np.max(self.data, axis=0))
        self.maxly.set_xdata(np.max(self.data, axis=1))
        if blit:
            self.Fig.canvas.restore_region(axbackground)
            self.Fig.canvas.restore_region(axxbackground)
            self.Fig.canvas.restore_region(axybackground)
            self.axes.draw_artist(self.im)
            self.maxx.draw_artist(self.maxlx)
            self.maxy.draw_artist(self.maxly)
            self.Fig.canvas.blit(self.axes.bbox)
            self.Fig.canvas.blit(self.maxx.bbox)
            self.Fig.canvas.blit(self.maxy.bbox)
        else:
            self.update_graph()


    def change_dimensions(self, event):
        width = event.width/self.Fig.get_dpi()
        height = event.height/self.Fig.get_dpi()
        self.Fig.set_size_inches(w=width, h=height)

    def update_graph(self):
        self.Fig.canvas.draw()
        self.Fig.canvas.flush_events()

    def destroy_graph(self):
        self.canvas.get_tk_widget().destroy()
        self.toolbar.destroy()

    def log_scale(self):
        self.axes.set_yscale('log')
        self.update_graph()

    def lin_scale(self):
        self.axes.set_yscale('linear')
        self.update_graph()


class TwoDFrame:
    """
    This is a class to create a matplotlib graphic using a non-pyplot format.
    It consist in a simplification of the normally hard implementation of the
    figure into a tkinter frame.

    Attributes:
        parent : tkinter frame in which the graphic is placed in.
        Fig : Figure object of the matplotlib class analogue to pyplot.figure
        axes : Matplotlib Axis object created to plot data
        Line : Matplotlib Line object created to update data in the given axis
        canvas : Matplotlib object that generates the 'drawing' in a tkinter
        frame it is mainly used to update the graphic in real time.
        toolbar : Matplotlib toolbar normally under any pyplot graph.

    TODO :
        This section is far from finished the updatable feature is still not
        working for this part. I am currently using imshow to try and update it
        but this is as far as it goes. Implementation and function remains the
        same as GraphicFrame for now.
    """

    def __init__(self, parent, axis_name=['', ''], figsize=[1, 1], data_size=(1000,1000), cmap='viridis',aspect=1,vmin=0,vmax=1):
        # axis_name is a string tuple of the x and y axis in that order
        # figsize is a list of two component the first one is the x and the other one is the y axis
        self.parent = parent
        self.Fig = Figure(dpi=100, figsize=figsize)
        self.axes = self.Fig.add_axes([0.1, 0.1, 0.87, 0.87])
        self.data = np.zeros(data_size)
        self.im = self.axes.imshow(self.data, vmin=vmin, vmax=vmax, cmap=cmap, aspect=aspect)
        #self.axes.tick_params(axis='both', which='major', labelsize=8)
        #self.axes.grid()
        #self.axes.set_xlabel(r'' + axis_name[0])
        #self.axes.set_ylabel(r'' + axis_name[1])
        ## Create Image on top and right of the graph
        #divider = make_axes_locatable(self.axes)
        #self.maxx = divider.append_axes('top', 1, pad=0, sharex=self.axes)
        #self.maxy = divider.append_axes('right', 1, pad=0, sharey=self.axes)
        ## Invisible label
        #self.maxx.xaxis.set_tick_params(labelbottom=False)
        #self.maxy.yaxis.set_tick_params(labelleft=False)

        self.canvas = FigureCanvasTkAgg(self.Fig, parent)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(expand=True, fill='both')
        self.toolbar = NavigationToolbar2Tk(self.canvas, parent)
        self.toolbar.update()
        self.canvas._tkcanvas.pack()

    def change_data(self,data,blit):
        if blit:
            axbackground = self.Fig.canvas.copy_from_bbox(self.axes.bbox)
            axxbackground = self.Fig.canvas.copy_from_bbox(self.maxx.bbox)
            axybackground = self.Fig.canvas.copy_from_bbox(self.maxy.bbox)
        self.data = data
        self.im.set_data(self.data)
        #self.maxlx.set_ydata(np.max(self.data, axis=0))
        #self.maxly.set_xdata(np.max(self.data, axis=1))
        if blit:
            self.Fig.canvas.restore_region(axbackground)
            self.Fig.canvas.restore_region(axxbackground)
            self.Fig.canvas.restore_region(axybackground)
            self.axes.draw_artist(self.im)
            self.maxx.draw_artist(self.maxlx)
            self.maxy.draw_artist(self.maxly)
            self.Fig.canvas.blit(self.axes.bbox)
            self.Fig.canvas.blit(self.maxx.bbox)
            self.Fig.canvas.blit(self.maxy.bbox)
        else:
            self.update_graph()


    def change_dimensions(self, event):
        """
        This function is a way to update the size of the figure when you change
        the size of your window automaticly it takes the width of your parent
        and the dpi of your figure to update the height and width.

        How to set it up : Your_Frame.bind('<Configure>', Your_Graph.change_dimensions)

        Parameters:
            event: An event is an object in tkinter that is created when you
            click on the screen. See the given documentation for the specifics.
            This parameter automaticly sent through when you click on the
            line.
        """
        width = event.width/self.Fig.get_dpi()
        height = event.height/self.Fig.get_dpi()
        self.Fig.set_size_inches(w=width, h=height)

    def update_graph(self):
        """
        This function is a compilation of two line to update the figure canvas
        so it update the values displayed whitout recreating the figure in the
        tkinter frame.

        """
        self.Fig.canvas.draw()
        self.Fig.canvas.flush_events()

    def destroy_graph(self):
        """
        This function is a compilation of two line to destroy a graph ie if
        you want to replace it or just get rid of it. It does not destroy the
        class itself so creating the canvas and the toolbar would make it
        appear the same way it was before.

        """
        self.canvas.get_tk_widget().destroy()
        self.toolbar.destroy()

    def log_scale(self):
        """
        This function is changing the y axis to make it a logarithmic scale.
        """
        self.axes.set_yscale('log')
        self.update_graph()

    def lin_scale(self):
        """
        This function is changing/reverting the y axis back to a linear scale.
        """
        self.axes.set_yscale('linear')
        self.update_graph()

