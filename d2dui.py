#!/usr/bin/env python
# encoding: utf-8
import desire2download
import os

username = None
password = None
ignore_re = None
loginapp = None

try:
    import Tkinter, tkMessageBox
except ImportError:
    print """Could not load Tk, please install the correct package for 
             your operating system. You can reference
             http://tkinter.unpythonic.net/wiki/How_to_install_Tkinter
             if you do not know how to do this"""

def login(event=None):
    global username, password
    
    username = loginapp.username.get()
    password = loginapp.password.get()
    remember = loginapp.remember_me.get()
    
    if remember:
        # Write to save file
        try:
            f = open('.d2dlogin', 'w')
            f.write(str(username)+"\n")
            f.write(password)
            f.close()
        except Exception:
            pass
    else:
        # Try to delete if already exists
        if os.path.exists('.d2dlogin'):
            try:
                os.unlink('.d2dlogin')
            except Exception:
                pass
    
    loginapp.login_failed = False
    loginapp.destroy()
    loginapp.quit()

class d2dLogin(Tkinter.Frame):
    login_failed = True
    manual_quit = False
    
    def __init__(self, master=None):
        Tkinter.Frame.__init__(self, master)
        self.master.title("Desire2Download")
        self.master.resizable(0,0)
        self.grid()
        self.createWidgets()
    
    def createWidgets(self):
        self.usrlbl = Tkinter.Label(self, text='Username')
        self.usrlbl.grid(column=0, row=0, padx=5)
        self.pwdlbl = Tkinter.Label(self, text='Password')
        self.pwdlbl.grid(column=0, row=1, padx=5)
        
        self.username = Tkinter.StringVar()
        self.usrbox = Tkinter.Entry(self, textvariable=self.username)
        self.usrbox.grid(column=1, row=0, pady=2, padx=5, columnspan=2)
        self.password = Tkinter.StringVar()
        self.pwdbox = Tkinter.Entry(self, show='*', textvariable=self.password)
        self.pwdbox.grid(column=1, row=1, pady=2, padx=5, columnspan=2)
        
        self.usrbox.bind('<Return>', login)
        self.pwdbox.bind('<Return>', login)
        
        self.remember_me = Tkinter.BooleanVar()
        self.remember_me.set(True)
        self.remchk = Tkinter.Checkbutton(self, text='Remember me?', variable=self.remember_me)
        self.remchk.grid(column=1, row=2, sticky=Tkinter.NW, columnspan=2)
        
        self.loginbtn = Tkinter.Button(self, text='Login', command=login)
        self.loginbtn.grid(column=1, row=3, pady=2, sticky=Tkinter.NW)
        self.quitbtn = Tkinter.Button(self, text='Cancel', command=self.quit)
        self.quitbtn.grid(column=2, row=3, pady=2, sticky=Tkinter.NW)
        
    def quit(self):
        self.manual_quit = True
        Tkinter.Frame.quit(self)
    
class d2dApp(Tkinter.Frame):
    def __init__(self, master=None):
        Tkinter.Frame.__init__(self, master)
        self.master.resizable(1,1)
        self.master.title("Desire2Download")
        self.grid()
        self.createWidgets()
    
    def createWidgets(self):
        self.quitButton = Tkinter.Button(self, text='Quit', command=self.quit)
        self.quitButton.grid()

def loadGUI(u, p, r):
    global username, password, ignore_re, loginapp
    
    username = u
    password = p
    ignore_re = r
    
    loginapp = d2dLogin()
    
    if os.path.exists('.d2dlogin'):
        try:
            f = open('.d2dlogin', 'r')
            fc = f.read()
            f.close()
            fc = fc.split('\n')
            username = fc[0]
            password = fc[1]
            loginapp.username.set(username)
            loginapp.password.set(password)
        except Exception:
            pass
    
    #get login
    if u is None and p is None:
        loginapp.mainloop()
    
    d2d = desire2download.Desire2Download(username, password, ignore_re)
    loginapp.manual_quit = False
    
    try:
        d2d.login()
        loginapp.login_failed = False
    except desire2download.AuthError as e:
        loginapp.login_failed = True
    
    if not loginapp.login_failed:
        app = d2dApp()
        app.mainloop()
    else:
        if not loginapp.manual_quit:
            rootwnd = Tkinter.Tk() #creating a fake root window is required
            rootwnd.withdraw()     #to prevent an empty window from appearing
            tkMessageBox.showerror("Desire2Download", "Login failed!", parent=rootwnd)
            rootwnd.quit()
        return 2
    
    return 1
