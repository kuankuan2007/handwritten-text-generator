from PIL import Image,ImageFont,ImageTk,ImageColor
from handright import Template,handwrite
import tkinter
from tkinter import messagebox,ttk,colorchooser,filedialog
import logging
import tempfile
import os
from time import time,localtime,strftime
import matplotlib.font_manager
import threading
import sys
import json
import yaml
import subprocess
from webbrowser import open as webbrowserOpen
from platform import platform
sys_platform = platform().lower()
def resource_path(relative_path):
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        #base_path = os.path.abspath(".")
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)
class FloatVar(tkinter.Variable):
    """Value holder for integer variables."""
    _default = 0

    def __init__(self, master=None, value=None, name=None):
        """Construct an integer variable.

        MASTER can be given as master widget.
        VALUE is an optional value (defaults to 0)
        NAME is an optional Tcl name (defaults to PY_VARnum).

        If NAME matches an existing variable and VALUE is omitted
        then the existing value is retained.
        """
        tkinter.Variable.__init__(self, master, value, name)

    def get(self):
        """Return the value of the variable as an integer."""
        value = self._tk.globalgetvar(self._name)
        try:
            return self._tk.getint(value)
        except (TypeError, tkinter.TclError):
            return self._tk.getdouble(value)

fonts=dict(sorted({f.name:f.fname for f in matplotlib.font_manager.fontManager.ttflist}.items(),key=lambda x:x[0]))

dateFormater="%Y-%m-%d %H:%M:%S"
logFormater="[%(asctime)s] [%(name)s] [%(threadName)s] [Line%(lineno)d] [%(levelname)s]: %(message)s"

fh = logging.FileHandler('log.txt')
ch = logging.StreamHandler()
logging.basicConfig(level=logging.DEBUG,format=logFormater,datefmt=dateFormater,handlers=[ch,fh])

launcherLog = logging.getLogger('Launcher')
launcherLog.info("initializated successfully")

tempfiles=os.path.join(tempfile.gettempdir(),"kuankuan/manuscript/",str(int(time()*1000)))
os.makedirs(tempfiles)

launcherLog.info("临时文件保存位置:"+tempfiles)

images=[Image.new("RGB",(400,600),"#888888")]

launcherLog.info("基本背景图片生成成功")



def resetEntry(entry,text="",readonly=False):
    entry.config(state="normal")
    entry.delete(0,tkinter.END)
    entry.insert(0,text)
    if readonly:
        entry.config(state="readonly")
    return entry

def easyGrid(ele,*args,**kwg):
    ele.grid(*args,**kwg)
    return ele

def easyBindScale(ele,command):
    ele.bind("<Return>", command)
    ele.bind("<FocusOut>", command)
    return ele
mainScreen = tkinter.Tk()
mainScreen.title("手写文字生成器")
mainScreen.resizable(height=False,width=False)
notebook = ttk.Notebook(mainScreen)
bgArgsBox=tkinter.Frame(notebook)
fontArgsBox=tkinter.Frame(notebook)
textBox=tkinter.Frame(notebook)



notebook.add(fontArgsBox, text='字体')
notebook.add(textBox, text='文本')
notebook.add(bgArgsBox, text='背景')
notebook.grid(column=0, row=0,sticky="WN")



changeScaleLog = logging.getLogger('ChangeScale')
def changeBgScale(value,li,num,name):
    changeScaleLog.debug("%s is change -> %d"%(name,float(value)))
    resetEntry(li[num][1],str(int(float(value))))
def changeBgEntry(value,li,num,name):
    loger=logging.getLogger(name)
    try:
        newValue=int(li[num][1].get())
    except BaseException as err:
        loger.debug("Wrong value :%s ->reset"%(li[num][1].get()))
        resetEntry(li[num][1],str(int(float(li[num][0].get()))))
    else:
        loger.debug("Enter value :%d ->upload"%(newValue))
        li[num][0].set(newValue)


class Colors(tkinter.Label):
    def __init__(self,*arg,logName="Colors",disabled=False,**kw):
        self.loger=logging.getLogger(logName)
        self.logName=logName
        kw["width"]=kw.get("width",4)
        kw["height"]=kw.get("height",1)
        kw["text"]=""
        kw["cursor"]=kw.get("cursor","hand2")
        kw["background"]=kw.get("value","#000000")
        if "variable" in kw:
            self.variable=kw["variable"]
            kw["background"]=self.variable.get()
            del kw["variable"]
        else:
            self.variable=tkinter.StringVar(value="#000000")
        tkinter.Label.__init__(self,*arg,**kw)
        self.variable.trace_variable("w",self._upload)
        self.disabled=disabled
        if disabled:self.disable()
        else:self.active()
        self.bind("<ButtonRelease-1>",self.chooseNewColor)
    def chooseNewColor(self,event=None):
        if self.disabled:
            return
        retsult=colorchooser.askcolor(initialcolor=self.variable.get())[1]
        if retsult:
            self.variable.set(retsult)
    def _upload(self,*args,**kw):
        if self.disabled:
            self.config(background="#888888")
            self.loger.warning("%s cannot be changed"%(self.logName))
        else:
            self.loger.debug("%s change -> %s"%(self.logName,self.variable.get()))
            self.config(background=self.variable.get())
    def disable(self):
        self.loger.debug("Disable")
        self.disabled=True
        self.config(background="#888888",cursor="X_cursor")
    def active(self):
        self.loger.debug("Active")
        self.disabled=False
        self.config(background=self.variable.get(),cursor="hand2")
class FileDroper(ttk.Entry):
    def __init__(self,*arg,logName="FileDroper",title="请选择文件",fileType=[("文件",["*.*"])],disabled=False,**kw):
        self.loger=logging.getLogger(logName)
        self.fileType=fileType
        self.title=title
        self.disabled=disabled
        self.logName=logName
        kw["state"]=kw.get("state","readonly")
        kw["cursor"]=kw.get("cursor","hand2")
        tkinter.Entry.__init__(self,*arg,**kw)
        if disabled:self.disable()
        else:self.active()
        self.bind("<ButtonRelease-1>",self.chooseNewFile)
    def chooseNewFile(self,event=None):
        if self.disabled:
            return
        retsult=filedialog.askopenfilename(title=self.title,filetypes=self.fileType)
        if retsult:
            self.loger.debug("%s change -> %s"%(self.logName,retsult))
            resetEntry(self,retsult,True)
    def disable(self):
        self.loger.debug("Disable")
        self.disabled=True
        self.config(state="disabled")
        self.config(background="#888888",cursor="X_cursor")
    def active(self):
        self.loger.debug("Active")
        self.disabled=False
        self.config(state="normal")
        self.config(background="#ffffff",cursor="hand2")
class EntryWithScale(tkinter.Frame):
    def __init__(self,master,name,variable,from_,to,length=200,precision=0):
        tkinter.Frame.__init__(self,master)
        self.name = name
        self.logger = logging.getLogger(name)
        self.variable = variable
        self.variable.trace_variable("w",self.upload)
        self.precision=precision
        self.entry=resetEntry(ttk.Entry(self,width=5),str(round(variable.get(),self.precision)))
        self.entry.grid(row=0,column=0)
        self.entry.bind("<Return>",self._entryUpload)
        self.entry.bind("<Return>",self._entryUpload)
        self.scale=ttk.Scale(self,from_=from_,to=to,variable=self.variable,command=self._scaleUpload,length=length)
        self.scale.grid(row=0,column=1)
    def _entryUpload(self,event):
        try:
            newValue=float(self.entry.get())
        except BaseException as err:
            self.logger.debug("Wrong entry value :%s ->reset"%(self.entry.get()))
            resetEntry(self.entry,str(round(self.variable.get(),self.precision)))
        else:
            self.logger.debug("Enter value :%d ->upload"%(newValue))
            self.scale.set(newValue)
    def _scaleUpload(self,value):
        self.logger.debug("scale is change -> %f"%(float(value)))
        resetEntry(self.entry,str(round(self.variable.get(),self.precision)))
    def upload(self,*args):
        resetEntry(self.entry,str(round(self.variable.get(),self.precision)))
        self.scale.set(self.variable.get())
    def disable(self):
        self.logger.debug("Disable")
        self.entry.config(state="disabled")
        self.scale.config(state="disabled")
    def active(self):
        self.logger.debug("Active")
        self.entry.config(state="normal")
        self.scale.config(state="normal")

def changeBgType():
    changeBgTypeLog=logging.getLogger('changeBgType')
    if bgArgs["bgType"].get():
        changeBgTypeLog.debug("background type -> File")
        bgArgsControler[3][0].disable()
        bgArgsControler[1][0].disable()
        bgArgsControler[2][0].disable()
        bgArgsControler[4][0].active()
    else:
        changeBgTypeLog.debug("background type -> Normal")
        bgArgsControler[3][0].active()
        bgArgsControler[1][0].active()
        bgArgsControler[2][0].active()
        bgArgsControler[4][0].disable()
bgArgs={
    "bgSize":[tkinter.IntVar(mainScreen,value=1240),tkinter.IntVar(mainScreen,value=1754)],
    "bgColor":tkinter.StringVar(mainScreen,value="#ffffff"),
    "bgFile":tkinter.StringVar(mainScreen,value=""),
    "bgType":tkinter.IntVar(mainScreen,value=0),
}
tkinter.Label(bgArgsBox,text="类型").grid(row=0,column=0,sticky="W")
tkinter.Label(bgArgsBox,text="宽度").grid(row=1,column=0,sticky="W")
tkinter.Label(bgArgsBox,text="高度").grid(row=2,column=0,sticky="W")
tkinter.Label(bgArgsBox,text="颜色").grid(row=3,column=0,sticky="W")
tkinter.Label(bgArgsBox,text="图片").grid(row=4,column=0,sticky="W")

bgArgsControler=[
    [
        easyGrid(ttk.Radiobutton(bgArgsBox,text='纯色',variable=bgArgs["bgType"],value=0,command=changeBgType),row=0,column=1,sticky="W"),
        easyGrid(ttk.Radiobutton(bgArgsBox,text='文件',variable=bgArgs["bgType"],value=1,command=changeBgType),row=0,column=2,sticky="W")
    ],
    [
        easyGrid(EntryWithScale(bgArgsBox,from_=100,to=5000,variable=bgArgs["bgSize"][0],name="图片高度"),row=1,column=1,columnspan=2,sticky="W"),
    ],
    [
        easyGrid(EntryWithScale(bgArgsBox,from_=100,to=5000,variable=bgArgs["bgSize"][1],name="图片高度"),row=2,column=1,columnspan=2,sticky="W"),
    ],
    [
        easyGrid(Colors(bgArgsBox,width=10,logName="背景颜色",variable=bgArgs["bgColor"]),row=3,column=1,columnspan=2,sticky="W")
    ],
    [
        easyGrid(FileDroper(bgArgsBox,logName="背景图片",textvariable=bgArgs["bgFile"],disabled=True,width=35,title="请选择背景图片",fileType=[("图片",[".png",".jpg",".bmp",".gif",".wedp",".tiff",".ico",".pcd",".tga"])]),row=4,column=1,sticky="W",columnspan=2)
    ]
]
bgArgsControler[0][1].bind("<Return>",lambda value:changeBgEntry(value,bgArgsControler,0,"123"))

tkinter.Label(fontArgsBox,text="字体").grid(row=0,column=0,sticky="W")
tkinter.Label(fontArgsBox,text="颜色").grid(row=1,column=0,sticky="W")
tkinter.Label(fontArgsBox,text="字号").grid(row=2,column=0,sticky="W")
tkinter.Label(fontArgsBox,text="字号扰动").grid(row=3,column=0,sticky="W")
tkinter.Label(fontArgsBox,text="行间距").grid(row=4,column=0,sticky="W")
tkinter.Label(fontArgsBox,text="行间距扰动").grid(row=5,column=0,sticky="W")
tkinter.Label(fontArgsBox,text="字间距").grid(row=6,column=0,sticky="W")
tkinter.Label(fontArgsBox,text="字间距扰动").grid(row=7,column=0,sticky="W")
tkinter.Label(fontArgsBox,text="笔画横向扰动").grid(row=8,column=0,sticky="W")
tkinter.Label(fontArgsBox,text="笔画纵向扰动").grid(row=9,column=0,sticky="W")
tkinter.Label(fontArgsBox,text="笔画旋转扰动").grid(row=10,column=0,sticky="W")
tkinter.Label(fontArgsBox,text="上间距").grid(row=11,column=0,sticky="W")
tkinter.Label(fontArgsBox,text="下间距").grid(row=12,column=0,sticky="W")
tkinter.Label(fontArgsBox,text="左间距").grid(row=13,column=0,sticky="W")
tkinter.Label(fontArgsBox,text="右间距").grid(row=14,column=0,sticky="W")
tkinter.Label(fontArgsBox,text="行首屏蔽").grid(row=15,column=0,sticky="W")

fontArgs={
    "fontFamily":tkinter.StringVar(mainScreen,value=""),
    "color":tkinter.StringVar(mainScreen,value="#000000"),
    "fontSize":tkinter.IntVar(mainScreen,32),
    "fontSizeSigma":FloatVar(mainScreen,3.0),
    "lineSpacing":FloatVar(mainScreen,32.0),
    "lineSpacingSigma":FloatVar(mainScreen,2.0),
    "wordSpacing":FloatVar(mainScreen,2.0),
    "wordSpacingSigma":FloatVar(mainScreen,1.0),
    "perturbXSigma":FloatVar(mainScreen,0.3),
    "perturbYSigma":FloatVar(mainScreen,0.3),
    "perturbThetaSigma":FloatVar(mainScreen,0.1),
    "topMargin":FloatVar(mainScreen,100.0),
    "bottomMargin":FloatVar(mainScreen,100.0),
    "leftMargin":FloatVar(mainScreen,100.0),
    "rightMargin":FloatVar(mainScreen,100.0),
    "endChars":tkinter.StringVar(mainScreen,value="，。,.;\"\'?？!！")
}

def changeFontFamily(*args):
    logging.getLogger("changeFontFamily").debug("fontFamily change -> %s(%s)"%(fontArgs["fontFamily"].get(),fonts[fontArgs["fontFamily"].get()]))
def changeEndChars(*args):
    logging.getLogger("changeEndChars").debug("endChars change -> %s"%fontArgs["endChars"].get())
def changeFontSize(*args):
    fontArgsControler[4][0].scale.config(from_=fontArgs["fontSize"].get())
    if fontArgs["lineSpacing"].get()<fontArgs["fontSize"].get():
        fontArgs["lineSpacing"].set(fontArgs["fontSize"].get())
def chooseOtherFont():
    chooseOtherFontLog=logging.getLogger("chooseOtherFont")
    chooseOtherFontLog.debug("等待用户选择")
    retsult=filedialog.askopenfilename(title="请选择文件",filetypes=[("字体文件",[".ttf",".otf"]),("任意文件","*.*")])
    if not retsult:
        chooseOtherFontLog.debug("用户取消了导入")
        return
    filename=os.path.basename(retsult)
    chooseOtherFontLog.debug("路径%s 文件%s"%(retsult,filename))
    fonts[filename]=retsult
    fontArgs["fontFamily"].set(filename)
fontArgs["fontFamily"].trace_variable("w",changeFontFamily)
fontArgs["endChars"].trace_variable("w",changeEndChars)
fontArgs["fontSize"].trace_variable("w",changeFontSize)
fontFamilyChooserBox=easyGrid(tkinter.Frame(fontArgsBox),row=0,column=1,columnspan=2,sticky="W")
fontArgsControler=[
    [
        
        easyGrid(resetEntry(ttk.Combobox(fontFamilyChooserBox,textvariable=fontArgs["fontFamily"],width=20,values=list(fonts.keys()),state="readonly"),list(fonts.keys())[0],True),row=0,column=0,sticky="W"),
        easyGrid(ttk.Button(fontFamilyChooserBox,text="其他",command=chooseOtherFont),row=0,column=1,sticky="W")
    ],
    [
        easyGrid(Colors(fontArgsBox,logName="文字颜色",width=10,variable=fontArgs["color"]),row=1,column=1,columnspan=2,sticky="W")
    ],
    [
        easyGrid(EntryWithScale(fontArgsBox,from_=4,to=72,variable=fontArgs["fontSize"],name="字号"),row=2,column=1,columnspan=2,sticky="W"),
    ],
    [
        easyGrid(EntryWithScale(fontArgsBox,from_=0,to=10,variable=fontArgs["fontSizeSigma"],name="字号扰动",precision=2),row=3,column=1,columnspan=2,sticky="W"),
    ],
    [
        easyGrid(EntryWithScale(fontArgsBox,from_=1,to=100,variable=fontArgs["lineSpacing"],name="行间距",precision=2),row=4,column=1,columnspan=2,sticky="W"),
    ],
    [
        easyGrid(EntryWithScale(fontArgsBox,from_=0,to=10,variable=fontArgs["lineSpacingSigma"],name="行间距扰动",precision=2),row=5,column=1,columnspan=2,sticky="W"),
    ],
    [
        easyGrid(EntryWithScale(fontArgsBox,from_=1,to=100,variable=fontArgs["wordSpacing"],name="字间距",precision=2),row=6,column=1,columnspan=2,sticky="W"),
    ],
    [
        easyGrid(EntryWithScale(fontArgsBox,from_=0,to=10,variable=fontArgs["wordSpacingSigma"],name="字间距扰动",precision=2),row=7,column=1,columnspan=2,sticky="W"),
    ],
    [
        easyGrid(EntryWithScale(fontArgsBox,from_=0,to=1,variable=fontArgs["perturbXSigma"],name="笔画横向扰动",precision=2),row=8,column=1,columnspan=2,sticky="W"),
    ],
    [
        easyGrid(EntryWithScale(fontArgsBox,from_=0,to=1,variable=fontArgs["perturbYSigma"],name="笔画纵向扰动",precision=2),row=9,column=1,columnspan=2,sticky="W"),
    ],
    [
        easyGrid(EntryWithScale(fontArgsBox,from_=0,to=1,variable=fontArgs["perturbThetaSigma"],name="笔画旋转扰动",precision=2),row=10,column=1,columnspan=2,sticky="W"),
    ],
    [
        easyGrid(EntryWithScale(fontArgsBox,from_=0,to=200,variable=fontArgs["topMargin"],name="上间距",precision=2),row=11,column=1,columnspan=2,sticky="W"),
    ],
    [
        easyGrid(EntryWithScale(fontArgsBox,from_=0,to=200,variable=fontArgs["bottomMargin"],name="下间距",precision=2),row=12,column=1,columnspan=2,sticky="W"),
    ],
    [
        easyGrid(EntryWithScale(fontArgsBox,from_=0,to=200,variable=fontArgs["leftMargin"],name="左间距",precision=2),row=13,column=1,columnspan=2,sticky="W"),
    ],
    [
        easyGrid(EntryWithScale(fontArgsBox,from_=0,to=200,variable=fontArgs["rightMargin"],name="右间距",precision=2),row=14,column=1,columnspan=2,sticky="W"),
    ],
    [
        easyGrid(ttk.Entry(fontArgsBox,textvariable=fontArgs["endChars"],width=35),row=15,column=1,columnspan=2,sticky="W"),
    ]
]

textScrollbar=easyGrid(ttk.Scrollbar(textBox),row=0,column=1,sticky="NSW")
textInput=easyGrid(tkinter.Text(textBox,width=45,height=30,yscrollcommand=textScrollbar.set),row=0,column=0,sticky="WENS")
textScrollbar.config(command=textInput.yview)


showerLog=logging.getLogger("shower")
showerArgs={
    "zoom":100,
    "num":0
}
imgshower=None
imgshowerTk=None
def uploadImage():
    global imgshower,imgshowerTk
    img=images[showerArgs["num"]]
    x,y=img.size
    imgshower=img.resize((int(x*showerArgs["zoom"]/100),int(y*showerArgs["zoom"]/100)))
    imgshowerTk=ImageTk.PhotoImage(image=imgshower)
    showerBox.itemconfig("shower", image=imgshowerTk)
def zoomPhoto(delta):
    if not 0<showerArgs["zoom"]+delta<1000:
        return
    showerArgs["zoom"]+=delta
    showerLog.debug("Photo zoom -> %d"%showerArgs["zoom"])
    uploadImage()
def windowsMouseWheel(event):
    delta=event.delta//12
    zoomPhoto(delta)
def macMouseWheel(event):
    delta=event.delta*10
    zoomPhoto(delta)
def linuxMouseWheel(way):
    if way:
        delta=10
    else:
        delta=-10
    zoomPhoto(delta)
def movePhoto(event):
    global moveAnchor
    if moveAnchor==None:
        moveAnchor=(event.x,event.y)
        return
    
    showerBox.move("shower",event.x-moveAnchor[0],event.y-moveAnchor[1])
    showerLog.debug("Photo move (%d,%d)"%(event.x-moveAnchor[0],event.y-moveAnchor[1]))
    moveAnchor=(event.x,event.y)
    if 0>showerBox.coords("shower")[0]:
        showerBox.move("shower",0-showerBox.coords("shower")[0],0)
    if 400<showerBox.coords("shower")[0]:
        showerBox.move("shower",400-showerBox.coords("shower")[0],0)
    if 0>showerBox.coords("shower")[1]:
        showerBox.move("shower",0,0-showerBox.coords("shower")[1])
    if 600<showerBox.coords("shower")[1]:
        showerBox.move("shower",0,600-showerBox.coords("shower")[1])
def resetPhoto():
    x, y = showerBox.coords('shower')
    showerBox.move('shower',200-x,300-y)
    showerArgs["zoom"]=int(min(40000/images[0].size[0],60000/images[0].size[1]))
    showerLog.debug("resetPhoto zoom->%d"%showerArgs["zoom"])
    showerArgs["num"]=0
    pageupButton.config(state="disabled")
    if len(images)>1:
        pagedownButton.config(state="normal")
    else:
        pagedownButton.config(state="disabled")
    uploadImage()
creatLog=logging.getLogger("creat")
def createPhoto():
    global images
    if bgArgs["bgType"].get():
        try:
            background=Image.open(bgArgs["bgFile"].get())
        except:
            messagebox.showerror("错误","无法打开选择的背景图片")
            creatLog.warning("无法打开选择的背景图片")
            createButton.config(state="normal")
            return
    else:
        background=Image.new("RGB",(bgArgs["bgSize"][0].get(),bgArgs["bgSize"][1].get()),color=bgArgs["bgColor"].get())
    try:
        choseFont=ImageFont.truetype(fonts[fontArgs["fontFamily"].get()],size=fontArgs["fontSize"].get())
    except:
        messagebox.showerror("错误","字体加载异常")
        creatLog.warning("字体加载异常")
        createButton.config(state="normal")
        return
    template = Template(
        background=background,
        font=choseFont,
        font_size_sigma=fontArgs["fontSizeSigma"].get(),  # 字体大小随机扰动
        line_spacing=fontArgs["lineSpacing"].get(),
        line_spacing_sigma=fontArgs["lineSpacingSigma"].get(),
        fill=ImageColor.getcolor(fontArgs["color"].get(), "RGB"),  # 字体“颜色”
        word_spacing=fontArgs["wordSpacing"].get(),  # 行间距随机扰动
        word_spacing_sigma=fontArgs["wordSpacingSigma"].get(),  # 字间距随机扰动
        end_chars=fontArgs["endChars"].get(),  # 防止特定字符因排版算法的自动换行而出现在行首
        perturb_x_sigma=fontArgs["perturbXSigma"].get(),  # 笔画横向偏移随机扰动
        perturb_y_sigma=fontArgs["perturbYSigma"].get(),  # 笔画纵向偏移随机扰动
        perturb_theta_sigma=fontArgs["perturbThetaSigma"].get(),  # 笔画旋转偏移随机扰动
        left_margin=fontArgs["leftMargin"].get(),
        top_margin=fontArgs["topMargin"].get(),
        right_margin=fontArgs["rightMargin"].get(),
        bottom_margin=fontArgs["bottomMargin"].get(),
    )
    images=list(handwrite(textInput.get(0.0,tkinter.END),template))
    resetPhoto()
    creatLog.warning(f"生成了{len(images)}张图片")
    createButton.config(state="normal")
def createPhotoT():
    createButton.config(state="disabled")
    creatLog.info("开始生成")
    threading.Thread(target=createPhoto,daemon=False).start()

moveAnchor=None

def mouseDown(event):
    global moveAnchor
    moveAnchor=(event.x,event.y)
    showerBox.config(cursor="fleur")
def mouseUp(event):
    global moveAnchor
    moveAnchor=None
    showerBox.config(cursor="arrow")
def showImage(image):
    filename=tempfiles+f"/{float(time())}.png"
    image.save(filename)
    print(filename)
    webbrowserOpen(filename)
def mouseDouble(event):
    showImage(images[showerArgs["num"]])
def pageDown():
    if showerArgs["num"]==len(images)-1:
        pagedownButton.config(state="disabled")
        return
    showerArgs["num"]+=1
    if showerArgs["num"]==len(images)-1:
        pagedownButton.config(state="disabled")
    pageupButton.config(state="normal")
    uploadImage()

def saveImage(num=showerArgs["num"],path=None):
    loger=logging.getLogger(f"saveImages {num}")
    if not path:
        loger.debug("询问保存文件名")
        path=filedialog.asksaveasfilename(title="请选择保存位置",defaultextension=".png",filetypes=[("图片",[".png",".jpg",".bmp",".gif",".wedp",".tiff",".ico",".pcd",".tga"]),("任意文件","*.*")])
        if not path:
            return
    loger.debug(f"保存到 {path}")
    images[num].save(path)
    loger.debug("保存完成")
def saveAllImages():
    loger=logging.getLogger("saveAllImages")
    loger.info("开始保存")
    path=filedialog.askdirectory(title="请选择保存位置")
    if not path:
        loger.info("取消保存")
        return
    t=int(time())
    loger.debug(f"保存到 {path}")
    for i in range(len(images)):
        loger.debug(f"保存第{i}张")
        saveImage(i,os.path.join(path,f"{t}-{i}.png"))
    loger.debug(f"保存完成")
def pageUp():
    if showerArgs["num"]==0:
        pageupButton.config(state="disabled")
        return
    showerArgs["num"]-=1
    if showerArgs["num"]==0:
        pageupButton.config(state="disabled")
    pagedownButton.config(state="normal")
    uploadImage()

imgshowerTk=ImageTk.PhotoImage(image=images[0])
showerBox=tkinter.Canvas(mainScreen,width=400,height=600)
showerBox.create_image(200,300,image=imgshowerTk,tag="shower")
showerBox.grid(row=0,column=1,rowspan=2,padx=2,pady=2)
if "windows" in sys_platform:
    showerBox.bind("<MouseWheel>",windowsMouseWheel)
elif "macos" in sys_platform:
    showerBox.bind("<MouseWheel>",macMouseWheel)
else:
    showerBox.bind("<Button-4>",lambda event:linuxMouseWheel(True))
    showerBox.bind("<Button-5>",lambda event:linuxMouseWheel(False))
showerBox.bind("<B1-Motion>",movePhoto)
showerBox.bind("<Button-1>",mouseDown)
showerBox.bind("<ButtonRelease-1>",mouseUp)
showerBox.bind("<Double-Button-1>",mouseDouble)

ButtonBox=easyGrid(tkinter.Frame(mainScreen),row=1,column=0,sticky="N")
createButton=easyGrid(ttk.Button(ButtonBox,text="\n生成\n",width=40,command=createPhotoT),row=0,column=0,columnspan=2,sticky="WEN",padx=2,pady=2)
easyGrid(ttk.Button(ButtonBox,text="保存",command=saveImage),row=1,column=0,sticky="WE",padx=2,pady=2)
easyGrid(ttk.Button(ButtonBox,text="全部保存",command=saveAllImages),row=1,column=1,sticky="WE",padx=2,pady=2)
pageupButton=easyGrid(ttk.Button(ButtonBox,text="上一张",state="disabled",command=pageUp),row=2,column=0,sticky="WE",padx=2,pady=2)
pagedownButton=easyGrid(ttk.Button(ButtonBox,text="下一张",state="disabled",command=pageDown),row=2,column=1,sticky="WE",padx=2,pady=2)

def dfsSave(now):
    if type(now) in [FloatVar,tkinter.IntVar,tkinter.StringVar]:
        return now.get()
    elif type(now) == dict:
        new={}
        for key in now:
            new[key]=dfsSave(now[key])
        return new
    elif type(now) == list:
        new=[]
        for i in now:
            new.append(dfsSave(i))
        return new
    else:
        return now
def dfsImport(now,new):
    errlist={}
    if type(now) ==dict:
        if type(new)!=dict:
            return ("typeErr",f"{now.__class__.__name__} != {new.__class__.__name__}")
        for i in now:
            if i not in new:
                errlist[i]=(("nonexistence",i))
                continue
            retsult=dfsImport(now[i],new[i])
            if retsult:
                errlist[i]=retsult
    elif type(now) == list:
        if type(new)!=list:
            return ("typeErr",f"{now.__class__.__name__} != {new.__class__.__name__}")
        for i in range(len(now)):
            if len(new)<=i:
                errlist[i]=(("nonexistence",i))
                continue
            retsult=dfsImport(now[i],new[i])
            if retsult:
                errlist[i]=retsult
    elif type(new) in [FloatVar,tkinter.IntVar,tkinter.StringVar]: 
        try:
            new.set(now)
        except:
            errlist="typeErr","set Fail"
    else:
        errlist="typeErr","unknown"
    return errlist

def importConfig():
    importConfigLog=logging.getLogger("importConfigLog")
    importConfigLog.debug("询问导入文件")
    retsult=filedialog.askopenfilename(title="请选择文件",filetypes=[("JSON文件","*.json"),("yaml文件","*.yml"),("任意文件","*.*")])
    if not retsult:
        importConfigLog.debug("用户取消")
    importConfigLog.debug(f"用户选择 {retsult}")
    try:
        with open(retsult,"r",encoding="utf-8") as f:
            configs=f.read()
    except:
        importConfigLog.warning("无法打开文件")
        messagebox.showerror("错误","无法打开文件")
        return
    importWays={"yaml":lambda configs:yaml.load(configs,Loader=yaml.FullLoader),"json":json.loads}
    importType=""
    for i in importWays:
        try:
            config=importWays[i](configs)
            if type(config)==dict:
                importType=i
                break
        except:
            continue
    if not importType:
        importConfigLog.warning("格式不正确")
        messagebox.showerror("错误","该文件不是支持的文件类型")
        return
    try:
        errs=dfsImport(config,{"bgArgs":bgArgs,"fontArgs":fontArgs})
    except:
        importConfigLog.warning("导入时异常")
        messagebox.showerror("错误","导入配置时出现异常")
        return
    if errs:
        importConfigLog.warning(json.dumps(errs,indent=4,separators=(",",":"),ensure_ascii=False))
        messagebox.showwarning("警告","部分参数导入失败,参见日志")
        return
    importConfigLog.info("导入成功")
    messagebox.showinfo("导出成功",f"配置{retsult}导入成功")
    

def deriveConfig():
    deriveConfigLog=logging.getLogger("deriveConfigLog")
    configs=dfsSave({"bgArgs":bgArgs,"fontArgs":fontArgs})
    deriveConfigLog.debug("数据检索完成，等待用户选择")
    retsult=filedialog.asksaveasfilename(title="请选择保存文件",filetypes=[("JSON文件","*.json"),("yaml文件","*.yml"),("任意文件","*.*")],defaultextension=".json",initialfile="配置文件%s.json"%(strftime("%Y-%m-%d-%H-%M-%S",localtime(time()))))
    deriveConfigLog.debug(f"用户选择 {retsult}")
    if not retsult:
        deriveConfigLog.info("取消导出")
        return
    if retsult.lower()[-4:]==".yml":
        encodeType="yaml"
        configs=yaml.dump(configs,allow_unicode=True)
    else:
        encodeType="json"
        configs=json.dumps(configs,indent=4,separators=(",",":"),ensure_ascii=False)
    
    deriveConfigLog.debug("序列化完成")
    try:
        with open(retsult,"w",encoding="utf-8") as f:
            f.write(configs)
    except:
        deriveConfigLog.warning("无法打开文件")
        messagebox.showerror("错误","无法打开文件")
        return
    deriveConfigLog.info(f"配置已用{encodeType}格式导出至 {retsult}")
    messagebox.showinfo("导出成功",f"当前配置已用{encodeType}格式导出至 {retsult}")

def aboutShower():
    auboutScreen=tkinter.Tk()
    auboutScreen.iconbitmap(resource_path(os.path.join("logo.ico")))
    auboutScreen.title("关于")

    messageBox=tkinter.Frame(auboutScreen)
    messageBox.grid(row=0,column=0)

    createrTitle=tkinter.Label(messageBox,text="作者:")
    createrTitle.grid(row=0,column=0,sticky="W")
    creater=tkinter.Entry(messageBox)
    creater.insert(0,"宽宽")
    creater.config(state="readonly")
    creater.grid(row=0,column=1,sticky="W")

    createrQQTitle=tkinter.Label(messageBox,text="作者QQ:")
    createrQQTitle.grid(row=1,column=0,sticky="W")
    createrQQ=tkinter.Entry(messageBox)
    createrQQ.insert(0,"2163826131")
    createrQQ.config(state="readonly")
    createrQQ.grid(row=1,column=1,sticky="W")
    
    createrUrlTitle=tkinter.Label(messageBox,text="作者主页:")
    createrUrlTitle.grid(row=2,column=0,sticky="W")
    createrUrl=tkinter.Entry(messageBox,fg="blue",cursor="hand2")
    createrUrl.insert(0,"宽宽2007的小天地")
    def startURL(event):
        webbrowserOpen("https://kuankuan2007.gitee.io")
    createrUrl.bind("<Button-1>", startURL)
    createrUrl.config(state="readonly")
    createrUrl.grid(row=2,column=1,sticky="W")

    createrGiteeTitle=tkinter.Label(messageBox,text="作者Gitee:")
    createrGiteeTitle.grid(row=3,column=0,sticky="W")
    createrGitee=tkinter.Entry(messageBox,fg="blue",cursor="hand2")
    createrGitee.insert(0,"宽宽2007")
    def startGitee(event):
        webbrowserOpen("https://gitee.com/kuankuan2007")
    createrGitee.bind("<Button-1>", startGitee)
    createrGitee.config(state="readonly")
    createrGitee.grid(row=3,column=1,sticky="W")

    createrGithbTitle=tkinter.Label(messageBox,text="作者Github:")
    createrGithbTitle.grid(row=4,column=0,sticky="W")
    createrGithb=tkinter.Entry(messageBox,fg="blue",cursor="hand2")
    createrGithb.insert(0,"KUANKUAN2007")
    def startGitee(event):
        webbrowserOpen("https://github.com/kuankuan2007")
    createrGithb.bind("<Button-1>", startGitee)
    createrGithb.config(state="readonly")
    createrGithb.grid(row=4,column=1,sticky="W")

    createrWeiXinPayTitle=tkinter.Label(messageBox,text="赞助作者")
    createrWeiXinPayTitle.grid(row=5,column=0,sticky="W")
    createrWeiXinPay=tkinter.Entry(messageBox,fg="blue",cursor="hand2")
    createrWeiXinPay.insert(0,"微信支付")
    def startWeiXinPayTitle(event):
        webbrowserOpen("https://kuankuan2007.gitee.io/WeiXinPay.png")
    createrWeiXinPay.bind("<Button-1>", startWeiXinPayTitle)
    createrWeiXinPay.config(state="readonly")
    createrWeiXinPay.grid(row=5,column=1,sticky="W")

    versionTitle=tkinter.Label(messageBox,text="版本")
    versionTitle.grid(row=6,column=0,sticky="W")
    version=tkinter.Entry(messageBox)
    version.insert(0,"v0.0.2")
    version.config(state="readonly")
    version.grid(row=6,column=1,sticky="W")

    releaseAtTitle=tkinter.Label(messageBox,text="发布日期")
    releaseAtTitle.grid(row=7,column=0,sticky="W")
    releaseAt=tkinter.Entry(messageBox)
    releaseAt.insert(0,"2023-3-19")
    releaseAt.config(state="readonly")
    releaseAt.grid(row=7,column=1,sticky="W")

    auboutScreen.mainloop()

mainManu=tkinter.Menu(mainScreen,tearoff=0)
mainScreen.config(menu=mainManu)

configurationManu=tkinter.Menu(mainManu,tearoff=0)
aboutManu=tkinter.Menu(mainManu,tearoff=0)

configurationManu.add_command(label="导入配置",command=importConfig)
configurationManu.add_command(label="导出配置",command=deriveConfig)

aboutManu.add_command(label="帮助",command=lambda:webbrowserOpen("https://kuankuan2007.gitee.io/docs/handwritten-text-generator/"))
aboutManu.add_command(label="开源",command=lambda:webbrowserOpen("https://gitee.com/kuankuan2007/handwritten-text-generator"))
aboutManu.add_command(label="关于",command=threading.Thread(target=aboutShower,daemon=True).start)

mainManu.add_cascade(label='配置',menu=configurationManu)
mainManu.add_cascade(label='软件',menu=aboutManu)

launcherLog.info("启动主循环")

mainScreen.mainloop()