#!/usr/bin/env python


from gi.repository import AppIndicator3 as appindicator
from gi.repository import Gtk
from gi.repository import Notify
import commands
import gobject
import sys
import argparse
import subprocess
from subprocess import call

# Commandline arguments
parser = argparse.ArgumentParser()
parser.add_argument('-s','--sec-update', help='update every x seconds',default="10")
parser.add_argument('-c','--capacity-path', help='sysfs path for capacity',default="/sys/class/power_supply/battery/capacity")
parser.add_argument('-o','--online-path', help='sysfs path for online',default="/sys/class/power_supply/ac/online")
parser.add_argument('-l','--ledlight-path', help='sysfs path for backlight',default="/sys/devices/platform/omap-pwm-backlight/backlight/omap-pwm-backlight/brightness")
parser.add_argument('-b','--bluetooth-path', help='sysfs path for bluetooth',default="/sys/class/rfkill/rfkill1/state")
parser.add_argument('-r','--range-control', help='min max values backlight',default="10-254")
args = parser.parse_args()
# Setting global variables
PING_FREQUENCY = int(args.sec_update) # seconds
CAP_PATH = args.capacity_path
ONLINE_PATH = args.online_path
CAPSTR_ARRAY = ["0-5","6-9","10-19","20-29","30-41","42-53","54-65","66-77","78-89","90-100"]
STATUS, ONLINE = commands.getstatusoutput("cat " + ONLINE_PATH)
PREV_ONLINE = bool(int(ONLINE))
ICON_PATH = "/usr/local/share/battmon/icons/" #TODO: change this to archos-power-manager path
BACKLIGHT_PATH = args.ledlight_path
BLUETOOTH_PATH = args.bluetooth_path
MIN = int(args.range_control.split("-")[0])
MAX = int(args.range_control.split("-")[1])

#Create notification, so we can later update and show it when needed.
Notify.init ("Batter Monitor")
Notice = Notify.Notification.new ("Battery Monitor","empty",ICON_PATH + "battery_error.png")
	
class ArchosPowerManager:
    def __init__(self):
        self.ind = appindicator.Indicator.new_with_path("battery-monitor",
                                           "battery_discharging_90-100",
                                           appindicator.IndicatorCategory.APPLICATION_STATUS,
                                           ICON_PATH)
        self.ind.set_status(appindicator.IndicatorStatus.ACTIVE)
        self.ind.set_attention_icon("new-messages-red")
        self.menu_setup()
        self.ind.set_menu(self.menu)
        
    def menu_setup(self):
	# Create dropdown menu
        self.menu = Gtk.Menu()
        self.cap_item = Gtk.MenuItem("Capacity = ")
        self.cap_item.show()
        self.menu.append(self.cap_item)
        self.blue_item = Gtk.CheckMenuItem("Bluetooth on/off")
        status, act = commands.getstatusoutput("cat " + BLUETOOTH_PATH)
        if bool(int(act)):
	  self.blue_item.set_active(True)
	  self.blue_item.set_label("Bluetooth Off")
	else:
	  self.blue_item.set_active(False)
	  self.blue_item.set_label("Bluetooth On")
        self.blue_item.connect("activate", self.control_bluetooth)
        self.blue_item.show()
        self.menu.append(self.blue_item)

        self.control_item = Gtk.MenuItem("Set brightness")
        self.control_item.connect("activate", self.window_adjust)
        self.control_item.show()
        self.menu.append(self.control_item)
        self.reboot_item = Gtk.MenuItem("Reboot")
        self.reboot_item.connect("activate", self.show_dialog,"Are you sure you want to Reboot","reboot")
        self.reboot_item.show()
        self.menu.append(self.reboot_item)
        self.shutdown_item = Gtk.MenuItem("Shutdown")
        self.shutdown_item.connect("activate", self.show_dialog,"Are you sure you want to Shutdown","shutdown now")
        self.shutdown_item.show()
        self.menu.append(self.shutdown_item)
        self.quit_item = Gtk.MenuItem("Quit")
        self.quit_item.connect("activate", self.show_dialog,"Are you sure you want to Quit\nArchos-power-manager","quit")
        self.quit_item.show()
        self.menu.append(self.quit_item)

    def main(self):
        self.check_bat()
        gobject.timeout_add(PING_FREQUENCY * 1000, self.check_bat)
        
        Gtk.main()

    def quit(self):
        sys.exit(0)
        
        
    def show_dialog(self,widget,message,command):
	powerdialog = Gtk.Dialog()
        powerdialog.set_default_size(300, 100)
        label = Gtk.Label(message)
        powerdialog.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
             Gtk.STOCK_OK, Gtk.ResponseType.OK)
        box = powerdialog.get_content_area()
        box.add(label)
        powerdialog.show_all()
        response = powerdialog.run()
	if response == Gtk.ResponseType.OK:
            print "The OK button was clicked we are going to "+command
            if command == "quit":
	      self.quit()
	    return_code = subprocess.call(command, shell=True)
        elif response == Gtk.ResponseType.CANCEL:
            print "The Cancel button was clicked"

        powerdialog.destroy()
        
    def check_bat(self):
	global PREV_ONLINE
	online, capacity = self.battery_checker(ONLINE_PATH,CAP_PATH)
        self.cap_item.set_label("Capacity = " + str(capacity))
        if online == "1":
	  icon = "battery_charging"
	  if not PREV_ONLINE:
	    try:
	      Notice.close()
	    except:
	      ignore=0
	    self.show_message("AC connected","dialog-information")
	    PREV_ONLINE = True
	else:
	  icon = "battery_discharging"
	  if PREV_ONLINE:
	    try:
	      Notice.close()
	    except:
	      ignore=0
	    self.show_message("AC disconnected","dialog-information")
	    PREV_ONLINE = False
	i = 0
	while i < len(CAPSTR_ARRAY):
	  cap = CAPSTR_ARRAY[i].split("-")
	  mincap = int(cap[0])
	  maxcap = int(cap[1])
	  if mincap <= capacity <= maxcap:
	    capstr = CAPSTR_ARRAY[i]
	    break
	  i += 1
	self.ind.set_icon(icon + "_" + capstr)
        return True

    def battery_checker(self, pathonline, pathcapacity):
        try:
            status, online = commands.getstatusoutput("cat " + pathonline)
            status, capacity = commands.getstatusoutput("cat " + pathcapacity)
            capacity = int(capacity)
            CAPACITY = capacity
            return (online, capacity)
        except:
            return False, 0
            
    def show_message(self, message, icon):
      Notice.update("Battery Monitor", message, icon)
      Notice.show()
      
    def window_adjust(self,widget):
        window = Gtk.Window()
        window.set_default_size(600,100)
        status, brightness = commands.getstatusoutput("cat " + BACKLIGHT_PATH)
        adj = Gtk.Adjustment(int(brightness), MIN, MAX, 5, 5, 0)
        
        self.h_scale = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL, adjustment=adj)
        self.h_scale.set_digits(0)
        self.h_scale.set_hexpand(True)
        self.h_scale.set_valign(Gtk.Align.START)

        self.h_scale.connect("value-changed", self.scale_moved)
        
        window.add(self.h_scale)
        window.show_all()

    def scale_moved(self, event):
        return_code = subprocess.call("echo " + str(int(self.h_scale.get_value())) + " > " + BACKLIGHT_PATH, shell=True)
        
    def control_bluetooth(self,widget):
      if self.blue_item.get_active():
	return_code = subprocess.call("echo 1" + " > " + BLUETOOTH_PATH, shell=True)
	self.blue_item.set_label("Bluetooth Off")
      else:
	return_code = subprocess.call("echo 0" + " > " + BLUETOOTH_PATH, shell=True)
	self.blue_item.set_label("Bluetooth On")
	
if __name__ == "__main__":
    indicator = ArchosPowerManager()
    indicator.main()
