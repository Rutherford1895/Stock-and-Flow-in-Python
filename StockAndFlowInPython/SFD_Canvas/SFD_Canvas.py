from tkinter import *
from tkinter import ttk
from tkinter import filedialog
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from SFD_Canvas.model_handler import ModelHandler
from Graph_SD.graph_based_engine import STOCK, FLOW, VARIABLE, PARAMETER, ALIAS
import math
import xml.dom.minidom
import shutil
import os


def name_handler(name):
    return name.replace(' ', '_').replace('\n', '_')


class SFDCanvas(Frame):
    def __init__(self, master):
        super().__init__(master)
        self.master = master
        self.xmost = 300
        self.ymost = 300

        self.canvas = Canvas(self)
        self.canvas.configure(background='#fff')
        #self.canvas.pack(side = BOTTOM, fill = BOTH, expand = 1)

        self.hbar = Scrollbar(self, orient=HORIZONTAL)
        self.hbar.pack(side=BOTTOM, fill=X)
        self.hbar.config(command=self.canvas.xview)

        self.vbar = Scrollbar(self, orient=VERTICAL)
        self.vbar.pack(side=RIGHT, fill=Y)
        self.vbar.config(command=self.canvas.yview)

        self.createWidgets()

        self.pack(fill=BOTH, expand=1)
        self.filename = ''

        # Initialize model handler
        self.modelHandler1 = ModelHandler()

    def create_stock(self, x, y, w, h, label):
        '''
        Center x, Center y, width, height, label
        '''
        self.canvas.create_rectangle(x - w * 0.5, y - h * 0.5, x + w * 0.5, y + h * 0.5, fill="#fff")
        self.canvas.create_text(x, y + 30, anchor=CENTER, font=("Arial", 13), text=label)

    def create_flow(self, x, y, pts, r, label):
        '''
        Starting point x, y, ending point x, y, length, circle radius, label
        '''
        for i in range(len(pts)-1):
            if i != len(pts)-2:
                self.canvas.create_line(pts[i][0], pts[i][1], pts[i+1][0], pts[i+1][1])
            else:
                self.canvas.create_line(pts[i][0], pts[i][1], pts[i+1][0], pts[i+1][1], arrow=LAST)
        #self.canvas.create_line(xA, yA, xB, yB, arrow=LAST)
        self.canvas.create_oval(x - r, y - r, x + r, y + r, fill="#fff")
        self.canvas.create_text(x, y + r + 10, anchor=CENTER, font=("Arial", 13), text=label)

    def create_aux(self, x, y, r, label):
        '''
        Central point x, y, radius, label
        '''
        self.canvas.create_oval(x - r, y - r, x + r, y + r, fill="#fff")
        self.canvas.create_text(x, y + r + 10, anchor=CENTER, font=("Arial", 13), text=label)

    def create_alias(self, x, y, r, label):
        '''
        Central point x, y, radius, label
        '''
        self.canvas.create_oval(x - r, y - r, x + r, y + r, fill="gray70")
        self.canvas.create_text(x, y, anchor=CENTER, font=("Arial", 10), text="G")
        self.canvas.create_text(x, y + r + 10, anchor=CENTER, font=("Arial", 13, "italic"), text=label)

    def create_connector(self, xA, yA, xB, yB, angle, color='black'):
        # self.create_dot(xA,yA,3,'black')
        # self.create_dot(xB,yB,3,'black')
        alpha = math.radians(angle)
        if math.pi < alpha < math.pi * 2:
            alpha -= math.pi * 2
        beta = math.atan2((yA - yB), (xB - xA))  # angle between A->B and x-positive
        #print('alpha in degrees, ', math.degrees(alpha), 'beta in degrees, ', math.degrees(beta))

        # calculate the center of circle

        rad_radiusA = alpha - math.pi * 0.5  # radiant of radius of the circle going out from A
        #print('rad_radiusA (degrees), ', math.degrees(rad_radiusA), 'radians, ', rad_radiusA)
        gA = math.tan(rad_radiusA)
        #print('gradiantA, ', gA)
        if xB != xA:
            gAB = (yA - yB) / (xB - xA)  # y axis inversed, could be 'zero division'
        else:
            gAB = 99.99
        #print('gradiantAB, ', gAB)

        gM = (-1) / gAB
        #print('gradiantM, ', gM)
        xM = (xA + xB) / 2
        yM = (yA + yB) / 2
        #print("M's coordinate", xM, yM)

        xC = (yA + gA * xA - gM * xM - yM) / (gA - gM)
        yC = yA - gA * (xC - xA)
        #print("A's coordinate: ", xA, yA)
        #print("C's coordinate: ", xC, yC)

        #self.create_dot(xC, yC, 2, color, str(angle))  # draw center of the circle
        # TODO: when C and A are calculated to be the same point (and in fact not)
        rad_CA = math.atan2((yC - yA), (xA - xC))
        rad_CB = math.atan2((yC - yB), (xB - xC))

        #print('rad_CA, ', rad_CA, 'rad_CB, ', rad_CB)


        # calculate radius

        radius = (pow((xB - xC), 2) + pow((yC - yB), 2)) ** 0.5
        baseArc = math.atan2(yC - yA, xA - xC)

        #print('baseArc in degrees, ', math.degrees(baseArc))

        #print("checking youhu or liehu")
        # vectors, this part seems to be correct

        vecStarting = [math.cos(alpha), math.sin(alpha)]
        vecAtoB = [xB - xA, yA - yB]
        #print('vecStarting, ', vecStarting, 'vecAtoB, ', vecAtoB)
        angleCos = self.cosFormula(vecStarting, vecAtoB)
        #print('Cosine of the angle in Between, ', angleCos)

        # checking youhu or liehu the direction

        inverse = 1

        if angleCos < 0:  # you hu
            #print('deg_CA, ', math.degrees(rad_CA),'deg_CB',math.degrees(rad_CB))
            diff = rad_CB-rad_CA
            #print('youhu')
        else: # lie hu
            if rad_CA*rad_CB<0 and rad_CA <= rad_CB: # yi hao
                diff = rad_CB-rad_CA
                if diff > math.pi:
                    diff = abs(diff) - math.pi*2
            elif rad_CA*rad_CB<0 and rad_CA > rad_CB:
                diff = math.pi*2-rad_CA+rad_CB
                if diff > math.pi:
                    diff = diff - math.pi*2
            elif rad_CA*rad_CB>0 and rad_CA > rad_CB:
                diff = rad_CB-rad_CA
                if diff > math.pi:
                    diff = math.pi*2 - diff
            elif rad_CA*rad_CB>0 and rad_CA < rad_CB:
                diff = rad_CB-rad_CA
                if diff > math.pi:
                    diff = math.pi*2 - diff
            else:
                diff = rad_CB-rad_CA
            #print('liehu')
        #print('final diff in degrees, ', math.degrees(diff))
        # generate new points

        x = [xA]
        y = [yA]
        n = 7

        for i in range(n):
            baseArc = baseArc + diff / (n + 1) * inverse
            x1 = xC + radius * math.cos(baseArc)
            x.append(x1)
            y1 = yC - radius * math.sin(baseArc)
            y.append(y1)
            # Draw dots of the connectors, if you would like
            #self.create_dot(x1,y1,2,'gray',str(i))

        x.append(xB)
        y.append(yB)

        self.canvas.create_line(x[0], y[0], x[1], y[1], x[2], y[2], x[3], y[3], x[4], y[4], x[5], y[5], x[6], y[6],
                                x[7], y[7], x[8], y[8], smooth=True, fill='maroon2', arrow=LAST)

        print('\n')

    def create_dot(self, x, y, r, color, label=''):
        self.canvas.create_oval(x - r, y - r, x + r, y + r, outline=color, fill=color)
        self.canvas.create_text(x, y - 10, text=label)

    def cosFormula(self, a, b):

        l = 0
        m = 0
        n = 0
        for i in range(2):
            l += a[i] * b[i]
            m += a[i] ** 2
            n += b[i] ** 2
        return l / ((m * n) ** 0.5)

    def locateVar(self, name):
        name = name_handler(name)
        print("locating...")
        print(name)
        print(self.modelHandler1.sess1.structures['default'].sfd.nodes)
        for element in self.modelHandler1.sess1.structures['default'].sfd.nodes:
            if element == name:
                x = self.modelHandler1.sess1.structures['default'].sfd.nodes[element]['pos'][0]
                y = self.modelHandler1.sess1.structures['default'].sfd.nodes[element]['pos'][1]
                return [float(x), float(y)]

    def locateAlias(self, uid):
        print("locateAlias is called, locating...")
        for element in self.modelHandler1.sess1.structures['default'].sfd.nodes:
            if element == uid:
                x = self.modelHandler1.sess1.structures['default'].sfd.nodes[element]['pos'][0]
                y = self.modelHandler1.sess1.structures['default'].sfd.nodes[element]['pos'][1]
                return [float(x), float(y)]

    # Here starts Widgets and Commands

    def createWidgets(self):
        fm_1 = Frame(self.master)
        fm_1.configure(background="#fff")
        self.lb = Label(fm_1, text='Display System Dynamics Model', background="#fff")
        self.lb.pack()
        fm_1.pack(side=TOP)

        fm_2 = Frame(fm_1)
        fm_2.configure(background="#fff")
        self.btn1 = Button(fm_2, text="Select model", command=self.fileLoad)
        self.btn1.pack(side=LEFT)
        self.btn_run = Button(fm_2, text="Run_pysd", command=self.simulationHandler)
        self.btn_run.pack(side=LEFT)
        # self.btn_run1 = Button(fm_2, text="Run_graph", command=None)
        # self.btn_run1.pack(side=LEFT)
        self.comboxlist = ttk.Combobox(fm_2)
        self.variablesInModel = ["Variable"]
        self.comboxlist["values"] = self.variablesInModel
        self.comboxlist.current(0)
        self.comboxlist.bind("<<ComboboxSelected>>", self.selectVariable)
        self.comboxlist.pack(side=LEFT)
        self.btn3 = Button(fm_2, text="Show Figure", command=self.showFigure)
        self.btn3.pack(side=LEFT)
        self.btn4 = Button(fm_2, text="Reset canvas", command=self.resetCanvas)
        self.btn4.pack(side=LEFT)
        fm_2.pack(side=TOP)

    def fileLoad(self):
        self.filename = filedialog.askopenfilename()
        if self.filename != '':
            self.lb.config(text="File selected: " + self.filename)
            self.modelHandler1.read_xmile_model(self.filename)
            self.modelDrawer()

        else:
            self.lb.config(text="No file is selected.")

    def resetCanvas(self):
        self.canvas.delete('all')
        self.lb.config(text='Load and display a Stella SD Model')
        self.variablesInModel = ["Variable"]
        self.comboxlist["values"] = self.variablesInModel
        self.comboxlist.current(0)
        self.xmost = 300
        self.ymost = 300
        self.canvas.config(width=self.xmost, height=self.ymost, scrollregion=(0, 0, self.xmost, self.ymost))

    def fileHandler(self, filename):
        DOMTree = xml.dom.minidom.parse(filename)
        #self.DOMTree = xml.dom.minidom.parse("./sample_models/reindeerModel.stmx")
        self.model = DOMTree.documentElement

    def modelDrawer(self):
        # now starts the 'drawing' part
        self.canvas.config(width=self.xmost, height=self.ymost, scrollregion=(0, 0, self.xmost, self.ymost))

        #self.canvas.config(width = wid, height = hei)
        self.canvas.config(xscrollcommand=self.hbar.set, yscrollcommand=self.vbar.set)

        # set common parameters
        width1 = 46
        height1 = 35
        length1 = 115
        radius1 = 8

        for connector in self.modelHandler1.sess1.structures['default'].sfd.edges():
            print(connector)
            from_element = connector[0]
            to_element = connector[1]
            from_cord = self.locateVar(from_element)
            print(from_cord)
            to_cord = self.locateVar(to_element)
            print(to_cord)
            angle = self.modelHandler1.sess1.structures['default'].sfd[from_element][to_element][0]['angle']
            print('angle:', angle)
            self.create_connector(from_cord[0], from_cord[1], to_cord[0], to_cord[1]-8, angle)

        # draw stocks
        for element in self.modelHandler1.sess1.structures['default'].sfd.nodes:
            #print(element)
            #print(self.modelHandler1.sess1.structures['default'].sfd.nodes.data())
            #print(self.modelHandler1.sess1.structures['default'].sfd.nodes[element])
            #print("This element: ", element)
            #print("These elements:", self.modelHandler1.sess1.structures['default'].sfd.nodes)
            if self.modelHandler1.sess1.structures['default'].sfd.nodes[element]['element_type'] == STOCK:
                x = self.modelHandler1.sess1.structures['default'].sfd.nodes[element]['pos'][0]
                y = self.modelHandler1.sess1.structures['default'].sfd.nodes[element]['pos'][1]
                #print(x,y)
                self.create_stock(x, y, width1, height1, element)
                if x > self.xmost:
                    self.xmost = x
                if y > self.ymost:
                    self.ymost = y

        # draw flows
        for element in self.modelHandler1.sess1.structures['default'].sfd.nodes:
            if self.modelHandler1.sess1.structures['default'].sfd.nodes[element]['element_type'] == FLOW:
                x = self.modelHandler1.sess1.structures['default'].sfd.nodes[element]['pos'][0]
                y = self.modelHandler1.sess1.structures['default'].sfd.nodes[element]['pos'][1]
                points = self.modelHandler1.sess1.structures['default'].sfd.nodes[element]['points']
                self.create_flow(x, y, points, radius1, element)
                if x > self.xmost:
                    self.xmost = x
                if y > self.ymost:
                    self.ymost = y

        # draw auxs
        for element in self.modelHandler1.sess1.structures['default'].sfd.nodes:
            if self.modelHandler1.sess1.structures['default'].sfd.nodes[element]['element_type'] in [PARAMETER, VARIABLE]:
                x = self.modelHandler1.sess1.structures['default'].sfd.nodes[element]['pos'][0]
                y = self.modelHandler1.sess1.structures['default'].sfd.nodes[element]['pos'][1]
                self.create_aux(x, y, radius1, element)
                if x > self.xmost:
                    self.xmost = x
                if y > self.ymost:
                    self.ymost = y

        for element in self.modelHandler1.sess1.structures['default'].sfd.nodes:
            if self.modelHandler1.sess1.structures['default'].sfd.nodes[element]['element_type'] == ALIAS:
                x = self.modelHandler1.sess1.structures['default'].sfd.nodes[element]['pos'][0]
                y = self.modelHandler1.sess1.structures['default'].sfd.nodes[element]['pos'][1]
                of_element = self.modelHandler1.sess1.structures['default'].sfd.nodes[element]['function']
                self.create_alias(x, y, radius1, of_element)
                if x > self.xmost:
                    self.xmost = x
                if y > self.ymost:
                    self.ymost = y

        self.xmost += 150
        self.ymost += 100
        print('Xmost,', self.xmost, 'Ymost,', self.ymost)
        self.canvas.config(width=self.xmost, height=self.ymost, scrollregion=(0, 0, self.xmost, self.ymost))
        self.canvas.pack(side=LEFT, expand=1, fill=BOTH)

    # Here starts the simulation part

    def simulationHandler(self):

        import pysd

        if self.filename != '':
            new_name = self.filename[:-5]+".xmile"
            shutil.copy(self.filename, new_name)
            self.model_run = pysd.read_xmile(new_name)
            os.remove(new_name)
            # os.remove(new_name[:-6]+".py")
            self.results = self.model_run.run()
            print("Simulation Finished.")
            self.variablesInModel = self.results.columns.values.tolist()
            self.variablesInModel.remove("TIME")
            self.comboxlist["values"] = self.variablesInModel

    def selectVariable(self, *args):
        self.selectedVariable = self.comboxlist.get()

    def showFigure(self):
        f = Figure(figsize=(5, 4), dpi=100)
        a = f.add_subplot(111)
        x = self.results['TIME'].tolist()
        y = self.results[self.selectedVariable].tolist()
        a.plot(x, y)
        a.set_title(self.selectedVariable)
        a.set_xlabel('Time')
        a.set_ylabel(self.selectedVariable)

        figure1 = GraphWindow(self.selectedVariable, f)


class GraphWindow():
    def __init__(self, title, figure):
        top = Toplevel()
        top.title = title
        graph = FigureCanvasTkAgg(figure, master=top)
        graph.draw()
        graph._tkcanvas.pack()
