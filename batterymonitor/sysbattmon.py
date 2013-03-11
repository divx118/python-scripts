#!/usr/bin/env python


from gi.repository import AppIndicator3 as appindicator
from gi.repository import Gtk
from gi.repository import Notify
import commands
import gobject
import sys
import argparse

# Commandline arguments
parser = argparse.ArgumentParser()
parser.add_argument('-s','--sec-update', help='update every x seconds',default="10")
parser.add_argument('-c','--capacity-path', help='sysfs path for capacity',default="/sys/class/power_supply/battery/capacity")
parser.add_argument('-o','--online-path', help='sysfs path for online',default="/sys/class/power_supply/ac/online")
args = parser.parse_args()
# Setting global variables
PING_FREQUENCY = int(args.sec_update) # seconds
CAP_PATH = args.capacity_path
ONLINE_PATH = args.online_path
CAPSTR_ARRAY = ["0-5","6-9","10-19","20-29","30-41","42-53","54-65","66-77","78-89","90-100"]
STATUS, ONLINE = commands.getstatusoutput("cat " + ONLINE_PATH)
PREV_ONLINE = bool(int(ONLINE))
#Create notification, so we can later update and show it when needed.
Notify.init ("Batter Monitor")
Notice = Notify.Notification.new ("Battery Monitor","empty","/usr/local/share/battmon/icons/battery_error.png")
	
class CheckBattery:
    def __init__(self):
        self.ind = appindicator.Indicator.new_with_path("battery-monitor",
                                           "battery_discharging_90-100",
                                           appindicator.IndicatorCategory.APPLICATION_STATUS,
                                           "/usr/local/share/battmon/icons/")
        self.ind.set_status(appindicator.IndicatorStatus.ACTIVE)
        self.ind.set_attention_icon("new-messages-red")
        self.menu_setup()
        self.ind.set_menu(self.menu)
        
    def menu_setup(self):
        self.menu = Gtk.Menu()
        self.quit_item = Gtk.MenuItem("Capacity = ")
        self.quit_item.connect("activate", self.quit)
        self.quit_item.show()
        self.menu.append(self.quit_item)

    def main(self):
        self.check_bat()
        gobject.timeout_add(PING_FREQUENCY * 1000, self.check_bat)
        
        Gtk.main()

    def quit(self, widget):
        sys.exit(0)

    def check_bat(self):
	global PREV_ONLINE
	online, capacity = self.battery_checker(ONLINE_PATH,CAP_PATH)
        self.quit_item.set_label("Capacity = " + str(capacity))
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
      
if __name__ == "__main__":
    indicator = CheckBattery()
    indicator.main()
