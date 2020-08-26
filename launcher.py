import tkinter as tk
from tkinter import ttk
from tkinter import font
import random
import os
from multiprocessing import freeze_support
import shutil
import traceback

def showmain():
    save_text.place(x=0,y=0)
    save_box.place(x=2,y=20)
    resolution_text.place(x=0,y=50)
    resolution_box.place(x=2,y=70)
    display_text.place(x=0,y=100)
    display_box.place(x=2,y=120)
    texture_text.place(x=0,y=150)
    texture_box.place(x=2,y=170)
    settings_text.place(x=0,y=220)
    type_text.place(x=0,y=250)
    type_box.place(x=2,y=270)
    seed_text.place(x=0,y=300)
    seed_box.place(x=2,y=320)
    enter.place(x=2,y=410)
    controls.place(x=102,y=410)
    delete.place(x=202,y=410)

def hidemain():
    save_text.place_forget()
    save_box.place_forget()
    resolution_text.place_forget()
    resolution_box.place_forget()
    display_text.place_forget()
    display_box.place_forget()
    texture_text.place_forget()
    texture_box.place_forget()
    settings_text.place_forget()
    type_text.place_forget()
    type_box.place_forget()
    seed_text.place_forget()
    seed_box.place_forget()
    enter.place_forget()
    controls.place_forget()
    delete.place_forget()

def goback():
    global controls_visible,ps_text
    control_text.place_forget()
    back.place_forget()
    ps_text.place_forget()
    controls_visible = False
    showmain()

def showcontrols():
    global control_text,ps_text,back,controls_visible
    controls_visible = True
    hidemain()
    #control_text = tk.Label(root, text="Controls:\n\nW - Move Forward\nA - Move Left\nS - Move Backwards\nD - Move Right")
    control_text = ttk.Label(root, text="Controls:\n\nW - Move Forward\n\nA - Move Left\n\nS - Move Backwards\n\nD - Move Right\n\nLeft Click - Break Block\n\nRight Click - Place Block\n\nSpace - Jump/Fly\n\nTab - Toggle Flying\n\nShift - Descend (Flying Mode Only)\n\nNumber Keys (1-9) - Switch Blocks\n\nLeft Control - Zoom\n\nEscape - Open Game Menu\n\nF1 - Toggle Texture Quality (Enhanced Texture Mode Only)")
    
    control_text.configure(anchor="e")
    control_text.place(x=0,y=0)

    back = tk.Button(text='Back',command=goback)
    back.place(x=2,y=410)

    ps_text = ttk.Label(root, text="ps. press f2 if you dare")
    
    small = font.Font(ps_text, ps_text.cget("font"))
    small.configure(size=7)
    ps_text.configure(font=small)
    ps_text.place(x=2,y=440)

def checkseed():
    ans = seed_box.get()
    try:
        int(ans)
        if (len(str(ans)) > 9):
            raise Exception("Seed too big")
        return True
    except:
        seed_box.delete(0, 'end')
        return False

def getans():
    global Launching

    proceed = True
    slot = save_menu.get()

    if slot[len(slot)-1] == ')':
        if checkseed():
            slot = slot.split('(')
            slot = slot[0]#[:len(slot)-1]
            slot = slot[0:len(slot)-1]
            worldtype = type_menu.get()
            if worldtype == "Normal":worldtype = str(1)
            if worldtype == "Superflat":worldtype = str(2)
            if worldtype == "Normal + Caves (Beta)":worldtype = str(3)
            seed = seed_box.get()
            os.mkdir('world_saves\\'+slot)
            saveattr = open('world_saves\\'+slot+'\\world_attributes.txt',"w")
            saveattr.write(worldtype+'\n'+seed)
            saveattr.close()
        else:
            proceed = False
    
    if proceed:
        resolution =resolution_menu.get().split('x')
        displaymode = display_menu.get()
        if displaymode == "Windowed":displaymode = str(0)
        elif displaymode == "Fullscreen":displaymode = str(1)
        texquality = texture_menu.get()
        if texquality == "Normal":texquality = str(0)
        elif texquality == "Enhanced":texquality = str(1)
            
        stringtowrite = 'previous_save:\n'+slot+'\nscreen_width:\n'+str(int(resolution[0]))+'\nscreen_height:\n'+str(int(resolution[1]))+'\nfullscreen:\n'+displaymode+'\ntexture_quality:\n'+texquality
        try:os.remove('world_saves\\properties.txt')
        except:pass
        file1 = open("world_saves\\properties.txt","w")
        file1.write(stringtowrite)
        file1.close() 
        Launching = False
        root.destroy()

def delete():
    global save_menu,save_box,saveslots
    delfile = save_menu.get()
    shutil.rmtree('world_saves\\'+delfile)

    saveslots = ['Slot 1','Slot 2','Slot 3','Slot 4']
    for n in range(len(saveslots)):
        if not os.path.exists('world_saves\\'+saveslots[n]):
            saveslots[n] += ' (New)'

    save_menu = tk.StringVar()
    save_menu.set(delfile+' (New)')

    save_box = ttk.Combobox(root, textvariable=save_menu, state='readonly')

    save_box['values'] = saveslots



if __name__ == "__main__":
    freeze_support()
    Launching = True

    root = tk.Tk()
    root.title("Blocks Launcher")
    root.resizable(width=False, height=False)
    root.geometry("%dx%d+%d+%d" % (720, 480, 0, 0))

    
    saveslots = ['Slot 1','Slot 2','Slot 3','Slot 4']
    if not os.path.exists('world_saves'):
        os.mkdir('world_saves')
        try:os.remove('world_saves\\properties.txt')
        except:pass
    for n in range(len(saveslots)):
        if not os.path.exists('world_saves\\'+saveslots[n]):
            saveslots[n] += ' (New)'

    if os.path.exists("world_saves\\properties.txt"):
        properties = open("world_saves\\properties.txt","r")
        properties = properties.readlines()

        savevar = properties[1].split('\n')[0]
        if not os.path.exists('world_saves\\'+savevar):
            savevar = 'Slot 1 (New)'
        resolutionvar = properties[3]+'x'+properties[5].split('\n')[0]
        displayvar = properties[7].split('\n')[0]
        if displayvar == str(0): displayvar = 'Windowed'
        elif displayvar == str(1): displayvar = 'Fullscreen'
        texturevar = properties[9].split('\n')[0]
        if texturevar == str(0): texturevar = 'Normal'
        elif texturevar == str(1): texturevar = 'Enhanced'
    else:
        savevar = 'Slot 1 (New)'
        resolutionvar = '720x480'
        displayvar = 'Windowed'
        texturevar = 'Normal'
    
    """Saves"""
    if True:
        save_text = tk.Label(root, text="World Saves")


        save_menu = tk.StringVar()
        save_menu.set(savevar)

        save_box = ttk.Combobox(root, textvariable=save_menu, state='readonly')

        save_box['values'] = saveslots

    """Resolution"""
    if True:
        resolution_text = tk.Label(root, text="Display Resolution")


        resolution_menu = tk.StringVar()
        resolution_menu.set(resolutionvar)

        resolution_box = ttk.Combobox(root, textvariable=resolution_menu, state='readonly')

        resolution_box['values'] = ("1920x1080",
                        "1280x720",
                        "720x480")

    """Display Mode"""
    if True:
        display_text = tk.Label(root, text="Display Mode")


        display_menu = tk.StringVar()
        display_menu.set(displayvar)


        display_box = ttk.Combobox(root, textvariable=display_menu, state='readonly')

        display_box['values'] = ("Windowed",
                        "Fullscreen",)

    """Texture Quality"""
    if True:
        texture_text = tk.Label(root, text="Texture Quality")


        texture_menu = tk.StringVar()
        texture_menu.set(texturevar)

        texture_box = ttk.Combobox(root, textvariable=texture_menu, state='readonly')

        texture_box['values'] = ("Normal",
                        "Enhanced",)

    """World Settings"""
    if True:
        settings_text = tk.Label(root, text="World Generation Settings")
        underlined = font.Font(settings_text, settings_text.cget("font"))
        underlined.configure(underline=True)
        settings_text.configure(font=underlined)

    """World Type"""
    if True:
        type_text = tk.Label(root, text="World Type")
        type_menu = tk.StringVar()
        type_menu.set("Normal")
        type_box = ttk.Combobox(root, textvariable=type_menu, state='readonly')
        type_box['values'] = ("Normal",
                        "Superflat",
                        "Normal + Caves (Beta)")

    """World Seed"""
    if True:
        seed_text = tk.Label(root, text="World Seed")
        seed_box = tk.Entry(root)
        seed_box.insert(0, str(random.randint(1,9999999)))


    enter = tk.Button(text='Launch Game',command=getans)
    controls = tk.Button(text='Controls',command=showcontrols)
    delete = tk.Button(text='Delete World',command=delete)

    controls_visible = False
    showmain()


    try:
        while Launching:
            if not controls_visible:
                root.bind('<<ComboboxSelected>>')
                if os.path.exists('world_saves\\'+save_menu.get()):
                    settings_text.place_forget()
                    type_text.place_forget()
                    type_box.place_forget()
                    seed_text.place_forget()
                    seed_box.place_forget()
                    delete.place(x=202,y=410)
                else:
                    showmain()
                    delete.place_forget()
            root.update_idletasks()
            root.update()

                #os.mkdir('world_saves\\'+save_menu.get())

    except:
        pass
    if not Launching:
        import test
        test.run()
        """
        try:
            import test
            test.run()
        except Exception:traceback.print_exc()
        """