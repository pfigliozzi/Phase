"""
Copyright 2015 Pat Figliozzi

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import Tkinter as tk
import ttk
import tkFileDialog
import string as string
import numpy as np
import os
from decimal import *
from PIL import Image, ImageTk
import collections
import ctypes
import ConfigParser
from numba import autojit




class main_window:
    def __init__(self, master):
        self.master = master
        self.master.title('Phase')

        # Build the Menu Bar
        self.menu_bar = tk.Menu(self.master)
        self.file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.file_menu.add_command(label="Open Image List...", command=self.open_mask_list)
        self.file_menu.add_command(label="Open Correction Parameters...")
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Save mask Bitmap...", command=self.save_as_bitmap)
        self.file_menu.add_command(label="Save Zernike Parameters...", command=self.save_zernike_parameters)
        self.file_menu.add_command(label="Load Zernike Parameters...", command=self.load_zernike_parameters)
        self.menu_bar.add_cascade(label="File", menu=self.file_menu)
        self.options_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.options_menu.add_command(label="Zernike Modes...")
        self.options_menu.add_command(label="Display on second monitor...", command=self.second_monitor_dialog)
        self.menu_bar.add_cascade(label="Options", menu=self.options_menu)
        self.master.config(menu=self.menu_bar)

        # Build the 3 Paned Window for the base masks, zernike boxes, and the mask previews
        self.paned_window = tk.PanedWindow(master=self.master, orient='horizontal', sashwidth=10)
        self.paned_window.pack(fill='both', expand=1)
        self.mask_list = tk.Listbox(self.paned_window, selectmode='SINGLE')
        self.zernike_coefficients = tk.LabelFrame(self.paned_window, text='Zernike Coefficients')
        self.mask_preview = tk.LabelFrame(self.paned_window, text='Mask Previews')
        self.paned_window.add(self.mask_list)
        self.paned_window.add(self.zernike_coefficients)
        self.paned_window.add(self.mask_preview)
        self.paned_window.config(sashwidth=10)
        self.paned_window.paneconfigure(self.mask_list, minsize=20, height=800)
        self.paned_window.paneconfigure(self.zernike_coefficients, minsize=120, height=800)
        self.paned_window.paneconfigure(self.mask_preview, minsize=20, height=800)

        # Build the widgets that display the base phase mask and the modified phase mask
        self.base_mask_image = ImageTk.PhotoImage(image=Image.new('L', (800, 600), color=0), size=(800, 600))
        self.base_mask_image_label = tk.Label(master=self.mask_preview, image=self.base_mask_image, anchor='nw')
        self.base_mask_text_label = tk.Label(master=self.mask_preview, text='Base Mask', justify='left')
        self.base_mask_image_label.image = self.base_mask_image
        self.base_mask_image_label.pil_image = Image.new('L', (800, 600), color=0)
        self.base_mask_text_label.pack(anchor='nw')
        self.base_mask_image_label.pack(fill='x', expand='YES', anchor='nw')
        self.base_mask_image_label.bind("<Configure>",
                                        self.resize_image)

        self.modified_mask_image = ImageTk.PhotoImage(image=Image.new('L', (800, 600), color=0), size=(800, 600))
        self.modified_mask_image_label = tk.Label(master=self.mask_preview, image=self.modified_mask_image, anchor='nw')
        self.modified_mask_text_label = tk.Label(master=self.mask_preview, text='Modified Mask', justify='left')
        self.modified_mask_image_label.image = self.modified_mask_image
        self.modified_mask_image_label.pil_image = Image.new('L', (800, 600), color=0)
        self.modified_mask_text_label.pack(anchor='nw')
        self.modified_mask_image_label.pack(fill='x', expand='YES', anchor='nw')

        self.modified_mask_image_label.bind("<Configure>",
                                            self.resize_image)
        self.phase_array = phase_array((800, 600))

        # Create the Listbox that contains the beginning phase masks
        # self.mask_list = tk.Listbox(self.master, selectmode='SINGLE')
        self.mask_list.bind("<<ListboxSelect>>",
                            self.setImage)

        self.stringvar1 = tk.StringVar(master=self.zernike_coefficients)
        self.stringvar1.trace("w", self.update_modified_mask_preview)

        self.zernike_entry_list = [('Z1', 'Z1 (0,0)\nPiston'),
                                   ('Z2', 'Z2 (-1,1)\nTilt x'),
                                   ('Z3', 'Z3 (1,1)\nTip Y'),
                                   ('Z4', 'Z4 (0,2)\nFocus'),
                                   ('Z5', 'Z5 (-2,2)\nOblique Astigmatism'),
                                   ('Z6', 'Z6 (2,2)\nVertical Astigmatism'),
                                   ('Z7', 'Z7 (3,-1)\nVertical Coma'),
                                   ('Z8', 'Z8 (3,1)\nHorizontal Coma'),
                                   ('Z11', 'Z11 (4,0)\nPrimary Spherical')]

        self.zernike_entry_widgets = self.make_zernike_entry_widgets(self.zernike_entry_list)

        self.mask_image_list = []
        self.selected_dir = None
        self.app_directory = os.getcwd()
        self.display_on_second_monitor = 0

        self.bounding_box_label_frame = tk.LabelFrame(self.zernike_coefficients, text='Bounding Box')
        self.modify_full_image = tk.IntVar()
        self.full_image_checkbox = tk.Checkbutton(master=self.bounding_box_label_frame, text='Full Image',
                                                  variable=self.modify_full_image)
        self.full_image_checkbox.select()
        self.modify_full_image.trace('w', self.disable_bounding_box_widgets)
        self.coordinates_label = tk.Label(master=self.bounding_box_label_frame, text='Starting Coordinates (x, y)')
        self.coordinates_bounding_box_start = tk.Entry(master=self.bounding_box_label_frame, justify='right', width=10)
        self.coordinates_bounding_box_start.bind('<Return>', self.update_modified_mask_preview)
        self.coordinates_bounding_box_start.bind('<FocusOut>', self.update_modified_mask_preview)
        self.box_size_label = tk.Label(master=self.bounding_box_label_frame, text='Size (width, height)')
        self.coordinates_bounding_box_size = tk.Entry(master=self.bounding_box_label_frame, justify='right', width=10)
        self.coordinates_bounding_box_size.bind('<Return>', self.update_modified_mask_preview)
        self.coordinates_bounding_box_size.bind('<FocusOut>', self.update_modified_mask_preview)
        self.coordinates_bounding_box_start.insert(0, '0, 0')
        self.coordinates_bounding_box_size.insert(0, '10, 10')
        self.disable_bounding_box_widgets()

        self.bounding_box_label_frame.pack()
        self.full_image_checkbox.pack()
        self.coordinates_label.pack()
        self.coordinates_bounding_box_start.pack()
        self.box_size_label.pack()
        self.coordinates_bounding_box_size.pack()


    def disable_bounding_box_widgets(self, *args):
        if self.modify_full_image.get() == 1:
            self.coordinates_bounding_box_start.config(state='disabled')
            self.coordinates_bounding_box_size.config(state='disabled')
        elif self.modify_full_image.get() == 0:
            self.coordinates_bounding_box_start.config(state='normal')
            self.coordinates_bounding_box_size.config(state='normal')
        self.update_modified_mask_preview()

    def second_monitor_dialog(self):
        self.dialog = HamamatsuDialogBox(self.master, self.app_directory)
        self.master.wait_window(self.dialog.main)
        self.display_on_second_monitor = self.dialog.display_on_second_monitor
        if self.dialog.okay_press == True:
            if self.dialog.display_on_second_monitor == 1:
                self.phase_display = FullScreenDisplay(self.app_directory,
                                                       self.modified_mask_image_label.pil_image,
                                                       self.dialog.monitor_to_display_on,
                                                       self.dialog.LUT_to_use,
                                                       self.dialog.wavefront_correction_to_use)
            if self.dialog.display_on_second_monitor == 0:
                try:
                    self.phase_display.destroy()
                except:
                    pass
            self.display_on_second_monitor = self.dialog.display_on_second_monitor
        return


    def make_zernike_entry_widgets(self, zernike_entry_list):
        """
        Generates the zernike entry widgets

        The function needs a list which contains [('zernike_mode_key', 'text_label'),...]. This
        function will build all the widgets so they have the correct reference and have the correct text label.

        :param zernike_entry_list: A list of tuples containing ('zernike_mode_key', 'text_label')
        """
        zernike_entry_widgets = {}
        for key, field in zernike_entry_list:
            widget = ZernikeEntryWidget(self.zernike_coefficients, field)
            zernike_entry_widgets[key] = (widget.label, widget.entry, widget.stringvar)
            widget.stringvar.trace("w", self.update_modified_mask_preview)
        return zernike_entry_widgets

    def save_zernike_parameters(self):
        save_filename = tkFileDialog.asksaveasfilename(initialdir=self.selected_dir, defaultextension='.txt',
                                                       filetypes=[('Text', '.txt')])
        f = open(save_filename, 'w')
        for key,value in self.zernike_entry_list:
            f.write(key.rjust(4)+self.zernike_entry_widgets[key][1].get().rjust(10)+'\n')
        f.close()

    def load_zernike_parameters(self):
        open_filename = tkFileDialog.askopenfilename(initialdir=self.selected_dir, defaultextension='.txt',
                                                       filetypes=[('Text', '.txt')])
        f = open(open_filename, 'r')
        for line in f.readlines():
            key, value = string.split(line)
            self.zernike_entry_widgets[key][1].delete(0,'end')
            self.zernike_entry_widgets[key][1].insert(0, value)
        f.close()

    def resize_image(self, event):
        label_size = (event.width, event.height)
        # print label_size
        # print event.widget.pil_image.size
        original_size = np.array(event.widget.pil_image.size)
        resize_ratio = min(label_size[0] / float(original_size[0]), label_size[1] / float(original_size[1]))
        resized_image = event.widget.pil_image.resize((original_size * resize_ratio).astype(int), Image.NEAREST)
        resized_photoimage = ImageTk.PhotoImage(image=resized_image)
        event.widget.configure(image=resized_photoimage)
        event.widget.image = resized_photoimage

    def open_mask_list(self):
        file_name = tkFileDialog.askopenfilename(filetypes=[('.txt Text File', '.txt'),
                                                       ('.lst Hamamatsu List', '.lst'),
                                                       ('.sif BNS Sequence File', '.sif')])
        self.mask_list.delete(0, tk.END)
        self.selected_dir = os.path.split(file_name)[0]
        os.chdir(self.selected_dir)
        picture_list = open(file_name).readlines()
        if os.path.splitext(file_name)[-1] == '.lst':
            picture_list = picture_list[2:]
        self.mask_image_list = []
        for line in picture_list:
            entry = os.path.split(string.strip(line))[-1]
            self.mask_list.insert(tk.END, entry)
            self.mask_image_list.append(entry)

    def save_as_bitmap(self):
        if self.selected_dir is None:
            self.selected_dir = os.curdir()
        save_filename = tkFileDialog.asksaveasfilename(initialdir=self.selected_dir, defaultextension='.bmp',
                                                       filetypes=[('Bitmap Image', '.bmp')])
        print save_filename
        self.modified_mask_image_label.pil_image.save(save_filename)

    def setImage(self, event):
        """
        Sets the preview base mask image upon selection of a new mask in the ListBox. Triggers when the ListBox
        value is changed
        """

        current_listbox_index = int(self.mask_list.curselection()[0])
        size = (self.base_mask_image_label.winfo_width(), self.base_mask_image_label.winfo_height())
        selected_image = Image.open(self.mask_image_list[current_listbox_index])
        original_size = np.array(selected_image.size)
        resize_ratio = min(size[0] / float(original_size[0]), size[1] / float(original_size[1]))
        resized_image = selected_image.copy()
        resized_image = resized_image.resize((original_size * resize_ratio).astype(int), Image.NEAREST)
        new_mask = ImageTk.PhotoImage(image=resized_image)
        self.base_mask_image_label.configure(image=new_mask)
        self.base_mask_image_label.image = new_mask
        self.base_mask_image_label.pil_image = selected_image

        if self.phase_array.phase.shape[0] != original_size[1] or self.phase_array.phase.shape[1] != original_size[0]:
            self.phase_array = phase_array(original_size)
        self.update_modified_mask_preview()

    def update_modified_mask_preview(self, *args):
        """
        This will update the modified mask with the zernike coefficients given in the entry boxes. This is called
        whenever a new image is selected or a change to a coefficient is made
        """

        # Import the image as an array and scale it to go between 0 and 2pi
        image_array = np.array(self.base_mask_image_label.pil_image.getdata())
        base_mask_size = self.base_mask_image_label.pil_image.size
        image_array = image_array.reshape((base_mask_size[1], base_mask_size[0])).astype('float64')
        if np.max(image_array) == np.min(image_array) == 0:
            image_array_scaled = image_array
        else:
            image_array_scaled = 2*np.pi * image_array / 255 # Hard coded to work with 8bit images only
        modified_mask = np.zeros(image_array_scaled.shape)

        # Apply the zernike coefficients to the zernike arrays and add them to the phase mask array
        for key, coefficient in self.zernike_entry_widgets.items():
            if len(coefficient[1].get()) == 0:
                return  # If the entry widget is ever blank, don't update the modified mask
            modified_mask += self.phase_array.zernike_modes.all[key] * float(coefficient[1].get())
        # If not working with the full image then modify the phase addition to only include the desired box
        if self.modify_full_image.get() == 0:
            x, y = [int(i) for i in string.split(self.coordinates_bounding_box_start.get(), ',')]
            width, height = [int(i) for i in string.split(self.coordinates_bounding_box_size.get(), ',')]
            mask = np.ones(modified_mask.shape, dtype=bool)
            mask[y:y+height,x:x+width] = False
            modified_mask[mask] = 0.0 # Set all values outside the bounding box equal to zero

        self.phase_array.phase = modified_mask + image_array_scaled

        # Need to wrap the phase around [0,2pi]
        self.phase_array.phase_normalize()

        # All this is to get the new image to fit within the label designated to previewing the mask
        phase_array_scaled = np.rint(self.phase_array.phase.copy() * (255 / (2*np.pi)))
        self.modified_mask_image_label.pil_image = Image.fromarray(phase_array_scaled.astype(np.uint8))
        if self.display_on_second_monitor == 1:
            self.phase_display.update_mask_display(self.modified_mask_image_label.pil_image)
        original_size = np.array(self.modified_mask_image_label.pil_image.size)
        label_size = (self.modified_mask_image_label.winfo_width(), self.modified_mask_image_label.winfo_height())
        resize_ratio = min(label_size[0] / float(original_size[0]), label_size[1] / float(original_size[1]))
        resized_image = self.modified_mask_image_label.pil_image.copy()
        resized_image = resized_image.resize((original_size * resize_ratio).astype(int), Image.NEAREST)
        new_modified_mask = ImageTk.PhotoImage(image=resized_image)
        self.modified_mask_image_label.configure(image=new_modified_mask)
        self.modified_mask_image_label.image = new_modified_mask


class ZernikeEntryWidget:
    def __init__(self, master, label):
        """Initialize the base widget and bindings. This includes creating the Label and Entry widgets and setting
        bindings on the Entry widget. A key is also included in order to get the entry box data out.

        :prams master: the master this widget resides in
        :prams label: the label given over the Entry widget
        """
        self.label = tk.Label(master=master, text=label, justify='left')
        self.stringvar = tk.StringVar(master=master)
        self.entry = tk.Entry(master=master, textvariable=self.stringvar, justify='right', width=10, validate='key')
        self.entry.bind()
        self.label.pack(anchor='w')
        self.entry.pack(anchor='w')
        self.entry.insert(0, '0.00')
        vcmd = (self.entry.register(self.onValidate),
                '%d', '%i', '%P', '%s', '%S', '%v', '%V', '%W')
        self.entry.configure(validatecommand=vcmd)
        self.entry.bind("<Up>", self.increment_value)
        self.entry.bind("<Down>", self.decrement_value)

    def increment_value(self, event):
        """
        Increments the value in the entry box relative to where the cursor currently is.
        """
        start_value = event.widget.get()
        str_len = len(event.widget.get())
        cursor_position = event.widget.index(tk.INSERT)
        decimal_index = start_value.find('.')
        value = Decimal(start_value)
        exponent = value.as_tuple()[2]
        if cursor_position <= decimal_index:
            temp_value = value + Decimal(10 ** (exponent + str_len - 1 - cursor_position))
        else:
            temp_value = value + Decimal(10 ** (exponent + str_len - cursor_position))
        temp_value = temp_value.quantize(Decimal(10) ** exponent)
        event.widget.delete(0, 'end')
        event.widget.insert(0, temp_value)
        event.widget.icursor(len(str(temp_value))-(str_len-cursor_position))

    def decrement_value(self, event):
        """
        Decrements the value in the entry box relative to where the cursor currently is.
        """
        start_value = event.widget.get()
        str_len = len(event.widget.get())
        cursor_position = event.widget.index(tk.INSERT)
        decimal_index = start_value.find('.')
        value = Decimal(start_value)
        exponent = value.as_tuple()[2]
        if cursor_position <= decimal_index:
            temp_value = value - Decimal(10 ** (exponent + str_len - 1 - cursor_position))
        else:
            temp_value = value - Decimal(10 ** (exponent + str_len - cursor_position))
        temp_value = temp_value.quantize(Decimal(10) ** exponent)
        event.widget.delete(0, 'end')
        event.widget.insert(0, temp_value)
        event.widget.icursor(len(str(temp_value))-(str_len-cursor_position))

    def onValidate(self, d, i, P, s, S, v, V, W):
        return True
        #     '''Validates each entry box to only contain numerical values. All the callback variables are accessible
        #        in the function but only the text being inserted is used'''
        #     valid = any(S == c for c in '0123456789.-' )
        #     print S
        #     if not valid:
        #         self.label.master.bell()
        #     try:
        #         float_test = float(S)
        #     except ValueError:
        #         self.label.master.bell()
        #         return False
        #     return valid

class FullScreenDisplay:
    """
    Displays phase mask on second monitor

    Creates the widget that displays the modified mask on the second monitor. The LUT and the wavefront correction are
    applied and need to be provided when the class is created.

    :param app_directory: The directory the app lives in (in order to properly load LUT and wavefront correction)
    :param modified_mask_image: The modified mask image that will be displayed on the the second monitor.
    :param monitor_to_display_on: The monitor that was selected to display the phase mask (from HamamatsuDialogBox). The
    number corresponds the the monitor number from the Windows API
    :param LUT_to_use: The file path of the LUT to use. The file must be txt of two columns. Column 1 is input value
    while column 2 is output value. Must have a value from 0 to 255.
    :param wavefront_correction_to_use: The file path to the wavefront correction image to use. Assumed to be grayscale
    bitmap.
    """
    def __init__(self, app_directory, modified_mask_image, monitor_to_display_on, LUT_to_use, wavefront_correction_to_use):
        self.top = tk.Toplevel(bg='black')
        self.top.overrideredirect(True)

        # Get the Monitor Information so we know how to display the image
        self.user = ctypes.windll.user32
        self.retval = []
        self.CBFUNC = ctypes.WINFUNCTYPE(ctypes.c_int, ctypes.c_ulong, ctypes.c_ulong, ctypes.POINTER(RECT), ctypes.c_double)
        self.cbfunc = self.CBFUNC(self.cb)
        self.monitor_info = self.user.EnumDisplayMonitors(0, 0, self.cbfunc, 0)

        # Select the specific monitor to use and find the Width and Height parameters
        self.second_monitor_info = self.retval[int(monitor_to_display_on)]
        self.second_monitor_parameters = [(self.retval[1][1][2]-self.retval[1][1][0], # Monitor Width
                                           self.retval[1][1][3]-self.retval[1][1][1]), # Monitor Height
                                          (self.retval[1][1][0],self.retval[1][1][1], # Starting width, height
                                           self.retval[1][1][2],self.retval[1][1][3])] # Ending width, height
        self.top.geometry("{0}x{1}+{2}+{3}".format(self.second_monitor_parameters[0][0],
                                                   self.second_monitor_parameters[0][1],
                                                   self.second_monitor_parameters[1][0],
                                                   self.second_monitor_parameters[1][1]))
        self.pil_image = modified_mask_image
        self.LUT = np.loadtxt(os.path.join(app_directory, LUT_to_use))
        self.wavefront_correction = Image.open(os.path.join(app_directory,wavefront_correction_to_use))
        self.display_image_array = np.asarray(self.pil_image.getdata())+np.asarray(self.wavefront_correction.getdata())
        self.display_image_array = wrap2value(self.display_image_array, 0, 255)
        self.display_image_array = self.display_image_array.reshape((self.pil_image.size[1], self.pil_image.size[0]))
        self.display_image = Image.fromarray(self.display_image_array.astype(np.uint8))
        self.display_image = self.display_image.point(self.LUT[:,1])


        self.photo_image = ImageTk.PhotoImage(image=self.display_image)
        self.label_widget = tk.Label(master=self.top, image=self.photo_image, bg='black')
        self.label_widget.image = self.photo_image
        self.label_widget.pack(fill='both', expand='YES')

    def update_mask_display(self, pil_image):
        """
        Updates the image on the secondary display to match the selection and modifications made in the GUI

        :param pil_image:
        :return:
        """
        self.pil_image = pil_image
        self.display_image_array = np.asarray(self.pil_image.getdata())+np.asarray(self.wavefront_correction.getdata())
        self.display_image_array = wrap2value(self.display_image_array, 0, 255)
        self.display_image_array = self.display_image_array.reshape((self.pil_image.size[1], self.pil_image.size[0]))
        self.display_image = Image.fromarray(self.display_image_array.astype(np.uint8))
        self.display_image = self.display_image.point(self.LUT[:,1])

        self.photo_image = ImageTk.PhotoImage(image=self.display_image)
        self.label_widget.configure(image=self.photo_image)
        self.label_widget.image = self.photo_image

    def destroy(self):
        self.top.destroy()

    def cb(self, hMonitor, hdcMonitor, lprcMonitor, dwData):

        r = lprcMonitor.contents
        #print "cb: %s %s %s %s %s %s %s %s" % (hMonitor, type(hMonitor), hdcMonitor, type(hdcMonitor), lprcMonitor, type(lprcMonitor), dwData, type(dwData))
        data = [hMonitor]
        data.append(r.dump())
        self.retval.append(data)
        return 1

class HamamatsuDialogBox:
    def __init__(self, master, app_directory):
        self.main = tk.Toplevel(master)
        self.main.resizable('FALSE','FALSE')
        self.main.transient(master)
        self.main.grab_set()
        self.main.geometry('+{}+{}'.format(200,200))
        #self.master.wait_window(self.main)
        self.main.title("Second Monitor Setup")

        # Load previous configuration and get monitor info from Windows API
        self.config_file = ConfigParser.ConfigParser()
        self.config_file.read(os.path.join(app_directory,'Hamamatsu_Defaults.ini'))
        self.monitor_info = self.get_monitor_info()

        # Check box to allow showing images on second monitor
        self.display_second = tk.IntVar()
        self.check_box = tk.Checkbutton(master=self.main, text='Display modified mask on second monitor',
                                        variable=self.display_second)
        self.check_box.value = self.display_second
        self.check_box.grid(row=0, column=0, columnspan=2)

        # Build the Combo box for selecting the monitor
        self.monitor_label = tk.Label(master=self.main, text='Monitor:')
        self.monitor_label.grid(row=1, column=0, columnspan=1)
        self.monitor_info_select = tk.StringVar()
        self.monitor_selection = ttk.Combobox(master=self.main, values=range(len(self.monitor_info)),
                                              textvariable=self.monitor_info_select,
                                              state='readonly', width=10)
        self.monitor_selection.set('1')
        self.selected_monitor_specs = self.get_resolution_of_selected_monitor(self.monitor_info_select.get())

        # Build the Label Frame that displays monitor info
        self.monitor_info_frame = tk.LabelFrame(master=self.main, text='Monitor Info')
        self.monitor_resolution_label = tk.Label(master=self.monitor_info_frame, text='Resolution:')
        self.monitor_resolution = tk.Label(master=self.monitor_info_frame,
                                           text=str(self.selected_monitor_specs[0])+
                                           ' x '+str(self.selected_monitor_specs[1]))
        self.monitor_selection.bind('<<ComboboxSelected>>', self.update_monitor_info)
        self.monitor_resolution_label.grid(row=0, column=0)
        self.monitor_resolution.grid(row=0, column=1)
        self.monitor_info_frame.grid(row=2, column=0, columnspan=2)
        self.monitor_selection.grid(row=1, column=1, columnspan=1)

        self.wavelength_label = tk.Label(master=self.main, text='Wavelength:')
        self.wavelengths = self.get_wavelengths(self.config_file)
        self.wavelength_selector = ttk.Combobox(master=self.main, state='readonly',
                                                values=[i for i in self.wavelengths])
        # Build the Wavelength selector which changes which LUT used
        self.wavelength_selector.bind('<<ComboboxSelected>>', self.update_wavelength_LUT)
        self.wavelength_selector.set(self.config_file.get('General','default_wavelength'))
        self.wavelength_label.grid(row=3, column=0)
        self.wavelength_selector.grid(row=3, column=1)

        # Display the LUT file to be used (changed by changing wavelength)
        self.LUT_label = tk.Label(master=self.main, text='LUT File')
        self.LUT_entry = tk.Entry(master=self.main)
        self.LUT_entry.insert(0,self.wavelengths[self.config_file.get('General', 'default_wavelength')])
        self.LUT_label.grid(row=4, column=0)
        self.LUT_entry.grid(row=4, column=1)

        # Build the Entry widget for selecting the image for wavefront correction
        self.wavefront_correction_label = tk.Label(master=self.main, text='Wavefront Correction:')
        self.wavefront_correction_entry = tk.Entry(master=self.main)
        self.wavefront_correction_entry.insert(0,self.config_file.get('Wavefront','corr_fname'))
        self.wavefront_correction_browse = tk.Button(master=self.main, text='Browse', command=self.select_new_wavefront)
        self.wavefront_correction_label.grid(row=5, column=0)
        self.wavefront_correction_entry.grid(row=5, column=1)
        self.wavefront_correction_browse.grid(row=5, column=2)

        # Build the Okay and Cancel buttons
        self.okay_button = tk.Button(master=self.main, text='Okay', command=self.okay_button)
        self.cancel_button = tk.Button(master=self.main, text='Cancel', command=self.cancel_button)
        self.okay_button.grid(row=6, column=0)
        self.cancel_button.grid(row=6, column=1)

    def okay_button(self):
        # Write new defaults
        self.config_file.set('General', 'default_wavelength', self.wavelength_selector.get())
        self.config_file.set('Wavefront', 'corr_fname', self.wavefront_correction_entry.get())
        self.config_file.write(open('Hamamatsu_Defaults.ini','w'))

        self.okay_press = True
        self.display_on_second_monitor = self.display_second.get()
        self.monitor_to_display_on = self.monitor_selection.get()
        self.LUT_to_use = self.LUT_entry.get()
        self.wavefront_correction_to_use = self.wavefront_correction_entry.get()

        self.main.destroy()

    def cancel_button(self):
        self.okay_press = False
        self.main.destroy()

    def select_new_wavefront(self):
        fname = tkFileDialog.askopenfilename(initialdir="wavefront_correction",
                                             title='Wavefront Correction',
                                             filetypes=[('Bitmap','.bmp')])
        fname = os.path.relpath(fname)
        self.wavefront_correction_entry.delete(0,'end')
        self.wavefront_correction_entry.insert(0,fname)

    def get_wavelengths(self, config_parser):
        number_of_wavelengths = config_parser.get('WaveLength','data')
        wavelengths = collections.OrderedDict()
        for i in range(1,int(number_of_wavelengths)+1):
            split_string = string.split(config_parser.get('WaveLength',str(i)),', ')
            wavelengths[split_string[0]] = split_string[1]
        return wavelengths

    def update_wavelength_LUT(self, event):
        self.LUT_entry.delete(0,'end')
        self.LUT_entry.insert(0,self.wavelengths[event.widget.get()])

    def update_monitor_info(self, event):
        self.selected_monitor_specs = self.get_resolution_of_selected_monitor(self.monitor_selection.get())
        self.monitor_resolution.configure(text=str(self.selected_monitor_specs[0])+
                                           ' x '+str(self.selected_monitor_specs[1]))

    def get_resolution_of_selected_monitor(self,monitor_number):

        monitor_specs = self.monitor_info[int(monitor_number)]
        height = monitor_specs[1][3]-monitor_specs[1][1]
        width = monitor_specs[1][2]-monitor_specs[1][0]
        return (width,height)

    def get_monitor_info(self):
        def cb(hMonitor, hdcMonitor, lprcMonitor, dwData):

            r = lprcMonitor.contents
            data = [hMonitor]
            data.append(r.dump())
            retval.append(data)
            return 1

        user = ctypes.windll.user32

        retval = []
        CBFUNC = ctypes.WINFUNCTYPE(ctypes.c_int, ctypes.c_ulong, ctypes.c_ulong, ctypes.POINTER(RECT), ctypes.c_double)
        cbfunc = CBFUNC(cb)
        monitor_info = user.EnumDisplayMonitors(0, 0, cbfunc, 0)
        return retval




class RECT(ctypes.Structure):
  _fields_ = [
    ('left', ctypes.c_ulong),
    ('top', ctypes.c_ulong),
    ('right', ctypes.c_ulong),
    ('bottom', ctypes.c_ulong)
    ]
  def dump(self):
    return map(int, (self.left, self.top, self.right, self.bottom))






class phase_array:
    def __init__(self, pil_size):
        """
        Takes the size of a PIL image and makes three arrays, one is the phase values, one is the rho matrix (distance
        from the center), and one is the phi matrix (polar coordinate angle).

        :prams pil_size: A tuple that contains (height,width) and is called from Image.size()
        :returns phase: Attribute that returns an array of the phase
        :returns rho: Attribute that returns an array of the radius from center
        :returns phi: Attribute that returns an array of the angle around the center
        """
        self.phase = np.zeros((pil_size[1], pil_size[0]))
        self.index_arrays = np.indices((pil_size[1], pil_size[0]))
        self.rho = np.sqrt(
            (self.index_arrays[0] - pil_size[1]/2)**2 + (self.index_arrays[1] - pil_size[0]/2)**2)
        self.rho /= float(np.max(self.rho))
        self.phi = np.arctan2((self.index_arrays[0] - pil_size[1] / 2),
                              (pil_size[0] / 2) - self.index_arrays[1]) + np.pi

        self.zernike_modes = zernike_modes(self.rho, self.phi)

    def phase_normalize(self):
        """
        Wraps the phase around 2pi such that multiples of 2pi greater than 2pi will equal 2pi and multiples of
         2p less than 0 will equal 0. This is called automatically on the phase attribute
        """
        self.phase[self.phase % (2*np.pi) != 0] %= (2*np.pi)
        self.phase[np.logical_and(self.phase % (2*np.pi) == 0, self.phase / (2*np.pi) > 0)] = 2*np.pi
        self.phase[np.logical_and(self.phase % (2*np.pi) == 0, self.phase / (2*np.pi) < 0)] = 0



class zernike_modes:
    """
    This class contains all the zernike modes and the base data for each mode to be added to the phase_array.

    Each zernike mode is generated based on the size of the input image rho and phi matrix.
    """
    def __init__(self, rho, phi):
        self.Z1 = (0*rho) + 2*np.pi
        self.Z2 = 2*rho*np.cos(phi)
        self.Z3 = 2*rho*np.sin(phi)
        self.Z4 = np.sqrt(3) * (2 * rho**2 - 1)
        self.Z5 = np.sqrt(6) * (rho**2) * np.sin(2*phi)
        self.Z6 = np.sqrt(6) * (rho**2) * np.cos(2*phi)
        self.Z7 = np.sqrt(8) * (3 * (rho**3) - 2*rho) * np.sin(phi)
        self.Z8 = np.sqrt(8) * (3 * (rho**3) - 2*rho) * np.cos(phi)
        self.Z11 = np.sqrt(5) * (6 * (rho**4) - 6 * (rho**2) + 1)

        self.Z2 += abs(np.min(self.Z2))
        self.Z3 += abs(np.min(self.Z3))
        self.Z4 += abs(np.min(self.Z4))
        self.Z5 += abs(np.min(self.Z5))
        self.Z6 += abs(np.min(self.Z6))
        self.Z7 += abs(np.min(self.Z7))
        self.Z8 += abs(np.min(self.Z8))
        self.Z11 += abs(np.min(self.Z11))


        self.all = collections.OrderedDict({'Z1': self.Z1,
                                            'Z2': self.Z2,
                                            'Z3': self.Z3,
                                            'Z4': self.Z4,
                                            'Z5': self.Z5,
                                            'Z6': self.Z6,
                                            'Z7': self.Z7,
                                            'Z8': self.Z8,
                                            'Z11': self.Z11})

@autojit
def wrap2value(array, lower_value, upper_value):
    """
    Wraps the phase around 2pi such that multiples of 2pi greater than 2pi will equal 2pi and multiples of
     2p less than 0 will equal 0. This is called automatically on the phase attribute
    """
    array[array % (upper_value) != lower_value] %= (upper_value)
    array[np.logical_and(array % (upper_value) == lower_value, array / (upper_value) > lower_value)] = upper_value
    array[np.logical_and(array % (upper_value) == lower_value, array / (upper_value) < lower_value)] = lower_value
    return array


root = tk.Tk()
main_window(root)
root.mainloop()
root.focus()
