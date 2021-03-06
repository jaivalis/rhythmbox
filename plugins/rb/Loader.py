# -*- Mode: python; coding: utf-8; tab-width: 8; indent-tabs-mode: t; -*- 
#
# Copyright (C) 2009 - Jonathan Matthew
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2, or (at your option)
# any later version.
#
# The Rhythmbox authors hereby grant permission for non-GPL compatible
# GStreamer plugins to be used and distributed together with GStreamer
# and Rhythmbox. This permission is above and beyond the permissions granted
# by the GPL license by which Rhythmbox is covered. If you modify this code
# you may extend this exception to your version of the code, but you are not
# obligated to do so. If you do not wish to do so, delete this exception
# statement from your version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301  USA.

from gi.repository import GObject, GLib, Gdk, Gio
import sys

def callback_with_gdk_lock(callback, data, args):
	Gdk.threads_enter()
	try:
		v = callback(data, *args)
		Gdk.threads_leave()
		return v
	except Exception as e:
		sys.excepthook(*sys.exc_info())
		Gdk.threads_leave()


class Loader(object):
	def __init__ (self):
		self._cancel = Gio.Cancellable()

	def _contents_cb (self, file, result, data):
		try:
			(ok, contents, etag) = file.load_contents_finish(result)
			if ok:
				callback_with_gdk_lock(self.callback, contents, self.args)
			else:
				callback_with_gdk_lock(self.callback, None, self.args)
		except Exception as e:
			sys.excepthook(*sys.exc_info())
			callback_with_gdk_lock(self.callback, None, self.args)

	def get_url (self, url, callback, *args):
		self.url = url
		self.callback = callback
		self.args = args
		try:
			file = Gio.file_new_for_uri(url)
			file.load_contents_async(self._cancel, self._contents_cb, None)
		except Exception as e:
			sys.excepthook(*sys.exc_info())
			callback(None, *args)

	def cancel (self):
		self._cancel.cancel()



class UpdateCheck(object):
	def __init__ (self):
		self._cancel = Gio.Cancellable()

	def _file_info_cb (self, file, result, data):
		try:
			rfi = file.query_info_finish(result)
			remote_mod = rfi.get_attribute_uint64(Gio.FILE_ATTRIBUTE_TIME_MODIFIED)
			callback_with_gdk_lock(self.callback, remote_mod != self.local_mod, self.args)
		except Exception as e:
			sys.excepthook(*sys.exc_info())
			callback_with_gdk_lock(self.callback, False, self.args)

	def check_for_update (self, local, remote, callback, *args):
		self.local = local
		self.remote = remote
		self.callback = callback
		self.args = args

		try:
			lf = Gio.file_new_for_commandline_arg(local)
			lfi = lf.query_info(Gio.FILE_ATTRIBUTE_TIME_MODIFIED, Gio.FileQueryInfoFlags.NONE, None)
			self.local_mod = lfi.get_attribute_uint64(Gio.FILE_ATTRIBUTE_TIME_MODIFIED)

			rf = Gio.file_new_for_uri(remote)
			rf.query_info_async(Gio.FILE_ATTRIBUTE_TIME_MODIFIED, Gio.FileQueryInfoFlags.NONE, GLib.PRIORITY_DEFAULT, self._cancel, self._file_info_cb, None)
		except Exception as e:
			sys.excepthook(*sys.exc_info())
			self.callback(True, *self.args)

	def cancel (self):
		self._cancel.cancel()

