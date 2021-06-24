#
# to use this for the localisation of other plugins,
# just change the DOMAIN to the name of the Plugin.
# It is assumed, that the domain ist the same as
# the directory name of the plugin.
#

DOMAIN=Bitrate
installdir = $(LIBDIR)/enigma2/python/Plugins/Extensions/$(DOMAIN)
#GETTEXT=./pygettext.py
GETTEXT=xgettext

#MSGFMT = ./msgfmt.py
MSGFMT = msgfmt

LANGS := bg fi fr el lt ru
LANGPO := $(foreach LANG, $(LANGS),$(LANG).po)
LANGMO := $(foreach LANG, $(LANGS),$(LANG).mo)

%.mo: %.po
	$(MSGFMT) -o $@ $<

%.po:
	msginit -l $@ -o $@ -i $(DOMAIN).pot --no-translator

CLEANFILES = $(foreach LANG, $(LANGS),$(LANG).mo)

clean-local:
	$(RM) -r $(LANGS)

install-data-am: $(LANGPO) $(LANGMO)
	for lang in $(LANGS); do \
		mkdir -p $(DESTDIR)$(installdir)/locale/$$lang/LC_MESSAGES; \
		cp $$lang.mo $(DESTDIR)$(installdir)/locale/$$lang/LC_MESSAGES/$(DOMAIN).mo; \
	done
