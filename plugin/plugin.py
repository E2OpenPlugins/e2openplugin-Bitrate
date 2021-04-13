from . import _
from Plugins.Plugin import PluginDescriptor
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Components.ActionMap import ActionMap
from Components.Sources.StaticText import StaticText
from Components.Label import Label
from enigma import getDesktop, ePoint, iPlayableService, eTimer
from Components.config import config, ConfigSubsection, ConfigSelection, ConfigInteger, ConfigYesNo, getConfigListEntry
from Components.ConfigList import ConfigListScreen
from Components.ServiceEventTracker import ServiceEventTracker
from Tools.Directories import pathExists, fileExists
from bitrate import Bitrate

config.plugins.bitrate = ConfigSubsection()
config.plugins.bitrate.background = ConfigSelection([("#00000000", _("black")), ("#54111112", _("transparent") + " - " + _("black"))], default="#00000000")
config.plugins.bitrate.x = ConfigInteger(default=300, limits=(0, 9999))
config.plugins.bitrate.y = ConfigInteger(default=300, limits=(0, 9999))
config.plugins.bitrate.force_restart = ConfigYesNo(default=True)
config.plugins.bitrate.show_in_menu = ConfigSelection([("infobar", _("as infobar")), ("extmenu", _("extension menu"))], default="extmenu")
config.plugins.bitrate.infobar_type_services = ConfigSelection([("all", _("all")), ("dvb", _("only DVB"))], default="all")
config.plugins.bitrate.style_skin = ConfigSelection([("compact", _("compact")), ("full", _("full info"))], default="full")
config.plugins.bitrate.z = ConfigSelection([(str(x), str(x)) for x in range(-20, 21)], "1")

infobarModeBitrateInstance = None
bitrateviewer = None

FULLHD = False
if getDesktop(0).size().width() >= 1920:
	FULLHD = True


class BitrateViewerExtra(Screen):
	skin_compact_fullhd = """
		<screen position="200,40" size="300,90" zPosition="%s" flags="wfNoBorder" backgroundColor="%s" title="Bitrate viewer">
			<widget render="Label" source="video_caption" position="10,10" zPosition="1" size="100,32" font="Regular;30" transparent="1"/>
			<widget render="Label" source="audio_caption" position="10,50" zPosition="1" size="100,32" font="Regular;30" transparent="1"/>
			<widget render="Label" source="video" position="105,10" zPosition="1" size="185,32" font="Regular;30" halign="right" transparent="1"/>
			<widget render="Label" source="audio" position="105,50" zPosition="1" size="185,32" font="Regular;30" halign="right" transparent="1"/>
		</screen>""" % (config.plugins.bitrate.z.value, config.plugins.bitrate.background.value)
	skin_info_fullhd = """
			<screen position="200,300" size="350,160" zPosition="%s" title="Bitrate viewer">
				<eLabel position="5,10" size="80,22" text="video" font="Regular;20" />
				<eLabel position="5,30" size="80,22" text="min" font="Regular;20" />
				<widget name="vmin" position="5,50" size="80,22" font="Regular;20" />
				<eLabel position="85,30" size="80,22" text="max" font="Regular;20" />
				<widget name="vmax" position="85,50" size="80,22" font="Regular;20" />
				<eLabel position="165,30" size="80,22" text="average" font="Regular;20" />
				<widget name="vavg" position="165,50" size="80,22" font="Regular;20" />
				<eLabel position="245,30" size="80,22" text="current" font="Regular;20" />
				<widget name="vcur" position="245,50" size="80,22" font="Regular;20" />
				<eLabel position="5,80" size="80,22" text="audio" font="Regular;20" />
				<eLabel position="5,100" size="80,22" text="min" font="Regular;20" />
				<widget name="amin" position="5,120" size="80,22" font="Regular;20" />
				<eLabel position="85,100" size="80,22" text="max" font="Regular;20" />
				<widget name="amax" position="85,120" size="80,22" font="Regular;20" />
				<eLabel position="165,100" size="80,22" text="average" font="Regular;20" />
				<widget name="aavg" position="165,120" size="80,22" font="Regular;20" />
				<eLabel position="245,100" size="80,22" text="current" font="Regular;20" />
				<widget name="acur" position="245,120" size="80,22" font="Regular;20" />
			</screen>""" % (config.plugins.bitrate.z.value)
	skin_compact = """
			<screen position="200,40" size="200,60" zPosition="%s" backgroundColor="%s" flags="wfNoBorder" title="Bitrate viewer">
				<widget render="Label" source="video_caption" position="10,10" zPosition="1" size="70,22" font="Regular;20" transparent="1"/>
				<widget render="Label" source="audio_caption" position="10,35" zPosition="1" size="70,22" font="Regular;20" transparent="1"/>
				<widget render="Label" source="video" position="85,10" zPosition="1" size="110,22" font="Regular;20" halign="right" transparent="1"/>
				<widget render="Label" source="audio" position="85,35" zPosition="1" size="110,22" font="Regular;20" halign="right" transparent="1"/>
			</screen>""" % (config.plugins.bitrate.z.value, config.plugins.bitrate.background.value)
	skin_info = """
			<screen position="200,300" size="350,160" zPosition="%s" title="Bitrate viewer">
				<eLabel position="5,10" size="80,20" text="video" font="Regular;16" />
				<eLabel position="5,30" size="80,20" text="min" font="Regular;16" />
				<widget name="vmin" position="5,50" size="80,20" font="Regular;16" />
				<eLabel position="85,30" size="80,20" text="max" font="Regular;16" />
				<widget name="vmax" position="85,50" size="80,20" font="Regular;16" />
				<eLabel position="165,30" size="80,20" text="average" font="Regular;16" />
				<widget name="vavg" position="165,50" size="80,20" font="Regular;16" />
				<eLabel position="245,30" size="80,20" text="current" font="Regular;16" />
				<widget name="vcur" position="245,50" size="80,20" font="Regular;16" />
				<eLabel position="5,80" size="80,20" text="audio" font="Regular;16" />
				<eLabel position="5,100" size="80,20" text="min" font="Regular;16" />
				<widget name="amin" position="5,120" size="80,20" font="Regular;16" />
				<eLabel position="85,100" size="80,20" text="max" font="Regular;16" />
				<widget name="amax" position="85,120" size="80,20" font="Regular;16" />
				<eLabel position="165,100" size="80,20" text="average" font="Regular;16" />
				<widget name="aavg" position="165,120" size="80,20" font="Regular;16" />
				<eLabel position="245,100" size="80,20" text="current" font="Regular;16" />
				<widget name="acur" position="245,120" size="80,20" font="Regular;16" />
			</screen>""" % (config.plugins.bitrate.z.value)

	def __init__(self, session, infobar_mode=False):
		if FULLHD:
			if config.plugins.bitrate.style_skin.value == "compact":
				self.skin = self.skin_compact_fullhd
			else:
				self.skin = self.skin_info_fullhd
		else:
			if config.plugins.bitrate.style_skin.value == "compact":
				self.skin = self.skin_compact
			else:
				self.skin = self.skin_info
		Screen.__init__(self, session)
		self.infobar_mode = infobar_mode
		self.style_skin = config.plugins.bitrate.style_skin.value
		self.startDelayTimer = eTimer()
		self.startDelayTimer.callback.append(self.bitrateAfrterDelayStart)
		if config.plugins.bitrate.style_skin.value == "compact":
			self["video_caption"] = StaticText(_("Video:"))
			self["audio_caption"] = StaticText(_("Audio:"))
			self["video"] = StaticText()
			self["audio"] = StaticText()
		else:
			self.setTitle(_("Bitrate viewer"))
			self["vmin"] = Label("")
			self["vmax"] = Label("")
			self["vavg"] = Label("")
			self["vcur"] = Label("")
			self["amin"] = Label("")
			self["amax"] = Label("")
			self["aavg"] = Label("")
			self["acur"] = Label("")
		if not infobar_mode:
			self["actions"] = ActionMap(["WizardActions"],
			{
				"back": self.keyCancel,
				"ok": self.keyCancel,
				"right": self.keyCancel,
				"left": self.keyCancel,
				"down": self.keyCancel,
				"up": self.keyCancel,
			}, -1)
		self.bitrate = Bitrate(session, self.refreshEvent, self.bitrateStopped)
		self.onLayoutFinish.append(self.__layoutFinished)

	def __layoutFinished(self):
		if self.instance:
			self.instance.move(ePoint(config.plugins.bitrate.x.value, config.plugins.bitrate.y.value))
		if not self.infobar_mode:
			self.bitrateUpdateStart()

	def bitrateUpdateStart(self, delay=0):
		self.startDelayTimer.stop()
		self.startDelayTimer.start(delay, True)

	def bitrateAfrterDelayStart(self):
		if not self.bitrateUpdateStatus():
			self.bitrate.start()

	def bitrateUpdateStatus(self):
		return self.bitrate.running

	def bitrateUpdateStop(self):
		self.startDelayTimer.stop()
		if self.bitrateUpdateStatus():
			self.bitrate.stop()
		if self.infobar_mode:
			self.refreshEvent()

	def refreshEvent(self):
		if self.style_skin == "compact":
			self["video"].setText(str(self.bitrate.vcur) + _(" kbit/s"))
			self["audio"].setText(str(self.bitrate.acur) + _(" kbit/s"))
		else:
			self["vmin"].setText(str(self.bitrate.vmin))
			self["vmax"].setText(str(self.bitrate.vmax))
			self["vavg"].setText(str(self.bitrate.vavg))
			self["vcur"].setText(str(self.bitrate.vcur))
			self["amin"].setText(str(self.bitrate.amin))
			self["amax"].setText(str(self.bitrate.amax))
			self["aavg"].setText(str(self.bitrate.aavg))
			self["acur"].setText(str(self.bitrate.acur))

	def keyCancel(self):
		self.bitrate.stop()
		self.close()

	def bitrateStopped(self, retval):
		if not self.infobar_mode:
			self.close()
		else:
			self.refreshEvent()
			if self.shown:
				self.hide()


class BitrateViewerSetup(Screen, ConfigListScreen):
	def __init__(self, session):
		self.setup_title = _("Bitrate viewer setup")
		Screen.__init__(self, session)
		self.skinName = "Setup"
		self["key_green"] = Label(_("Save/OK"))
		self["key_red"] = Label(_("Cancel"))
		self["actions"] = ActionMap(["SetupActions", "ColorActions"],
		{
			"ok": self.keyOk,
			"save": self.keyGreen,
			"cancel": self.keyRed,
		}, -1)
		ConfigListScreen.__init__(self, [])
		self.prev_show_in_menu = config.plugins.bitrate.show_in_menu.value
		self.prev_force_restart = config.plugins.bitrate.force_restart.value
		self.prev_background = config.plugins.bitrate.background.value
		self.prev_style_skin = config.plugins.bitrate.style_skin.value
		self.prev_z = config.plugins.bitrate.z.value
		self.prev_x = config.plugins.bitrate.x.value
		self.prev_y = config.plugins.bitrate.y.value
		self.initConfig()
		self.createSetup()
		self.onClose.append(self.__closed)
		self.onLayoutFinish.append(self.__layoutFinished)

	def __closed(self):
		pass

	def getCurrentEntry(self):
		if self["config"].getCurrent():
			return self["config"].getCurrent()[0]
		return ""

	def getCurrentValue(self):
		if self["config"].getCurrent() and len(self["config"].getCurrent()) > 0:
			return str(self["config"].getCurrent()[1].getText())
		return ""

	def createSummary(self):
		from Screens.Setup import SetupSummary
		return SetupSummary

	def __layoutFinished(self):
		self.setTitle(self.setup_title)

	def initConfig(self):
		def getPrevValues(section):
			res = {}
			for (key, val) in section.content.items.items():
				if isinstance(val, ConfigSubsection):
					res[key] = getPrevValues(val)
				else:
					res[key] = val.value
			return res

		self.bitrate = config.plugins.bitrate
		self.prev_values = getPrevValues(self.bitrate)
		self.cfg_show_in_menu = getConfigListEntry(_("Mode"), self.bitrate.show_in_menu)
		self.cfg_style_skin = getConfigListEntry(_("Style skin"), self.bitrate.style_skin)
		self.cfg_infobar_type_services = getConfigListEntry(_("Start for type services"), self.bitrate.infobar_type_services)
		self.cfg_force_restart = getConfigListEntry(_("Show 'restart bitrate' in extensions menu"), self.bitrate.force_restart)
		self.cfg_background = getConfigListEntry(_("Background window"), self.bitrate.background)
		self.cfg_x = getConfigListEntry(_("X screen position"), self.bitrate.x)
		self.cfg_y = getConfigListEntry(_("Y screen position"), self.bitrate.y)
		self.cfg_z = getConfigListEntry(_("Z screen position"), self.bitrate.z)

	def createSetup(self):
		list = [self.cfg_show_in_menu]
		if self.bitrate.show_in_menu.value == "infobar":
			list.append(self.cfg_infobar_type_services)
			list.append(self.cfg_force_restart)
		list.append(self.cfg_style_skin)
		if self.bitrate.style_skin.value == "compact":
			list.append(self.cfg_background)
		list.append(self.cfg_x)
		list.append(self.cfg_y)
		list.append(self.cfg_z)
		self["config"].list = list
		self["config"].l.setList(list)

	def keyOk(self):
		self.keyGreen()

	def keyRed(self):
		def setPrevValues(section, values):
			for (key, val) in section.content.items.items():
				value = values.get(key, None)
				if value is not None:
					if isinstance(val, ConfigSubsection):
						setPrevValues(val, value)
					else:
						val.value = value
		setPrevValues(self.bitrate, self.prev_values)
		self.keyGreen()

	def keyGreen(self):
		global bitrateviewer
		self.bitrate.save()
		if self.bitrate.show_in_menu.value == "infobar":
			if self.prev_style_skin != config.plugins.bitrate.style_skin.value or self.prev_x != config.plugins.bitrate.x.value or self.prev_y != config.plugins.bitrate.y.value:
				if bitrateviewer:
					bitrateviewer.bitrateUpdateStop()
					self.session.deleteDialog(bitrateviewer)
					bitrateviewer = None
			if not bitrateviewer and infobarModeBitrateInstance:
				infobarModeBitrateInstance.resetService()
		elif bitrateviewer:
			bitrateviewer.bitrateUpdateStop()
			self.session.deleteDialog(bitrateviewer)
			bitrateviewer = None
		if self.prev_show_in_menu != self.bitrate.show_in_menu.value or self.prev_force_restart != self.bitrate.force_restart.value:
			self.refreshPlugins()
		if fileExists("/usr/lib/enigma2/python/Components/Converter/bitratecalc.so") and self.bitrate.show_in_menu.value == "infobar":
			try:
				from Components.Converter.bitratecalc import eBitrateCalculator
				self.session.open(MessageBox, _("Using bitrate in the skins with this plugin is not compatible!"), MessageBox.TYPE_WARNING, timeout=5)
			except:
				pass
		if self.prev_background != self.bitrate.background.value or self.prev_z != self.bitrate.z.value:
			self.session.open(MessageBox, _("GUI needs a restart to apply changes!"), MessageBox.TYPE_INFO, timeout=5)
		self.close()

	def refreshPlugins(self):
		from Components.PluginComponent import plugins
		from Tools.Directories import SCOPE_PLUGINS, resolveFilename
		plugins.clearPluginList()
		plugins.readPluginList(resolveFilename(SCOPE_PLUGINS))

	def keyLeft(self):
		ConfigListScreen.keyLeft(self)
		self.createSetup()

	def keyRight(self):
		ConfigListScreen.keyRight(self)
		self.createSetup()


class infobarModeBitrate:
	def __init__(self, session):
		self.session = session
		self.dvb_service = ""
		self.onClose = []
		self.__event_tracker = ServiceEventTracker(screen=self, eventmap={
				iPlayableService.evStart: self.__evStart,
				iPlayableService.evUpdatedInfo: self.__evUpdatedInfo,
				iPlayableService.evEnd: self.__evEnd
			})
		self.InfoBarInstance = None
		self.firstDelayTimer = eTimer()
		self.firstDelayTimer.callback.append(self.infoBarAppendShowHide)
		self.firstDelayTimer.start(5000, True)

	def infoBarAppendShowHide(self):
		from Screens.InfoBar import InfoBar
		self.InfoBarInstance = InfoBar.instance
		if self.InfoBarInstance:
			if hasattr(self.InfoBarInstance, 'onShowHideNotifiers') and self.show_hide_func not in self.InfoBarInstance.onShowHideNotifiers:
				self.InfoBarInstance.onShowHideNotifiers.append(self.show_hide_func)
				self.resetService()

	def show_hide_func(self, func):
		if func:
			self.__onInfoBarBitrateShow()
		else:
			self.__onInfoBarBitrateHide()

	def initDialog(self):
		global bitrateviewer
		if not bitrateviewer and config.plugins.bitrate.show_in_menu.value == "infobar":
			bitrateviewer = self.session.instantiateDialog(BitrateViewerExtra, True)
			self.runBitrateForService()

	def __evStart(self):
		if bitrateviewer:
			if config.plugins.bitrate.infobar_type_services.value == "dvb":
				playref = self.session.nav.getCurrentlyPlayingServiceReference()
				if not playref:
					self.dvb_service = ""
				else:
					str_service = playref.toString()
					if str_service.startswith("1:") and '%3a//' not in str_service:
						self.dvb_service = "dvb"
					else:
						self.dvb_service = "video"
			self.runBitrateForService()

	def runBitrateForService(self):
		if bitrateviewer and config.plugins.bitrate.show_in_menu.value == "infobar" and (config.plugins.bitrate.infobar_type_services.value == "all" or self.dvb_service == "dvb"):
			bitrateviewer.bitrateUpdateStart(500)
			if self.InfoBarInstance and self.InfoBarInstance.shown and not bitrateviewer.shown:
				bitrateviewer.show()

	def __evUpdatedInfo(self):
		self.runBitrateForService()

	def __evEnd(self):
		self.dvb_service = ""
		if bitrateviewer:
			bitrateviewer.bitrateUpdateStop()
			if bitrateviewer.shown:
				bitrateviewer.hide()

	def __onInfoBarBitrateShow(self):
		if bitrateviewer and config.plugins.bitrate.show_in_menu.value == "infobar" and (config.plugins.bitrate.infobar_type_services.value == "all" or self.dvb_service == "dvb"):
			if bitrateviewer.bitrateUpdateStatus() and not bitrateviewer.shown:
				bitrateviewer.show()

	def __onInfoBarBitrateHide(self):
		if bitrateviewer and bitrateviewer.shown:
			bitrateviewer.hide()

	def resetService(self):
		self.initDialog()
		self.__evEnd()
		self.__evStart()


def main(session, **kwargs):
	global bitrateviewer
	if bitrateviewer:
		bitrateviewer.bitrateUpdateStop()
		session.deleteDialog(bitrateviewer)
		bitrateviewer = None
	session.open(BitrateViewerExtra)


def settings(session, **kwargs):
	session.open(BitrateViewerSetup)


def restart(session, **kwargs):
	if session.nav.getCurrentlyPlayingServiceReference() and bitrateviewer and infobarModeBitrateInstance:
		infobarModeBitrateInstance.resetService()


def sessionstart(reason, session, **kwargs):
	global infobarModeBitrateInstance
	if reason == 0 and session and infobarModeBitrateInstance is None:
		infobarModeBitrateInstance = infobarModeBitrate(session)


def Plugins(**kwargs):
	desc = _("Show bitrate for live service")
	list = [PluginDescriptor(name=_("Bitrate setup"), description=desc, where=PluginDescriptor.WHERE_PLUGINMENU, icon="bitrateviewer.png", fnc=settings)]
	list.append(PluginDescriptor(where=PluginDescriptor.WHERE_SESSIONSTART, fnc=sessionstart))
	if config.plugins.bitrate.show_in_menu.value == "extmenu":
		list.append(PluginDescriptor(name=_("Bitrate viewer"), description=desc, where=PluginDescriptor.WHERE_EXTENSIONSMENU, fnc=main))
	elif config.plugins.bitrate.force_restart.value:
		list.append(PluginDescriptor(name=_("Restart bitrate viewer"), description=desc, where=PluginDescriptor.WHERE_EXTENSIONSMENU, fnc=restart))
	return list
