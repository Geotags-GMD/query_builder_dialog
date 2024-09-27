from .query_builder_dialog_base import QueryBuilderDialog
from qgis.core import QgsProject
from qgis.gui import QgsGui
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import QAction, QToolBar
from PyQt5.QtGui import QIcon
import os

class QueryBuilderPlugin:
    def __init__(self, iface):
        """Initialize the plugin."""
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)
        self.icon_path = os.path.join(self.plugin_dir, 'icon.png')
        self.menu = 'GMD Plugins'
        self.toolbar = None

    def initGui(self):
        """Called when the plugin is started."""
        # Create a toolbar if it doesn't exist
        if not self.toolbar:
            self.toolbar = self.iface.addToolBar('Query Manager')
        
        # Add the action to the toolbar
        self.action = QAction(QIcon(self.icon_path), 'Query Manager', self.iface.mainWindow())
        self.action.triggered.connect(self.run)
        self.iface.addPluginToMenu(self.menu, self.action)
        self.toolbar.addAction(self.action)

    def unload(self):
        """Called when the plugin is unloaded."""
        # Remove the action from the toolbar
        if self.toolbar:
            self.toolbar.removeAction(self.action)
        
        # Remove the action from the plugin menu
        self.iface.removePluginMenu(self.menu, self.action)

        # Delete toolbar if it's not used by other plugins
        if self.toolbar and not self.toolbar.actions():
            self.iface.mainWindow().removeToolBar(self.toolbar)
            self.toolbar = None

    def run(self):
        """Method that runs the main functionality of the plugin."""
        dialog = QueryBuilderDialog()
        dialog.exec_()
